import hashlib, json, pathlib, tempfile, unittest

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);self.root=pathlib.Path(self.d.name);(self.root/'design').mkdir()
    def test_prompt_is_design_only(self):
        from scripts.design_session import DesignSession
        prompt=DesignSession(self.root).phase_prompt('BRAINSTORMING',{'spec_path':'specs/APP_SPEC.md','run_id':'run1'})
        self.assertIn('Figma',prompt)
        self.assertIn('brainstorming',prompt.lower())
        self.assertIn('KHÔNG',prompt)
    def test_resume_blocks_wal_create(self):
        from scripts.state_bridge import StateBridge
        state={'version':2,'items':{'screen:S01':{'status':'creating','node_id':None,'name':'Home'}}}
        (self.root/'design/STATE.json').write_text(json.dumps(state))
        self.assertEqual(StateBridge(self.root).require_reconcile()[0]['key'],'screen:S01')
    def test_qa_blocks_missing_error_state_and_unverified_build_audit(self):
        from scripts.design_qa import DesignQA
        approved={'screens':[{'id':'S01','priority':'P0','states':['default','error'],'flows':['F01']}],'prototype_required':False}
        state={'items':{'screen:S01':{'status':'done','node_id':'20:9','qa':{'structural':'passed','visual':'passed'}}}}
        evidence={'screens':{'S01':{'states':['default'],'flows':['F01'],'screenshot_ref':'frame1','inspection_ref':'inspect1'}},'application_source_files':[]}
        outcome=DesignQA(self.root).evaluate(approved,state,evidence)
        self.assertFalse(outcome['passed'])
        self.assertIn('state',json.dumps(outcome).lower())
    def test_qa_pass_requires_evidence_and_complete_states(self):
        from scripts.design_qa import DesignQA
        approved={'screens':[{'id':'S01','priority':'P0','states':['default'],'flows':['F01']}],'prototype_required':False}
        state={'items':{'screen:S01':{'status':'done','node_id':'20:9','qa':{'structural':'passed','visual':'passed'}}}}
        evidence={'screens':{'S01':{'states':['default'],'flows':['F01'],'screenshot_ref':'shot','inspection_ref':'inspect','verified_live':True}},'application_source_files':[],'audit_commands':'verified_no_build','pending_wal':[]}
        self.assertTrue(DesignQA(self.root).evaluate(approved,state,evidence)['passed'])
    def test_cli_invalid_args_json_envelope(self):
        from scripts.agent import main
        import io
        from contextlib import redirect_stdout
        f=io.StringIO()
        with redirect_stdout(f):code=main(['retry','--phase','invalid','--json'])
        self.assertEqual(code,2)
        self.assertEqual(set(json.loads(f.getvalue())),{'code','status','reason','next_action','run_id'})
