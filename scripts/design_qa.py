"""Figma-only completion gate; local evidence checks are not Figma live validation."""
import json, pathlib
class DesignQA:
    def __init__(self,root):self.root=pathlib.Path(root)
    def evaluate(self,approved,state_v2,evidence):
        failures=[];required=[s for s in approved.get('screens',[]) if s.get('priority')=='P0']
        if not required:failures.append('No P0 screens in approved plan')
        items=state_v2.get('items',{})
        for s in required:
            sid=s['id'];it=items.get('screen:'+sid,{})
            proof=evidence.get('screens',{}).get(sid,{})
            if it.get('status')!='done' or not it.get('node_id'):failures.append(f'{sid}: P0 screen not done')
            qa=it.get('qa') or {}
            if qa.get('structural')!='passed' or qa.get('visual')!='passed':failures.append(f'{sid}: structural/visual QA not passed')
            if not proof.get('verified_live') or not proof.get('screenshot_ref') or not proof.get('inspection_ref'):failures.append(f'{sid}: live screenshot/inspection missing')
            for status in s.get('states',[]):
                if status not in proof.get('states',[]):failures.append(f'{sid}: missing UI state {status}')
            for flow in s.get('flows',[]):
                if flow not in proof.get('flows',[]):failures.append(f'{sid}: missing flow {flow}')
        if any(it.get('status') in ('creating','updating','legacy_reconcile') for it in items.values()) or evidence.get('pending_wal'):
            failures.append('Unresolved WAL transaction')
        if evidence.get('application_source_files'):failures.append('Design-only violation: application source generated')
        if evidence.get('audit_commands')!='verified_no_build':failures.append('Application build command audit unverified')
        if approved.get('prototype_required') and not evidence.get('prototype_verified'):
            failures.append('Prototype required but unverified or unsupported')
        return {'passed':not failures,'status':'PASS' if not failures else 'QA_INCOMPLETE','p0_total':len(required),'failures':failures,'prototype_status':'verified' if evidence.get('prototype_verified') else 'not_verified','product_code_files_generated':len(evidence.get('application_source_files',[])),'product_build_commands_invoked':0 if evidence.get('audit_commands')=='verified_no_build' else 'unverified'}
    def report(self,approved,state_v2,evidence):
        result=self.evaluate(approved,state_v2,evidence)
        dest=self.root/'design';dest.mkdir(parents=True,exist_ok=True)
        (dest/'WORKFLOW_REPORT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
        (dest/'DESIGN_REPORT.md').write_text('# Figma Design Delivery Report\n\n'+f'Overall: **{result["status"]}**\n\n'+'\n'.join('- '+x for x in result['failures'])+'\n')
        return result
