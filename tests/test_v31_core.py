import json, pathlib, tempfile, unittest
from unittest.mock import patch

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        (self.root/'design').mkdir()
    def test_policy_rejects_official_and_approval_bypass(self):
        from scripts.policy import load_policy
        f=self.root/'workflow.yaml'
        f.write_text('version: 1\nbackend: figma-official\nbrainstorm: {required: true, approval_required: true, max_questions: 8}\n')
        with self.assertRaises(ValueError): load_policy(f)
        f.write_text('version: 1\nbackend: talktofigma\nbrainstorm: {required: true, approval_required: false, max_questions: 8}\n')
        with self.assertRaises(ValueError): load_policy(f)
    def test_spec_required_p0_and_safe_path(self):
        from scripts.spec_input import validate_spec
        s=self.root/'specs'/'APP_SPEC.md'; s.parent.mkdir()
        s.write_text('# APP_SPEC\n- Tên ứng dụng: Shop\n- Nền tảng: mobile\n- Mục tiêu sản phẩm: Giúp khách mua hàng\n- Ngôn ngữ giao diện: vi\n## Vai trò người dùng\n| Khách | mua |\n## Chức năng\n|1|View|Khách|P1|abc|\n## Ràng buộc\n- Dark mode: không\n')
        with self.assertRaises(ValueError): validate_spec(s,self.root)
        s.write_text(s.read_text().replace('P1','P0'))
        got=validate_spec(s,self.root)
        self.assertEqual(got.app_name,'Shop')
        self.assertEqual(len(got.p0_features),1)
        with self.assertRaises(ValueError): validate_spec(pathlib.Path('../outside'),self.root)
    def test_goal_and_constraints_are_required(self):
        from scripts.spec_input import validate_spec
        s=self.root/'APP_SPEC.md'
        s.write_text('# APP_SPEC\n- Tên ứng dụng: Shop\n- Nền tảng: mobile\n- Ngôn ngữ giao diện: vi\n## Vai trò người dùng\n|Khách|Mua hàng|\n## Chức năng\n|1|Shop|Khách|P0|abc|\n')
        with self.assertRaises(ValueError):validate_spec(s,self.root)
    def test_workflow_restart_and_no_phase_skip(self):
        from scripts.workflow import WorkflowStore
        s=self.root/'spec.md';s.write_text('spec')
        a=WorkflowStore(self.root).begin(str(s),'codex')
        b=WorkflowStore(self.root).begin(str(s),'codex')
        self.assertEqual(a['run_id'],b['run_id'])
        with self.assertRaises(ValueError): WorkflowStore(self.root).advance('figma_ready')
        self.assertEqual(WorkflowStore(self.root).status()['phase'],'ENVIRONMENT_CHECK')
    def test_approval_requires_human_reference_and_hash(self):
        from scripts.workflow import ApprovalGate
        gate=ApprovalGate(self.root)
        with self.assertRaises(ValueError): gate.record('a'*64,'b'*64,'r1','agent')
        record=gate.record('a'*64,'b'*64,'r1','interactive_user:message-123')
        self.assertEqual(record['approved_by'],'interactive_user')
        self.assertTrue(gate.is_current('a'*64,'b'*64,'r1'))
        self.assertFalse(gate.is_current('a'*64,'c'*64,'r1'))
    def test_writer_lock_contends(self):
        from scripts.writer_lock import WriterLock
        one=WriterLock(self.root)
        with one.acquire('file-a','r1'):
            with self.assertRaises(BlockingIOError): WriterLock(self.root).acquire('file-a','r2').__enter__()
