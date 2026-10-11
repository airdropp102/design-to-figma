"""Read-only reconciliation before delegation to existing state.py v2 CLI."""
import json, pathlib, subprocess, sys
class StateBridge:
    def __init__(self,root):self.root=pathlib.Path(root)
    def state(self):
        file=self.root/'design/STATE.json'
        return json.loads(file.read_text()) if file.exists() else {'items':{}}
    def require_reconcile(self):
        return [{'key':k,'status':v.get('status'),'node_id':v.get('node_id'),'name':v.get('name')} for k,v in self.state().get('items',{}).items() if v.get('status') in ('creating','updating','legacy_reconcile')]
    @staticmethod
    def is_verified_permission_probe(wal, evidence):
        """A single empty registered root can prove write access at the connection gate.

        This does not finish or replay its WAL transaction. All other open WAL
        entries, populated roots, and update transactions still require recovery.
        """
        if len(wal) != 1 or evidence.get('verified') is not True:
            return False
        item = wal[0]
        probe = evidence.get('permission_probe', {})
        if not isinstance(probe, dict):
            return False
        return bool(
            item.get('key', '').startswith('screen:')
            and item.get('status') == 'creating'
            and item.get('node_id')
            and probe.get('live_verified') is True
            and probe.get('node_id') == item['node_id']
            and probe.get('name') == item.get('name')
            and probe.get('type') == 'FRAME'
            and probe.get('child_count') == 0
            and evidence.get('page_id')
            and probe.get('page_id') == evidence['page_id']
            and evidence.get('figma_file_id')
            and probe.get('file_key') == evidence['figma_file_id']
        )
    def _call(self,*args):
        cp=subprocess.run([sys.executable,'scripts/state.py',*args],cwd=str(self.root),capture_output=True,text=True)
        if cp.returncode:raise RuntimeError(f'state.py exit={cp.returncode}: {cp.stdout.strip()} {cp.stderr.strip()}')
        return json.loads(cp.stdout)
    def plan_screens(self,plan_path):
        obj=json.loads(pathlib.Path(plan_path).read_text())
        if len(obj.get('screens',[]))>25:raise ValueError('Too many screens in one run')
        result=[]
        for s in obj['screens']:result.append(self._call('plan','screen',s['id'],s['name'],'--priority',s.get('priority','P0')))
        return {'planned':result}
    def inspect_screen(self,recipe,tokens,assets,screen_id):
        if self.require_reconcile():raise RuntimeError('Open WAL; live reconciliation required')
        return self._call('inspect','screen',screen_id,'--recipe',str(recipe),'--tokens',str(tokens),'--assets',str(assets))
    def commit_qa(self,screen_id,evidence_path):
        evidence=json.loads(pathlib.Path(evidence_path).read_text())
        if not (evidence.get('verified_live') and evidence.get('figma_file_id') and evidence.get('page_id')):raise ValueError('Missing live document identity')
        if self.require_reconcile():raise RuntimeError('Open WAL; do not commit QA')
        return self._call('qa','screen',screen_id,'--structural',evidence['structural'],'--visual',evidence['visual'])
