"""Black-box regression tests for the option-A TalkToFigma harness.

Run: python3 -m unittest discover -s tests -v
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import io
import contextlib

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "state.py"
sys.path.insert(0, str(ROOT / "scripts"))
import state as state_module


class StateV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        (self.home / "specs").mkdir()
        (self.home / "design").mkdir()
        (self.home / "specs" / "APP_SPEC.md").write_text("# App v1", encoding="utf-8")
        self.env = dict(os.environ, FIGMA_AGENT_STATE=str(self.home / "design" / "STATE.json"))
        self.cmd("init", "--app", "Demo", "--spec", str(self.home / "specs" / "APP_SPEC.md"))
        self.cmd("plan", "screen", "S05", "S05 Chi tiết", "--priority", "P0")
        self.recipe = self.home / "S05.json"
        self.tokens = self.home / "tokens.json"
        self.assets = self.home / "assets.json"
        self.tokens.write_text(json.dumps({"colors": {"primary": "#112233", "unused": "#ffffff"}}))
        self.assets.write_text(json.dumps({"assets": {"hero": {"hash": "a"}, "unused": {"hash": "b"}}}))
        self.write_recipe()

    def cmd(self, *args, ok=True):
        """Execute CLI entrypoint in-process, retaining actual parser + filesystem behavior."""
        prev_argv, prev_cwd = sys.argv, Path.cwd()
        previous_state = state_module.STATE
        out, err = io.StringIO(), io.StringIO()
        rc = 0
        try:
            sys.argv = [str(CLI), *args]
            os.chdir(self.home)
            state_module.STATE = self.env["FIGMA_AGENT_STATE"]
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    state_module.main()
                except SystemExit as ex:
                    rc = ex.code if isinstance(ex.code, int) else 1
        finally:
            os.chdir(prev_cwd)
            sys.argv = prev_argv
            state_module.STATE = previous_state
        if ok and rc != 0:
            self.fail(f"{' '.join(args)} exit={rc}: {out.getvalue()} {err.getvalue()}")
        try:
            result = json.loads(out.getvalue())
        except json.JSONDecodeError:
            result = out.getvalue()
        return rc, result

    def state(self):
        return json.loads((self.home / "design" / "STATE.json").read_text())

    def write_recipe(self, label="Đặt lịch", background="primary", hero="hero", node_type="TEXT"):
        payload = {
            "screen_id": "S05", "name": "S05 Chi tiết",
            "nodes": [
                {"semantic_id": "service.hero", "type": "FRAME", "parent": "root",
                 "layout": {"direction": "VERTICAL"}, "assets": [hero]},
                {"semantic_id": "service.cta", "type": node_type, "parent": "service.hero",
                 "text": label, "tokens": ["colors." + background]},
            ],
        }
        self.recipe.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload

    def paths(self):
        return ("--recipe", str(self.recipe), "--tokens", str(self.tokens),
                "--assets", str(self.assets))

    def complete_screen(self):
        self.cmd("begin", "screen", "S05", "S05 Chi tiết")
        self.cmd("intend", "screen", "S05", *self.paths())
        self.cmd("node", "screen", "S05", "41:7")
        self.cmd("bind", "screen", "S05", "service.cta", "41:9", "--type", "TEXT", "--parent", "41:7", "--verified")
        self.cmd("qa", "screen", "S05", "--structural", "passed", "--visual", "passed")
        self.cmd("done", "screen", "S05")

    def test_migrate_v1_preserves_data_and_is_idempotent(self):
        self.cmd("begin", "screen", "S05", "S05 Chi tiết")
        self.cmd("node", "screen", "S05", "41:7")
        old = self.state()
        self.assertEqual(old["version"], 2)
        old["version"] = 1
        for item in old["items"].values():
            for field in ("semantic_nodes", "intent", "pending_intent", "qa", "metrics"):
                item.pop(field, None)
        (self.home / "design" / "STATE.json").write_text(json.dumps(old))
        self.cmd("migrate")
        st = self.state()
        self.assertEqual(st["version"], 2)
        self.assertEqual(st["items"]["screen:S05"]["node_id"], "41:7")
        self.assertEqual(st["items"]["screen:S05"]["status"], "creating")
        self.assertEqual(st["app"], old["app"])
        self.cmd("migrate")
        self.assertEqual(self.state(), st)

    def test_unmodified_design_skips_but_unrelated_token_does_not_invalidate(self):
        self.cmd("migrate")
        self.complete_screen()
        code, res = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(res["action"], "skip")
        tok = json.loads(self.tokens.read_text())
        tok["colors"]["unused"] = "#000000"
        self.tokens.write_text(json.dumps(tok))
        _, res = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(res["action"], "skip")

    def test_text_only_update_and_crash_recovery_gate(self):
        self.cmd("migrate")
        self.complete_screen()
        self.write_recipe(label="Xác nhận lịch")
        _, res = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(res["action"], "text_patch")
        self.assertEqual(res["changed_text"], ["service.cta"])
        rc, _ = self.cmd("begin-update", "screen", "S05", *self.paths(), ok=False)
        self.assertEqual(rc, 2)  # live read required before mutation
        _, begin = self.cmd("begin-update", "screen", "S05", *self.paths(), "--verified-live")
        self.assertEqual(begin["action"], "text_patch")
        self.assertEqual(self.state()["items"]["screen:S05"]["status"], "updating")
        rc, _ = self.cmd("resume", ok=False)
        self.assertEqual(rc, 3)
        rc, _ = self.cmd("inspect", "screen", "S05", *self.paths(), ok=False)
        self.assertEqual(rc, 3)
        self.cmd("qa", "screen", "S05", "--structural", "passed", "--visual", "passed")
        self.cmd("done-update", "screen", "S05")
        _, result = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(result["action"], "skip")

    def test_token_change_is_style_patch_and_structure_change_is_rebuild(self):
        self.cmd("migrate")
        self.complete_screen()
        tok = json.loads(self.tokens.read_text())
        tok["colors"]["primary"] = "#123456"
        self.tokens.write_text(json.dumps(tok))
        _, res = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(res["action"], "style_patch")
        recipe = self.write_recipe()
        recipe["nodes"][0]["layout"]["direction"] = "HORIZONTAL"
        self.recipe.write_text(json.dumps(recipe, ensure_ascii=False))
        _, res = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(res["action"], "rebuild")

    def test_same_path_asset_byte_change_triggers_rebuild(self):
        self.cmd("migrate")
        image = self.home / "assets" / "images" / "hero.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"asset-v1")
        self.assets.write_text(json.dumps({"images": {"hero": {"file": "assets/images/hero.png"}}}))
        self.write_recipe(hero="images:hero")
        self.complete_screen()
        image.write_bytes(b"asset-v2")
        _, res = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(res["action"], "rebuild")

    def test_visual_qa_mandatory_for_p0(self):
        self.cmd("migrate")
        self.cmd("begin", "screen", "S05", "S05 Chi tiết")
        self.cmd("intend", "screen", "S05", *self.paths())
        self.cmd("node", "screen", "S05", "41:7")
        self.cmd("qa", "screen", "S05", "--structural", "passed", "--visual", "blocked")
        rc, _ = self.cmd("done", "screen", "S05", ok=False)
        self.assertEqual(rc, 2)
        self.cmd("qa", "screen", "S05", "--structural", "passed", "--visual", "passed")
        self.cmd("done", "screen", "S05")
        self.assertEqual(self.state()["items"]["screen:S05"]["status"], "done")

    def test_binding_requires_verified_unique_node_and_parent(self):
        self.cmd("migrate")
        self.cmd("begin", "screen", "S05", "S05 Chi tiết")
        self.cmd("node", "screen", "S05", "41:7")
        rc, _ = self.cmd("bind", "screen", "S05", "service.cta", "41:9", "--type", "TEXT", "--parent", "41:7", ok=False)
        self.assertEqual(rc, 2)
        self.cmd("bind", "screen", "S05", "service.cta", "41:9", "--type", "TEXT", "--parent", "41:7", "--verified")
        rc, _ = self.cmd("bind", "screen", "S05", "service.other", "41:9", "--type", "TEXT", "--parent", "41:7", "--verified", ok=False)
        self.assertEqual(rc, 2)

    def test_missing_state_qa_old_v1_done_remains_untouched(self):
        st = self.state()
        st["version"] = 1
        (self.home / "design" / "STATE.json").write_text(json.dumps(st))
        self.cmd("begin", "screen", "S05", "S05 Chi tiết")
        self.cmd("node", "screen", "S05", "41:7")
        self.cmd("done", "screen", "S05")
        self.cmd("migrate")
        _, r = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(r["action"], "legacy_reconcile")
        self.assertEqual(self.state()["items"]["screen:S05"]["node_id"], "41:7")

    def test_legacy_adopt_after_live_verification_without_rebuild(self):
        st = self.state()
        st["version"] = 1
        (self.home / "design" / "STATE.json").write_text(json.dumps(st))
        self.cmd("begin", "screen", "S05", "S05 Chi tiết")
        self.cmd("node", "screen", "S05", "41:7")
        self.cmd("done", "screen", "S05")
        self.cmd("migrate")
        self.cmd("bind", "screen", "S05", "service.hero", "41:8", "--type", "FRAME", "--parent", "41:7", "--verified")
        self.cmd("bind", "screen", "S05", "service.cta", "41:9", "--type", "TEXT", "--parent", "41:8", "--verified")
        rc, _ = self.cmd("adopt", "screen", "S05", *self.paths(), "--visual", "passed", ok=False)
        self.assertEqual(rc, 2)
        self.cmd("adopt", "screen", "S05", *self.paths(), "--verified-live", "--visual", "passed")
        _, res = self.cmd("inspect", "screen", "S05", *self.paths())
        self.assertEqual(res["action"], "skip")

    def test_metrics_and_no_mutation_when_paused(self):
        self.cmd("migrate")
        self.cmd("metrics", "screen", "S05", "--calls", "7", "--failed", "1", "--batch", "2", "--reused", "3")
        self.assertEqual(self.state()["items"]["screen:S05"]["metrics"]["tool_calls"], 7)
        self.cmd("pause", "--reason", "channel died")
        rc, _ = self.cmd("begin", "screen", "S05", "S05 Chi tiết", ok=False)
        self.assertEqual(rc, 5)
        rc, _ = self.cmd("begin-update", "screen", "S05", *self.paths(), ok=False)
        self.assertEqual(rc, 5)


    def test_updating_cannot_reenter_create_fail_or_reset_blindly(self):
        self.complete_screen()
        self.write_recipe(label="Xác nhận lịch")
        self.cmd("begin-update", "screen", "S05", *self.paths(), "--verified-live")
        for command in (
            ("begin", "screen", "S05", "S05 Chi tiết"),
            ("fail", "screen", "S05", "--note", "unconfirmed"),
            ("reset", "screen", "S05", "--reason", "blind"),
        ):
            rc, _ = self.cmd(*command, ok=False)
            self.assertIn(rc, (2, 3))
        self.assertEqual(self.state()["items"]["screen:S05"]["status"], "updating")

    def test_root_node_cannot_be_silently_replaced(self):
        self.cmd("begin", "screen", "S05", "S05 Chi tiết")
        self.cmd("node", "screen", "S05", "41:7")
        rc, _ = self.cmd("node", "screen", "S05", "41:700", ok=False)
        self.assertEqual(rc, 2)
        self.assertEqual(self.state()["items"]["screen:S05"]["node_id"], "41:7")

    def test_accept_spec_requires_approval_and_preserves_state(self):
        self.cmd("migrate")
        (self.home / "specs" / "APP_SPEC.md").write_text("# App changed", encoding="utf-8")
        rc, _ = self.cmd("check-spec", ok=False)
        self.assertEqual(rc, 4)
        rc, _ = self.cmd("accept-spec", ok=False)
        self.assertEqual(rc, 2)
        self.cmd("accept-spec", "--approved")
        _, status = self.cmd("status")
        self.assertFalse(status["spec_changed"])
        self.assertIn("screen:S05", self.state()["items"])

    def test_reject_malformed_recipe_or_missing_token(self):
        self.cmd("migrate")
        self.write_recipe(background="no_such_token")
        rc, _ = self.cmd("inspect", "screen", "S05", *self.paths(), ok=False)
        self.assertEqual(rc, 2)
        self.write_recipe()
        recipe = json.loads(self.recipe.read_text())
        recipe["nodes"].append(recipe["nodes"][1])
        self.recipe.write_text(json.dumps(recipe))
        rc, _ = self.cmd("inspect", "screen", "S05", *self.paths(), ok=False)
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
