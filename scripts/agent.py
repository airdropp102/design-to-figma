"""CLI controller for Figma Design Agent Only. TalkToFigma-only, fail closed."""
import argparse, json, pathlib, sys
from .workflow import WorkflowStore, ApprovalGate, digest, atomic
from .spec_input import validate_spec
from .policy import load_policy
from .bootstrap import setup
from .readiness import ReadinessDoctor
from .socket_supervisor import SocketSupervisor
from .design_session import DesignSession
from .state_bridge import StateBridge
from .design_qa import DesignQA

ROOT=pathlib.Path(__file__).resolve().parent.parent

class Parser(argparse.ArgumentParser):
    def error(self,message):raise ValueError(message)

def envelope(code,status,reason,next_action='',run_id=None):
    return {'code':code,'status':status,'reason':reason,'next_action':next_action,'run_id':run_id}

def parser():
    p=Parser(prog='./agent',description='Figma-only design workflow controller')
    sub=p.add_subparsers(dest='command',required=True,parser_class=Parser)
    for cmd in ('setup','doctor','up','down','status','design','resume','retry','checkpoint'):
        c=sub.add_parser(cmd)
        c.add_argument('--json',action='store_true')
        if cmd=='setup':c.add_argument('--runtime',required=True,choices=['codex','claude','both'])
        if cmd=='doctor':c.add_argument('--runtime',choices=['codex','claude','both'])
        if cmd=='design':
            c.add_argument('spec');c.add_argument('--runtime',required=True,choices=['codex','claude'])
        if cmd=='resume':c.add_argument('--runtime',choices=['codex','claude'])
        if cmd=='retry':c.add_argument('--phase',required=True)
        if cmd=='checkpoint':
            c.add_argument('--event',required=True);c.add_argument('--evidence',required=True)
    return p

