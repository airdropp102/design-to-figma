"""Durable workflow checkpoint controller; never mutates design/STATE.json."""
import hashlib, json, os, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path

PHASES=('ENVIRONMENT_CHECK','SPEC_VALIDATION','BRAINSTORMING','AWAITING_APPROVAL','DESIGN_PLANNING','DESIGN_SYSTEM_READY','FIGMA_CONNECTION_GATE','DESIGN_EXECUTION','QUALITY_ASSURANCE','DELIVERY','COMPLETED')
EVENTS={'environment_ready':('ENVIRONMENT_CHECK','SPEC_VALIDATION'), 'spec_valid':('SPEC_VALIDATION','BRAINSTORMING'), 'brainstorm_drafted':('BRAINSTORMING','AWAITING_APPROVAL'), 'approved':('AWAITING_APPROVAL','DESIGN_PLANNING'),'plan_ready':('DESIGN_PLANNING','DESIGN_SYSTEM_READY'),'design_system_ready':('DESIGN_SYSTEM_READY','FIGMA_CONNECTION_GATE'),'figma_ready':('FIGMA_CONNECTION_GATE','DESIGN_EXECUTION'),'screens_verified':('DESIGN_EXECUTION','QUALITY_ASSURANCE'),'qa_passed':('QUALITY_ASSURANCE','DELIVERY'),'delivery_ready':('DELIVERY','COMPLETED')}

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def atomic(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.wf-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def clock():return datetime.now(timezone.utc).isoformat()

class WorkflowStore:
    def __init__(self,root):
        self.root=Path(root).resolve();self.path=self.root/'design/WORKFLOW.json';self.journal=self.root/'design/workflow-journal.log'
    def status(self):
        if not self.path.exists():return {'phase':'NOT_STARTED','status':'not_started','run_id':None}
        result=json.loads(self.path.read_text())
        if result.get('version') != 1: raise ValueError('Unknown workflow state version')
        return result
    def _save(self,obj,event):
        atomic(self.path,obj)
        with self.journal.open('a',encoding='utf8') as f:
            f.write(json.dumps({'at':clock(),'event':event,'run_id':obj['run_id'],'phase':obj['phase']})+'\n');f.flush();os.fsync(f.fileno())
    def begin(self,spec_path,runtime):
        if runtime not in ('claude','codex'):raise ValueError('runtime must be claude or codex')
        p=Path(spec_path).resolve()
        if not p.is_file() or not p.is_relative_to(self.root):raise ValueError('Invalid workspace spec')
        existing=self.status();hash_=digest(p)
        if existing['phase']!='NOT_STARTED':
            if existing.get('spec_path')!=str(p) or existing.get('runtime')!=runtime:raise ValueError('Existing workflow conflicts with new spec or runtime')
            if existing.get('spec_sha256')!=hash_:raise ValueError('APP_SPEC changed; previous approval invalid')
            return existing
        result={'version':1,'run_id':'run-'+uuid.uuid4().hex[:12],'runtime':runtime,'spec_path':str(p),'spec_sha256':hash_, 'phase':'ENVIRONMENT_CHECK','phase_attempt':1,'status':'running','approval':None,'artifacts':{},'checkpoints':[], 'last_error':None,'updated_at':clock()}
        self._save(result,'begin');return result
    def advance(self,event,evidence_path=None):
        obj=self.status()
        if event not in EVENTS or EVENTS[event][0]!=obj['phase']: raise ValueError('Invalid workflow phase transition')
        if digest(obj['spec_path'])!=obj['spec_sha256']:raise ValueError('APP_SPEC changed; reconfirm requirements')
        evidence={}
        if evidence_path is not None:
            path=Path(evidence_path).resolve()
            if not path.is_relative_to(self.root) or not path.is_file():raise ValueError('Evidence path invalid')
            evidence=json.loads(path.read_text())
            if not isinstance(evidence,dict) or evidence.get('verified') is not True:raise ValueError('Unverified event evidence')
        else:
            raise ValueError('Verified evidence required')
        if event=='environment_ready':
            if not evidence.get('runtime_version') or not evidence.get('mcp_registration_ref') or any(evidence.get('skills',{}).get(skill) is not True for skill in ('superpowers','ui-ux-pro-max')):
                raise ValueError('Runtime, MCP and both skill smoke-test references must be verified')
        if event=='figma_ready':
            required=('figma_file_id','page_id','channel_id','tool_result_ref','permission_probe_ref')
            if any(not evidence.get(k) for k in required):raise ValueError('Live Figma file/page/plugin/permission evidence required')
        if event=='delivery_ready':
            report=self.root/'design/WORKFLOW_REPORT.json'
            design_report=self.root/'design/DESIGN_REPORT.md'
            if not report.is_file() or not design_report.is_file():raise ValueError('Figma delivery reports missing')
            if json.loads(report.read_text()).get('passed') is not True:raise ValueError('Delivery report QA incomplete')
        if event=='plan_ready':
            for relative in ('design/SCREENS.md','design/NEEDED.md'):
                if not (self.root/relative).is_file():raise ValueError(f'Missing planning artifact: {relative}')
        if event=='design_system_ready':
            for relative in ('design/MASTER.md','design/tokens.json'):
                if not (self.root/relative).is_file():raise ValueError(f'Missing design system artifact: {relative}')
        if event=='screens_verified':
            path=self.root/'design/STATE.json'
            if not path.is_file():raise ValueError('Missing screen state v2')
            items=json.loads(path.read_text()).get('items',{})
            if not any(k.startswith('screen:') and v.get('status')=='done' for k,v in items.items()):
                raise ValueError('No verified Figma screen exists in STATE.json')
        if event=='approved':
            ap=obj.get('approval');brief=obj.get('artifacts',{}).get('brainstorm')
            if not ap or not brief or not ApprovalGate(self.root).is_current(obj['spec_sha256'],brief['sha256'],obj['run_id']):raise ValueError('Approval invalid or stale')
        if event=='brainstorm_drafted':
            brief=self.root/'design/BRAINSTORM.md'
            if not brief.is_file():raise ValueError('BRAINSTORM.md draft missing')
            obj['artifacts']['brainstorm']={'path':'design/BRAINSTORM.md','sha256':digest(brief)}
        obj['phase']=EVENTS[event][1]
        obj['status']='waiting_user' if obj['phase']=='AWAITING_APPROVAL' else ('complete' if obj['phase']=='COMPLETED' else 'running')
        obj['updated_at']=clock();obj['checkpoints'].append({'event':event,'at':obj['updated_at'],'evidence':str(evidence_path) if evidence_path else None})
        self._save(obj,event)
        return obj
    def resume(self):
        obj=self.status()
        if obj['phase']!='NOT_STARTED' and digest(obj['spec_path'])!=obj['spec_sha256']:
            raise ValueError('APP_SPEC hash mismatch; reapproval required')
        return obj

class ApprovalGate:
    def __init__(self,root):self.root=Path(root);self.path=self.root/'design/approval.json'
    def record(self,spec_sha256,brief_sha256,run_id,interaction_ref):
        if not (isinstance(interaction_ref,str) and interaction_ref.startswith('interactive_user:') and len(interaction_ref)>len('interactive_user:')):raise ValueError('Requires interactive user confirmation reference')
        if any(len(h)!=64 or any(c not in '0123456789abcdef' for c in h) for h in (spec_sha256,brief_sha256)):raise ValueError('Invalid digest')
        obj={'approved_by':'interactive_user','interaction_ref':interaction_ref,'spec_sha256':spec_sha256,'brief_sha256':brief_sha256,'run_id':run_id,'approved_at':clock()}
        atomic(self.path,obj)
        return obj
    def is_current(self,spec_sha256,brief_sha256,run_id):
        if not self.path.exists():return False
        obj=json.loads(self.path.read_text())
        return all(obj.get(k)==v for k,v in {'spec_sha256':spec_sha256,'brief_sha256':brief_sha256,'run_id':run_id}.items())
