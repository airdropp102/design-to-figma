import json, pathlib, tempfile, unittest, os
from unittest.mock import patch

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);self.root=pathlib.Path(self.d.name)
        (self.root/'.agent/runtime').mkdir(parents=True)
    def test_doctor_does_not_imply_figma_from_socket(self):
        from scripts.readiness import ReadinessDoctor
        with patch('scripts.readiness.shutil.which',return_value='/usr/bin/tool'):
            doc=ReadinessDoctor(self.root).check('codex')
        self.assertFalse(doc['figma_ready'])
        self.assertFalse(doc['canvas_ready'])
    def test_unowned_port_cannot_be_stopped(self):
        from scripts.socket_supervisor import SocketSupervisor
        supervisor=SocketSupervisor(self.root)
        got=supervisor.down()
        self.assertFalse(got['stopped'])
    def test_adapter_fails_closed_without_verified_launch_syntax(self):
        from scripts.runtime_adapters import CodexAdapter
        with self.assertRaises(RuntimeError):CodexAdapter(self.root).launch_interactive('do design',self.root)
    def test_setup_reports_missing_bins_and_does_not_install_random_latest(self):
        from scripts.bootstrap import setup
        with patch('scripts.bootstrap.shutil.which',return_value=None):
            result=setup(self.root,'both')
        self.assertEqual(result['status'],'action_required')
        self.assertIn('bun',result['missing'])
    def test_skill_absent_is_not_ready(self):
        from scripts.runtime_adapters import ClaudeAdapter
        a=ClaudeAdapter(self.root)
        self.assertFalse(a.verify_skill('ui-ux-pro-max')['ready'])