def main(argv=None):
    try:
        args=parser().parse_args(argv)
        store=WorkflowStore(ROOT)
        status=store.status()
        run=status.get('run_id')
        cmd=args.command
        if cmd=='setup':
            result=setup(ROOT,args.runtime)
            code=3 if result['status']!='ready' else 0
            obj=envelope(code,result['status'],'Setup readiness checks completed',result['next_action'],run)
            obj['details']=result
        elif cmd=='doctor':
            obj=envelope(3,'action_required','Doctor is read-only; Figma live session is not verified','Use interactive agent to connect Figma and provide tool evidence',run)
            obj['details']=ReadinessDoctor(ROOT).check(args.runtime)
        elif cmd=='up':
            res=SocketSupervisor(ROOT).up();code=0 if res.get('running') else 3
            obj=envelope(code,'socket_ready' if code==0 else 'action_required','TalkToFigma socket supervisor', 'Check pinned Bun checkout / socket protocol',run)
            obj['details']=res
        elif cmd=='down':
            res=SocketSupervisor(ROOT).down()
            obj=envelope(0,'stopped','Stopped owned socket' if res['stopped'] else 'No owned socket process to stop','',run)
            obj['details']=res
        elif cmd=='status':
            wal=StateBridge(ROOT).require_reconcile()
            obj=envelope(4 if wal else 0,'reconcile_required' if wal else status.get('status','not_started'),status.get('phase','NOT_STARTED'),'Verify live Figma nodes before retry' if wal else '',run)
            obj['details']={'workflow':status,'open_wal':wal}
        elif cmd=='design':
            load_policy(ROOT/'workflow.yaml')
            spec=validate_spec(pathlib.Path(args.spec),ROOT)
            obj0=store.begin(spec.spec_path,args.runtime)
            run=obj0['run_id']
            # An interactive CLI agent may only start after its version-specific invocation is actually verified.
            health=ReadinessDoctor(ROOT).check(args.runtime)
            cli_available=health.get('runtimes',{}).get(args.runtime,{}).get('cli',{}).get('available',False)
            if not cli_available:
                obj=envelope(3,'action_required','Selected interactive runtime CLI not available','Install selected CLI, then run ./agent setup',run)
            else:
                try:
                    rc=DesignSession(ROOT).launch(pathlib.Path(args.spec),args.runtime)
                    if rc != 0:
                        obj=envelope(5,'adapter_failure','Interactive agent exited nonzero','Inspect runtime diagnostics, then resume safely',run)
                    elif not health['agent_ready']:
                        obj=envelope(3,'action_required','Interactive agent started; skills and MCP readiness still need verified evidence','Verify required skills in session and checkpoint environment_ready before brainstorming',run)
                    else:
                        obj=envelope(0,'session_exited','Interactive design session exited; verify workflow status separately','Run ./agent status --json',run)
                except RuntimeError as e:
                    obj=envelope(5,'adapter_unsupported',str(e),'Verify pinned CLI version/interactive prompt mode or launch CLI manually',run)
            obj['phase']=obj0['phase'];obj['spec_sha256']=spec.spec_sha256
        elif cmd=='resume':
            current=store.resume();run=current.get('run_id')
            if current['phase']=='NOT_STARTED':obj=envelope(2,'invalid_input','No workflow to resume','Run ./agent design specs/APP_SPEC.md --runtime codex',run)
            elif args.runtime and args.runtime!=current['runtime']:obj=envelope(6,'workflow_conflict','Cannot switch writer runtime on active run','Resume with original runtime',run)
            else:
                open_wal=StateBridge(ROOT).require_reconcile()
                if open_wal:obj=envelope(4,'reconcile_required','Open create/update WAL entries; never replay blindly','Inspect TalkToFigma live document and reconcile node identity',run)
                else:
                    obj=envelope(3,'action_required','Resume requires verified interactive runtime session','Start '+current['runtime']+' and continue '+current['phase']+' with run_id '+run,run)
                    obj['phase_prompt']=DesignSession(ROOT).phase_prompt(current['phase'] if current['phase'] in ('BRAINSTORMING','AWAITING_APPROVAL','DESIGN_PLANNING','DESIGN_SYSTEM_READY','FIGMA_CONNECTION_GATE','DESIGN_EXECUTION','QUALITY_ASSURANCE','DELIVERY') else 'SPEC_VALIDATION',current)
        elif cmd=='retry':
            if args.phase!='figma-execution':obj=envelope(2,'invalid_input','Only figma-execution retry supported','',run)
            elif StateBridge(ROOT).require_reconcile():obj=envelope(4,'reconcile_required','WAL still open; retry unsafe','Verify and reconcile TalkToFigma nodes first',run)
            else:obj=envelope(3,'action_required','Retry requires fresh live file/page identity and approval','Resume verified interactive session',run)
        elif cmd=='checkpoint':
            path=pathlib.Path(args.evidence).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Evidence path must be an existing workspace file')
            ev=json.loads(path.read_text())
            if not isinstance(ev,dict) or ev.get('verified') is not True:raise ValueError('Unverified checkpoint evidence')
            if args.event=='approved':
                current=store.status()
                if current['phase']!='AWAITING_APPROVAL':raise ValueError('Not awaiting brainstorm approval')
                brief=ROOT/'design/BRAINSTORM.md'
                if not brief.exists():raise ValueError('No brainstorm draft')
                if current['artifacts'].get('brainstorm',{}).get('sha256')!=digest(brief):raise ValueError('Brief modified since reviewed')
                # Controller records the explicit user-interaction reference, not an 'auto-approved' flag.
                ref=ev.get('interaction_ref','')
                ApprovalGate(ROOT).record(current['spec_sha256'],digest(brief),current['run_id'],ref)
                current['approval']=json.loads((ROOT/'design/approval.json').read_text())
                store._save(current,'approval_recorded')
            if args.event in ('figma_ready','screens_verified','qa_passed','delivery_ready'):
                if args.event=='figma_ready' and not all(ev.get(k) for k in ('figma_file_id','page_id','channel_id','tool_result_ref','permission_probe_ref')):raise ValueError('Figma live identity/permission evidence missing')
                bridge = StateBridge(ROOT)
                open_wal = bridge.require_reconcile()
                verified_probe = args.event == 'figma_ready' and bridge.is_verified_permission_probe(open_wal, ev)
                if open_wal and not verified_probe:raise ValueError('Open WAL requires live reconciliation')
                if args.event in ('qa_passed','delivery_ready'):
                    approved=ev.get('approved_plan');proof=ev.get('qa_evidence')
                    if not isinstance(approved,dict) or not isinstance(proof,dict):raise ValueError('QA data missing')
                    result=DesignQA(ROOT).evaluate(approved,StateBridge(ROOT).state(),proof)
                    if not result['passed']:
                        obj=envelope(7,'qa_incomplete',json.dumps(result,ensure_ascii=False),'Fix missing Figma QA before transition',run)
                        print(json.dumps(obj,ensure_ascii=False));return obj['code']
            updated=store.advance(args.event,path)
            obj=envelope(0,'checkpoint_saved',f"Entered {updated['phase']}",'',updated['run_id'])
        else:raise ValueError('Unknown command')
    except (ValueError,KeyError,FileNotFoundError,json.JSONDecodeError) as exc:
        obj=envelope(2,'invalid_input',str(exc),'Check APP_SPEC, policy, phase or command arguments')
    except RuntimeError as exc:
        obj=envelope(5,'blocked',str(exc),'Run doctor and resolve missing dependencies or evidence')
    print(json.dumps(obj,ensure_ascii=False,default=str))
    return obj['code']

if __name__=='__main__':sys.exit(main())
