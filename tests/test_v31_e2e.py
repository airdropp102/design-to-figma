import json, pathlib, tempfile, unittest, hashlib
from unittest.mock import patch

class WorkflowE2ETests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        (self.root/'design').mkdir()
        (self.root/'workflow.yaml').write_text((pathlib.Path(__file__).resolve().parents[1]/'workflow.yaml').read_text())
        self.spec=self.root/'spec.md'
        self.spec.write_text('# Example spec')
    def evidence(self,filename,**kwargs):
        path=self.root/filename
        path.write_text(json.dumps({'verified':True,**kwargs}))
        return path
    def test_end_to_end_blocked_before_brainstorm_approval(self):
        from scripts.workflow import WorkflowStore
        w=WorkflowStore(self.root)
        w.begin(str(self.spec),'codex')
        w.advance('environment_ready',self.evidence('env.json',runtime_version='codex-cli pinned',skills={'superpowers':True,'ui-ux-pro-max':True},mcp_registration_ref='project-config'))
        w.advance('spec_valid',self.evidence('spec.json'))
        self.assertEqual(w.status()['phase'],'BRAINSTORMING')
        with self.assertRaises(ValueError):w.advance('approved',self.evidence('approval.json'))
        (self.root/'design/BRAINSTORM.md').write_text('Design brief draft')
        w.advance('brainstorm_drafted',self.evidence('brief.json'))
        with self.assertRaises(ValueError):w.advance('approved',self.evidence('approval.json'))
        self.assertEqual(w.status()['phase'],'AWAITING_APPROVAL')
    def test_checkpoint_requires_delivery_reports(self):
        from scripts.workflow import WorkflowStore
        w=WorkflowStore(self.root)
        w.begin(str(self.spec),'codex')
        # test transition only once persisted legitimately; ensure no free pass at the end
        d=w.status();d['phase']='DELIVERY';w._save(d,'test-fixture')
        with self.assertRaises(ValueError):w.advance('delivery_ready',self.evidence('done.json'))
    def test_figma_gate_requires_identity_and_permission_proof(self):
        from scripts.workflow import WorkflowStore
        w=WorkflowStore(self.root);w.begin(str(self.spec),'codex')
        d=w.status();d['phase']='FIGMA_CONNECTION_GATE';w._save(d,'test-fixture')
        with self.assertRaises(ValueError):w.advance('figma_ready',self.evidence('figma.json'))
    def test_app_spec_limit_25_screen_rows(self):
        from scripts.spec_input import validate_spec
        s=self.root/'specs/APP_SPEC.md';s.parent.mkdir()
        rows='\n'.join(f'| S{i:02d} | Screen {i} | Khách | P0 | detail |' for i in range(26))
        s.write_text('# APP_SPEC\n- Tên ứng dụng: Shop\n- Nền tảng: mobile\n- Mục tiêu sản phẩm: Giúp khách mua hàng\n- Ngôn ngữ giao diện: vi\n## Vai trò người dùng\n|Khách|Mua hàng|\n## Chức năng\n|#|Chức năng|Vai trò|Ưu tiên (P0/P1/P2)|Mô tả|\n'+rows+'\n## Ràng buộc\n- Dark mode: không')
        with self.assertRaises(ValueError):validate_spec(s,self.root)
