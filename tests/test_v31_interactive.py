import json,pathlib,tempfile,unittest,subprocess
from unittest.mock import patch
from scripts.runtime_adapters import CodexAdapter
class InteractiveTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);self.root=pathlib.Path(self.d.name)
        (self.root/'config').mkdir()
        (self.root/'config/dependencies.lock.json').write_text(json.dumps({'runtime_clis':{'codex':{'version':'codex-cli 9.1.0','verified_interactive_args':'positional-prompt'}}}))
    def test_exact_pinned_help_allows_interactive_without_shell(self):
        def fake_run(cmd,**kw):
            return subprocess.CompletedProcess(cmd,0,'Usage: codex [OPTIONS] [PROMPT]' if '--help' in cmd else 'codex-cli 9.1.0','')
        with patch('scripts.runtime_adapters.shutil.which',return_value='/fake/codex'):
            with patch('scripts.runtime_adapters.subprocess.run',side_effect=fake_run):
                with patch('scripts.runtime_adapters.subprocess.call',return_value=0) as launch:
                    code=CodexAdapter(self.root).launch_interactive('FIGMA DESIGN ONLY',self.root)
        self.assertEqual(code,0)
        self.assertEqual(launch.call_args.args[0],['codex','FIGMA DESIGN ONLY'])
    def test_mismatched_pin_refuses_to_launch(self):
        def fake_run(cmd,**kw):return subprocess.CompletedProcess(cmd,0,'codex-cli 8.0.0','')
        with patch('scripts.runtime_adapters.shutil.which',return_value='/fake/codex'):
            with patch('scripts.runtime_adapters.subprocess.run',side_effect=fake_run):
                with self.assertRaises(RuntimeError):CodexAdapter(self.root).launch_interactive('prompt',self.root)
