import json, pathlib, subprocess, tempfile, unittest
from scripts.runtime_adapters import ClaudeAdapter,CodexAdapter

class AdapterRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);self.root=pathlib.Path(self.d.name)
        self.checkout=self.root/'.agent/vendor/talktofigma';self.checkout.mkdir(parents=True)
        (self.checkout/'src/talk_to_figma_mcp').mkdir(parents=True)
        (self.checkout/'src/talk_to_figma_mcp/server.ts').write_text('// fake fixture')
        def run(*args):
            subprocess.run(['git','-C',str(self.checkout),*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        run('init','-q');run('add','.');run('-c','user.email=test@example.com','-c','user.name=test','commit','-qm','fixture')
        self.sha=subprocess.run(['git','-C',str(self.checkout),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
        config=self.root/'config';config.mkdir()
        (config/'dependencies.lock.json').write_text(json.dumps({'talktofigma':{'commit_sha':self.sha},'runtime_clis':{'codex':{},'claude':{}}}))
    def test_claude_preserves_other_project_mcp_servers_and_idempotency(self):
        config=self.root/'.mcp.json';config.write_text(json.dumps({'mcpServers':{'Other':{'command':'other'}}}))
        a=ClaudeAdapter(self.root)
        a.register_mcp();once=config.read_text();a.register_mcp();twice=config.read_text()
        d=json.loads(twice)
        self.assertEqual(once,twice)
        self.assertIn('Other',d['mcpServers'])
        self.assertIn('TalkToFigma',d['mcpServers'])
        self.assertNotIn('@latest',twice)
    def test_codex_preserves_unrelated_toml_and_idempotency(self):
        config=self.root/'.codex/config.toml';config.parent.mkdir();config.write_text('[mcp_servers.Other]\ncommand = "other"\n')
        a=CodexAdapter(self.root);a.register_mcp();once=config.read_text();a.register_mcp()
        self.assertEqual(once,config.read_text())
        self.assertIn('[mcp_servers.Other]',once)
        self.assertIn('[mcp_servers.TalkToFigma]',once)
    def test_dirty_checkout_blocks(self):
        (self.checkout/'src/talk_to_figma_mcp/server.ts').write_text('// modified')
        with self.assertRaises(RuntimeError):ClaudeAdapter(self.root).register_mcp()
