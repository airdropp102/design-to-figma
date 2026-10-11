import json, pathlib, subprocess, tempfile, unittest
from unittest.mock import patch
from scripts.bootstrap import setup, prepare_checkout

class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);self.root=pathlib.Path(self.d.name)
        (self.root/'config').mkdir();(self.root/'.agent/vendor/talktofigma').mkdir(parents=True)
        checkout=self.root/'.agent/vendor/talktofigma'
        (checkout/'src/talk_to_figma_mcp').mkdir(parents=True)
        (checkout/'src/talk_to_figma_mcp/server.ts').write_text('// stable fake fixture')
        def git(*args):subprocess.run(['git','-C',str(checkout),*args],check=True,capture_output=True)
        git('init','-q');git('add','.');git('-c','user.email=fixture@test','-c','user.name=fixture','commit','-qm','test')
        self.sha=subprocess.run(['git','-C',str(checkout),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
        self.lock={'talktofigma':{'repository':'https://github.com/grab/cursor-talk-to-figma-mcp','commit_sha':self.sha},'superpowers':{'commit_sha':self.sha},'ui_ux_pro_max':{'release_version':'1.2.3'},'runtime_clis':{'claude':{},'codex':{}}}
        self.lockpath=self.root/'config/dependencies.lock.json';self.lockpath.write_text(json.dumps(self.lock))
    def test_valid_local_checkout_verifies_and_registers_project_scope(self):
        result=prepare_checkout(self.root,self.lock)
        self.assertEqual(result['sha'],self.sha)
        with patch('scripts.bootstrap.shutil.which',return_value='/usr/bin/tool'):
            with patch('scripts.bootstrap.SocketSupervisor.up',return_value={'running':True}):
                out=setup(self.root,'claude')
        self.assertIn('TalkToFigma', (self.root/'.mcp.json').read_text())
        self.assertEqual(out['status'],'action_required') # skills still cannot be proven installed
    def test_socket_attempted_when_skills_require_user_action(self):
        with patch('scripts.bootstrap.shutil.which',return_value='/usr/bin/tool'):
            with patch('scripts.bootstrap.SocketSupervisor.up',return_value={'running':True,'owned':True}) as start:
                out=setup(self.root,'claude')
        self.assertTrue(start.called)
        self.assertEqual(out['status'],'action_required')
    def test_untrusted_origin_rejected_without_cloning(self):
        self.lock['talktofigma']['repository']='https://evil.example/fake'
        with self.assertRaises(ValueError):prepare_checkout(self.root,self.lock)
    def test_modified_checkout_never_reset(self):
        (self.root/'.agent/vendor/talktofigma/src/talk_to_figma_mcp/server.ts').write_text('changed')
        with self.assertRaises(RuntimeError):prepare_checkout(self.root,self.lock)
