import pathlib,tempfile,unittest,json
from unittest.mock import patch

class ReadinessGateTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup)
        self.root=pathlib.Path(self.d.name);(self.root/'design').mkdir();(self.root/'spec.md').write_text('spec')
    def test_environment_transition_requires_skill_evidence(self):
        from scripts.workflow import WorkflowStore
        w=WorkflowStore(self.root);w.begin(str(self.root/'spec.md'),'codex')
        with self.assertRaises(ValueError):w.advance('environment_ready')
    def test_invalid_environment_evidence_cannot_advance(self):
        from scripts.workflow import WorkflowStore
        w=WorkflowStore(self.root);w.begin(str(self.root/'spec.md'),'codex')
        f=self.root/'evidence.json';f.write_text(json.dumps({'verified':True,'skills':{'superpowers':False}}))
        with self.assertRaises(ValueError):w.advance('environment_ready',f)
    def test_interactive_design_session_uses_workspace_lock(self):
        from scripts.design_session import DesignSession
        spec=self.root/'spec.md'
        class FakeAdapter:
            def launch_interactive(self,prompt,cwd):
                from scripts.writer_lock import WriterLock
                with self.assert_lock_not_possible(cwd):
                    return 0
            def assert_lock_not_possible(self,root):
                from contextlib import contextmanager
                @contextmanager
                def check():
                    from scripts.writer_lock import WriterLock
                    with self_case.assertRaises(BlockingIOError):
                        WriterLock(root).acquire('any-target','r2').__enter__()
                    yield
                return check()
        self_case=self
        with patch('scripts.spec_input.validate_spec') as validate:
            validate.return_value=type('S',(),{'spec_path':str(spec)})
            with patch('scripts.design_session.get_adapter',return_value=FakeAdapter()):
                self.assertEqual(DesignSession(self.root).launch(spec,'codex'),0)
