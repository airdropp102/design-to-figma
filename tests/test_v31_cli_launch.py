import io,json,pathlib,tempfile,unittest
from contextlib import redirect_stdout
from unittest.mock import patch

class DesignLaunchTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup)
        self.root=pathlib.Path(self.d.name)
        (self.root/'workflow.yaml').write_text((pathlib.Path(__file__).resolve().parents[1]/'workflow.yaml').read_text())
        (self.root/'design').mkdir()
        self.spec=self.root/'APP_SPEC.md'
        self.spec.write_text('# APP_SPEC\n- Tên ứng dụng: Shop\n- Mục tiêu sản phẩm: Cho phép khách đặt lịch\n- Nền tảng: mobile\n- Ngôn ngữ giao diện: vi\n## Vai trò người dùng\n| Khách | Đặt lịch |\n## Chức năng\n|1|Book|Khách|P0|abc|\n## Ràng buộc\n- Dark mode: không\n')
    def test_launch_runtime_to_verify_skills_without_pretending_canvas_ready(self):
        from scripts.agent import main
        with patch('scripts.agent.ROOT',self.root):
            with patch('scripts.agent.ReadinessDoctor.check',return_value={'agent_ready':False,'runtimes':{'codex':{'cli':{'available':True}}}}):
                with patch('scripts.agent.DesignSession.launch',return_value=0) as launch:
                    buf=io.StringIO()
                    with redirect_stdout(buf):code=main(['design',str(self.spec),'--runtime','codex'])
        self.assertTrue(launch.called)
        self.assertEqual(code,3)  # active interactive bootstrap, but readiness not proven
