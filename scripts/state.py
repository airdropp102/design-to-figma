#!/usr/bin/env python3
"""Sổ trạng thái cho Figma design agent. Chỉ dùng thư viện chuẩn.

Nguyên tắc chống làm trùng (write-ahead):
  1. `begin`  : ghi ý định (status=creating) TRƯỚC khi gọi tool Figma.
  2. `node`   : ghi nodeId ngay sau create_frame/create_section.
  3. `done`   : ghi hoàn thành SAU khi dựng xong và kiểm tra.
  Nếu phiên chết giữa chừng, mục còn 'creating' => lần sau `begin` trả mã 3
  và agent phải đối soát với Figma (theo nodeId hoặc theo TÊN) trước khi tạo lại.

Mọi lần ghi: khóa -> đọc -> sửa -> ghi tệp tạm -> os.replace (nguyên tử).
Mã thoát: 0 ok | 2 sai tham số/thiếu dữ liệu | 3 cần đối soát | 4 spec đã đổi | 5 đang tạm dừng
Đổi vị trí sổ bằng biến môi trường FIGMA_AGENT_STATE (mặc định design/STATE.json).
"""
import argparse
import contextlib
import hashlib
import json
import os
import sys
import tempfile
import time

from intent import compute_intent, classify

STATE = os.environ.get("FIGMA_AGENT_STATE", "design/STATE.json")
KINDS = ("section", "component", "screen")
PRIO = {"P0": 0, "P1": 1, "P2": 2}
MAX_ATTEMPTS = 3
PHASES = ("0", "0.5", "1", "1.5", "2", "3", "4", "5", "done")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def die(msg, code=2):
    out({"error": msg}, code)


def journal(event, key="", detail=""):
    p = os.path.join(os.path.dirname(os.path.abspath(STATE)), "journal.log")
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{now()} | {event} | {key} | {detail}\n")


@contextlib.contextmanager
def lock(timeout=10.0):
    path = os.path.abspath(STATE) + ".lock"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = time.time()
    while True:
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except FileExistsError:
            with contextlib.suppress(OSError):
                if time.time() - os.path.getmtime(path) > 30:  # khóa mồ côi
                    os.remove(path)
                    continue
            if time.time() - start > timeout:
                die("Không lấy được khóa STATE.json (tiến trình khác đang ghi?)")
            time.sleep(0.1)
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            os.remove(path)


def load():
    if not os.path.exists(STATE):
        die(f"Chưa có {STATE}. Chạy: state.py init --app <Tên> --spec specs/APP_SPEC.md")
    with open(STATE, encoding="utf-8") as f:
        return json.load(f)


def save(st):
    st["updated_at"] = now()
    d = os.path.dirname(os.path.abspath(STATE))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".state.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def spec_changed(st):
    p = st.get("spec_path")
    if not p or not os.path.exists(p):
        return None
    return sha256(p) != st.get("spec_sha256")


def ikey(kind, key):
    if kind not in KINDS:
        die(f"kind phải là một trong {KINDS}")
    return f"{kind}:{key}"


def get_item(st, kind, key):
    it = st["items"].get(ikey(kind, key))
    if not it:
        die(f"Chưa plan {kind}:{key}. Dùng `plan`/`plan-bulk` trước (tránh gõ sai ID).")
    return it


def add_item(st, kind, key, name, prio):
    k = ikey(kind, key)
    if k in st["items"]:
        return False
    if any(i["name"] == name for i in st["items"].values()):
        die(f"Tên '{name}' đã dùng cho mục khác. Tên khung là khóa đối soát nên phải duy nhất.")
    st["items"][k] = {"kind": kind, "key": key, "name": name, "priority": prio,
                      "status": "pending", "node_id": None, "attempts": 0,
                      "note": "", "updated_at": now()}
    if st.get("version", 1) >= 2:
        st["items"][k].update(semantic_nodes={}, intent=None, pending_intent=None,
            qa={"structural": "not_checked", "visual": "not_checked"},
            metrics={"tool_calls": 0, "failed_calls": 0, "batch_calls": 0, "reused_nodes": 0})

    return True


# ---------------------------------------------------------------- lệnh
def cmd_init(a):
    with lock():
        if os.path.exists(STATE) and not a.force:
            st = load()
            out({"status": "exists", "app": st["app"], "spec_changed": spec_changed(st)})
        if not os.path.exists(a.spec):
            die(f"Không thấy spec: {a.spec}")
        st = {"version": 2, "app": a.app, "spec_path": a.spec, "spec_sha256": sha256(a.spec),
              "created_at": now(), "updated_at": now(), "phase": "0", "paused": None,
              "figma": {"channel": None, "file": None, "page": None}, "items": {}}
        save(st)
        journal("init", a.app)
        out({"status": "created", "state": STATE})


def cmd_phase(a):
    if a.value not in PHASES:
        die(f"phase phải thuộc {PHASES}")
    with lock():
        st = load()
        st["phase"] = a.value
        save(st)
        journal("phase", a.value)
    out({"phase": a.value})


def cmd_figma(a):
    with lock():
        st = load()
        for f in ("channel", "file", "page"):
            v = getattr(a, f)
            if v is not None:
                st["figma"][f] = v
        save(st)
        journal("figma", "", json.dumps(st["figma"], ensure_ascii=False))
    out({"figma": st["figma"]})


def cmd_plan(a):
    with lock():
        st = load()
        created = add_item(st, a.kind, a.key, a.name, a.priority)
        save(st)
    out({"planned": created, "key": ikey(a.kind, a.key)})


def cmd_plan_bulk(a):
    n = 0
    with lock():
        st = load()
        for line in sys.stdin:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2:
                die(f"Dòng sai (cần KEY|NAME[|P0]): {line}")
            prio = parts[2] if len(parts) > 2 and parts[2] in PRIO else "P0"
            n += add_item(st, a.kind, parts[0], parts[1], prio)
        save(st)
        journal("plan-bulk", a.kind, f"+{n}")
    out({"added": n, "total": len(st["items"])})


def cmd_begin(a):
    with lock():
        st = load()
        if st["paused"]:
            out({"error": "paused", "reason": st["paused"]["reason"],
                 "hint": "Chạy Pha R (đối soát) rồi `state.py resume`"}, 5)
        it = get_item(st, a.kind, a.key)
        if it["name"] != a.name:
            die(f"Tên không khớp kế hoạch: '{it['name']}' != '{a.name}'")
        if it["status"] == "done":
            out({"action": "skip", "node_id": it["node_id"]})
        if it["status"] in ("creating", "updating"):
            out({"action": "reconcile", "status": it["status"], "node_id": it["node_id"], "name": it["name"],
                 "hint": "Lần trước chưa xong. Đối soát với Figma (nodeId hoặc tên) trước khi tạo."}, 3)
        if it["attempts"] >= MAX_ATTEMPTS:
            die(f"{a.kind}:{a.key} đã thử {it['attempts']} lần — bị chặn, cần người xem.")
        it.update(status="creating", node_id=None, attempts=it["attempts"] + 1, updated_at=now())
        if st.get("version", 1) >= 2:
            it["qa"] = {"structural": "not_checked", "visual": "not_checked"}
            it["pending_intent"] = None
            it["semantic_nodes"] = {}
        save(st)
        journal("begin", ikey(a.kind, a.key), f"attempt={it['attempts']}")
    out({"action": "create", "attempt": it["attempts"], "name": it["name"]})


def cmd_node(a):
    with lock():
        st = load()
        it = get_item(st, a.kind, a.key)
        if it["status"] != "creating":
            die(f"{a.kind}:{a.key} không ở trạng thái creating (đang {it['status']}).")
        if it.get("node_id") and it["node_id"] != a.node_id:
            die("Root node đã ghi trong WAL, không được thay ID mà chưa đối soát")
        it.update(node_id=a.node_id, updated_at=now())
        save(st)
        journal("node", ikey(a.kind, a.key), a.node_id)
    out({"ok": True})


def cmd_done(a):
    with lock():
        st = load()
        it = get_item(st, a.kind, a.key)
        if it["status"] != "creating":
            die(f"{a.kind}:{a.key} không ở trạng thái creating (đang {it['status']}).")
        nid = a.node_id or it["node_id"]
        if not nid:
            die("Thiếu node_id (truyền vào hoặc chạy `node` trước).")
        if st.get("version", 1) >= 2:
            validate_qa(it)
            if it["kind"] == "screen" and not it.get("pending_intent"):
                die("Screen thiếu intent đã tính từ recipe; chạy `intend` trước")
            if it.get("pending_intent"):
                it["intent"] = it.pop("pending_intent")
        it.update(status="done", node_id=nid, note=a.note or "", updated_at=now())
        save(st)
        journal("done", ikey(a.kind, a.key), nid)
    out({"ok": True, "node_id": nid})


def cmd_fail(a):
    with lock():
        st = load()
        it = get_item(st, a.kind, a.key)
        if st.get("version", 1) >= 2 and it["status"] == "updating":
            die("Không fail item updating khi Figma có thể đã áp dụng một phần; pause rồi reconcile", 3)
        it.update(status="failed", note=a.note, updated_at=now())
        save(st)
        journal("fail", ikey(a.kind, a.key), a.note)
    out({"ok": True, "attempts": it["attempts"]})


def cmd_reset(a):
    with lock():
        st = load()
        it = get_item(st, a.kind, a.key)
        if st.get("version", 1) >= 2 and it["status"] == "updating":
            die("Không reset item updating vì có thể đã patch một phần; pause và kiểm tra live", 3)
        old = it["node_id"]
        it.update(status="pending", node_id=None, note=f"reset: {a.reason} (nodeId cũ {old})",
                  updated_at=now())
        if st.get("version", 1) >= 2:
            it["semantic_nodes"] = {}
            it["pending_intent"] = None
            it["intent"] = None
            it["qa"] = {"structural": "not_checked", "visual": "not_checked"}
        if a.forgive:
            it["attempts"] = 0
        save(st)
        journal("reset", ikey(a.kind, a.key), a.reason)
    out({"ok": True, "old_node_id": old})


def cmd_pause(a):
    with lock():
        st = load()
        st["paused"] = {"reason": a.reason, "at": now()}
        save(st)
        journal("pause", "", a.reason)
    out({"paused": True, "reason": a.reason})


def cmd_resume(a):
    with lock():
        st = load()
        if any(i["status"] in ("creating", "updating") for i in st["items"].values()) and not a.force:
            die("Còn mục 'creating' chưa đối soát. Đối soát + reset trước, hoặc dùng --force.", 3)
        st["paused"] = None
        save(st)
        journal("resume")
    out({"paused": False})


def pick_next(st):
    c = [i for i in st["items"].values()
         if i["status"] in ("pending", "failed", "lost") and i["attempts"] < MAX_ATTEMPTS]
    order = {k: n for n, k in enumerate(st["items"])}
    c.sort(key=lambda i: (PRIO.get(i["priority"], 9), order[ikey(i["kind"], i["key"])]))
    return c[0] if c else None


def cmd_next(a):
    st = load()
    n = pick_next(st)
    out({"next": n})


def summarize(st):
    counts = {}
    for i in st["items"].values():
        counts[i["status"]] = counts.get(i["status"], 0) + 1
    return {
        "app": st["app"], "phase": st["phase"], "paused": st["paused"],
        "spec_changed": spec_changed(st), "figma": st["figma"], "counts": counts,
        "creating": [i for i in st["items"].values() if i["status"] in ("creating", "updating")],
        "blocked": [i["key"] for i in st["items"].values()
                    if i["status"] in ("failed", "lost", "pending") and i["attempts"] >= MAX_ATTEMPTS],
        "next": pick_next(st),
    }


def cmd_status(a):
    s = summarize(load())
    if not a.text:
        out(s)
    c = s["counts"]
    print(f"[Figma agent] app={s['app']} phase={s['phase']} "
          + " ".join(f"{k}={v}" for k, v in sorted(c.items())))
    if s["paused"]:
        print(f"  TẠM DỪNG: {s['paused']['reason']} ({s['paused']['at']})")
    if s["spec_changed"]:
        print("  CẢNH BÁO: APP_SPEC.md đã đổi từ lần chạy trước — hỏi người dùng trước khi tiếp tục.")
    for i in s["creating"]:
        print(f"  CẦN ĐỐI SOÁT: {i['kind']}:{i['key']} status={i['status']} ({i['name']}) nodeId={i['node_id']}")
    if s["blocked"]:
        print(f"  BỊ CHẶN (>= {MAX_ATTEMPTS} lần): {', '.join(s['blocked'])}")
    if s["next"]:
        print(f"  Tiếp theo: {s['next']['kind']}:{s['next']['key']} ({s['next']['name']})")
    print("  Việc đầu tiên khi mở phiên: làm Pha R trong AGENTS.md.")
    sys.exit(0)


def cmd_ids(a):
    st = load()
    ids = [i["node_id"] for i in st["items"].values() if i["status"] == a.status and i["node_id"]]
    out({"status": a.status, "node_ids": ids})


def cmd_check_spec(a):
    st = load()
    ch = spec_changed(st)
    out({"spec_changed": ch}, 4 if ch else 0)


# ---------------------------------------------------- TalkToFigma-only v2

def require_v2(st):
    if st.get("version", 1) != 2:
        die("State v1: chạy `python3 scripts/state.py migrate` trước")


def make_intent(a):
    try:
        return compute_intent(a.recipe, a.tokens, a.assets)
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
        die(f"Invalid screen recipe/tokens/assets: {exc}")


def ensure_target(it, intent):
    if it["kind"] != "screen" or it["key"] != intent["screen_id"] or it["name"] != intent["name"]:
        die("Recipe identity (screen_id/name) does not match planned screen")


def validate_qa(it):
    qa = it.get("qa") or {}
    if qa.get("structural") != "passed":
        die("Structural QA chưa passed: không được commit")
    if it["kind"] == "screen" and it["priority"] == "P0" and qa.get("visual") != "passed":
        die("P0 bắt buộc visual QA passed: không được commit")
    if qa.get("visual") not in ("passed", "skipped"):
        die("Visual QA chưa passed/skipped: không được commit")


def cmd_migrate(a):
    with lock():
        st = load()
        if st.get("version") == 2:
            out({"version": 2, "migrated": False})
        if st.get("version") != 1:
            die(f"Unsupported state version: {st.get('version')}")
        st["version"] = 2
        for it in st["items"].values():
            it.setdefault("semantic_nodes", {})
            it.setdefault("intent", None)
            it.setdefault("pending_intent", None)
            it.setdefault("qa", {"structural": "not_checked", "visual": "not_checked"})
            it.setdefault("metrics", {"tool_calls": 0, "failed_calls": 0, "batch_calls": 0, "reused_nodes": 0})
        save(st)
        journal("migrate", "v1-to-v2")
    out({"version": 2, "migrated": True})


def cmd_intend(a):
    intent = make_intent(a)
    with lock():
        st = load()
        require_v2(st)
        it = get_item(st, a.kind, a.key)
        if it["status"] != "creating":
            die("intend chỉ được gọi khi creating")
        ensure_target(it, intent)
        it["pending_intent"] = intent
        it["qa"] = {"structural": "not_checked", "visual": "not_checked"}
        save(st)
        journal("intend", ikey(a.kind, a.key), str(intent["hashes"]))
    out({"ok": True, "hashes": intent["hashes"]})


def cmd_inspect(a):
    intent = make_intent(a)
    st = load()
    require_v2(st)
    it = get_item(st, a.kind, a.key)
    ensure_target(it, intent)
    if it["status"] in ("creating", "updating"):
        out({"action": "reconcile", "status": it["status"], "node_id": it.get("node_id")}, 3)
    if it["status"] != "done":
        out({"action": "create", "status": it["status"]})
    diff = classify(it.get("intent"), intent)
    out({**diff, "node_id": it.get("node_id"),
         "note": "Dùng get_nodes_info để xác nhận ID/type/parent trước khi gọi mutation"})


def patch_targets(old, new, diff):
    affected = set(diff.get("changed_text", []))
    if diff["action"] in ("style_patch", "mixed_patch"):
        old_styles = old["snapshot"]["style"]
        new_styles = new["snapshot"]["style"]
        affected.update(k for k in set(old_styles) | set(new_styles) if old_styles.get(k) != new_styles.get(k))
    return sorted(affected)


def cmd_begin_update(a):
    intent = make_intent(a)
    with lock():
        st = load()
        require_v2(st)
        if st["paused"]:
            out({"error": "paused", "reason": st["paused"]["reason"]}, 5)
        it = get_item(st, a.kind, a.key)
        ensure_target(it, intent)
        if it["status"] != "done":
            die(f"begin-update cần status done (đang {it['status']})", 3)
        diff = classify(it.get("intent"), intent)
        if diff["action"] in ("skip", "legacy_reconcile", "rebuild"):
            out(diff)
        if not a.verified_live:
            die("Trước begin-update: dùng get_nodes_info kiểm tra file, node ID, type, parent rồi thêm --verified-live")
        affected = patch_targets(it["intent"], intent, diff)
        unmapped = [x for x in affected if x not in it.get("semantic_nodes", {})]
        if unmapped:
            die(f"Semantic IDs chưa bind/verify trên Figma: {unmapped}")
        it["status"] = "updating"
        it["pending_intent"] = intent
        it["qa"] = {"structural": "not_checked", "visual": "not_checked"}
        it["updated_at"] = now()
        save(st)
        journal("begin-update", ikey(a.kind, a.key), f"{diff['action']} {affected}")
    out({**diff, "target_node_ids": {k: it["semantic_nodes"][k]["node_id"] for k in affected}})


def cmd_done_update(a):
    with lock():
        st = load()
        require_v2(st)
        it = get_item(st, a.kind, a.key)
        if it["status"] != "updating" or not it.get("pending_intent"):
            die("done-update chỉ dành cho mục updating có pending_intent")
        validate_qa(it)
        it["intent"] = it.pop("pending_intent")
        it["status"] = "done"
        it["updated_at"] = now()
        save(st)
        journal("done-update", ikey(a.kind, a.key), it["node_id"] or "")
    out({"ok": True, "node_id": it["node_id"]})


def cmd_bind(a):
    with lock():
        st = load()
        require_v2(st)
        it = get_item(st, a.kind, a.key)
        if it["status"] not in ("creating", "updating") and not (
            it["status"] == "done" and it.get("intent") is None
        ):
            die("bind chỉ dùng khi creating/updating hoặc khi đối soát legacy done chưa có intent")
        if not a.verified:
            die("Phải xác nhận node tồn tại/type/parent bằng get_node_info(s), sau đó thêm --verified")
        if not a.node_id or not a.semantic_id or not a.parent:
            die("node_id, semantic_id và parent không được rỗng")
        bound = it.setdefault("semantic_nodes", {})
        if a.parent != it.get("node_id") and a.parent not in {x["node_id"] for x in bound.values()}:
            die("parent không thuộc root hoặc semantic registry đã kiểm chứng")
        if any(x["node_id"] == a.node_id for k, x in bound.items() if k != a.semantic_id):
            die("node_id đã bind cho semantic ID khác")
        for other in st["items"].values():
            if other is it:
                continue
            if other.get("node_id") == a.node_id or any(x["node_id"] == a.node_id for x in other.get("semantic_nodes", {}).values()):
                die("node_id đã thuộc mục khác")
        bound[a.semantic_id] = {"node_id": a.node_id, "type": a.type, "parent": a.parent, "verified_at": now()}
        save(st)
        journal("bind", ikey(a.kind, a.key), f"{a.semantic_id}={a.node_id}")
    out({"ok": True, "semantic_id": a.semantic_id, "node_id": a.node_id})


def cmd_qa(a):
    with lock():
        st = load()
        require_v2(st)
        it = get_item(st, a.kind, a.key)
        if it["status"] not in ("creating", "updating"):
            die("qa chỉ dùng khi creating/updating")
        it["qa"] = {"structural": a.structural, "visual": a.visual}
        save(st)
        journal("qa", ikey(a.kind, a.key), f"{a.structural}/{a.visual}")
    out({"qa": it["qa"]})


def cmd_adopt(a):
    intent = make_intent(a)
    with lock():
        st = load()
        require_v2(st)
        it = get_item(st, a.kind, a.key)
        ensure_target(it, intent)
        if st.get("paused"):
            die("State đang paused, phải đối soát trước", 5)
        if it["status"] != "done" or it.get("intent") is not None or not it.get("node_id"):
            die("adopt chỉ dành cho màn done từ state v1 chưa có intent và còn root node")
        if not a.verified_live:
            die("adopt đòi hỏi kiểm tra live Figma tất cả semantic nodes và root: --verified-live")
        required = {n["semantic_id"] for n in intent["snapshot"]["structure"]}
        missing = sorted(required - set(it.get("semantic_nodes", {})))
        if missing:
            die(f"Cần bind các semantic node sau khi đọc live trước adopt: {missing}")
        it["qa"] = {"structural": "passed", "visual": a.visual}
        validate_qa(it)
        it["intent"] = intent
        it["updated_at"] = now()
        save(st)
        journal("adopt", ikey(a.kind, a.key), it["node_id"])
    out({"ok": True, "node_id": it["node_id"], "action": "adopted"})


def cmd_accept_spec(a):
    if not a.approved:
        die("Cần --approved sau khi người dùng duyệt thay đổi APP_SPEC.md")
    with lock():
        st = load()
        p = st.get("spec_path")
        if not p or not os.path.exists(p):
            die("Không đọc được APP_SPEC.md")
        if any(i["status"] in ("creating", "updating") for i in st["items"].values()):
            die("Còn transaction dở; reconcile trước khi accept-spec", 3)
        st["spec_sha256"] = sha256(p)
        save(st)
        journal("accept-spec", "", st["spec_sha256"])
    out({"spec_changed": False, "approved": True})


def cmd_metrics(a):
    with lock():
        st = load()
        require_v2(st)
        it = get_item(st, a.kind, a.key)
        m = it.setdefault("metrics", {"tool_calls": 0, "failed_calls": 0, "batch_calls": 0, "reused_nodes": 0})
        for field, value in (("tool_calls", a.calls), ("failed_calls", a.failed),
                             ("batch_calls", a.batch), ("reused_nodes", a.reused)):
            if value < 0:
                die("Metrics không được âm")
            m[field] += value
        if m["failed_calls"] > m["tool_calls"] or m["batch_calls"] > m["tool_calls"]:
            die("failed/batch calls không thể vượt quá tổng calls")
        save(st)
        journal("metrics", ikey(a.kind, a.key), json.dumps(m))
    out({"metrics": m})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def sp(name, fn, **kw):
        s = sub.add_parser(name, **kw)
        s.set_defaults(fn=fn)
        return s

    s = sp("init", cmd_init)
    s.add_argument("--app", required=True)
    s.add_argument("--spec", required=True)
    s.add_argument("--force", action="store_true")
    s = sp("phase", cmd_phase)
    s.add_argument("value")
    s = sp("figma", cmd_figma)
    for f in ("channel", "file", "page"):
        s.add_argument(f"--{f}")
    s = sp("plan", cmd_plan)
    s.add_argument("kind")
    s.add_argument("key")
    s.add_argument("name")
    s.add_argument("--priority", default="P0", choices=list(PRIO))
    s = sp("plan-bulk", cmd_plan_bulk, help="đọc stdin: KEY|NAME|P0")
    s.add_argument("kind")
    for n, fn in (("begin", cmd_begin), ("node", cmd_node), ("done", cmd_done),
                  ("fail", cmd_fail), ("reset", cmd_reset)):
        s = sp(n, fn)
        s.add_argument("kind")
        s.add_argument("key")
        if n == "begin":
            s.add_argument("name")
        if n == "node":
            s.add_argument("node_id")
        if n == "done":
            s.add_argument("node_id", nargs="?")
            s.add_argument("--note")
        if n == "fail":
            s.add_argument("--note", required=True)
        if n == "reset":
            s.add_argument("--reason", required=True)
            s.add_argument("--forgive", action="store_true", help="đặt lại số lần thử về 0")
    s = sp("pause", cmd_pause)
    s.add_argument("--reason", required=True)
    s = sp("resume", cmd_resume)
    s.add_argument("--force", action="store_true")
    sp("next", cmd_next)
    s = sp("status", cmd_status)
    s.add_argument("--text", action="store_true")
    s = sp("ids", cmd_ids)
    s.add_argument("--status", default="done")
    sp("check-spec", cmd_check_spec)


    sp("migrate", cmd_migrate)
    for cmd, fn in (("intend", cmd_intend), ("inspect", cmd_inspect),
                    ("begin-update", cmd_begin_update)):
        s = sp(cmd, fn)
        s.add_argument("kind", choices=["screen"])
        s.add_argument("key")
        s.add_argument("--recipe", required=True)
        s.add_argument("--tokens", required=True)
        s.add_argument("--assets", required=True)
        if cmd == "begin-update":
            s.add_argument("--verified-live", action="store_true")
    s = sp("adopt", cmd_adopt)
    s.add_argument("kind", choices=["screen"])
    s.add_argument("key")
    s.add_argument("--recipe", required=True)
    s.add_argument("--tokens", required=True)
    s.add_argument("--assets", required=True)
    s.add_argument("--verified-live", action="store_true")
    s.add_argument("--visual", choices=["passed", "blocked", "skipped"], required=True)
    s = sp("done-update", cmd_done_update)
    s.add_argument("kind", choices=["screen"])
    s.add_argument("key")
    s = sp("bind", cmd_bind)
    s.add_argument("kind", choices=list(KINDS))
    s.add_argument("key")
    s.add_argument("semantic_id")
    s.add_argument("node_id")
    s.add_argument("--type", required=True)
    s.add_argument("--parent", required=True)
    s.add_argument("--verified", action="store_true")
    s = sp("qa", cmd_qa)
    s.add_argument("kind", choices=list(KINDS))
    s.add_argument("key")
    s.add_argument("--structural", choices=["passed", "failed", "blocked"], required=True)
    s.add_argument("--visual", choices=["passed", "failed", "blocked", "skipped"], required=True)
    s = sp("accept-spec", cmd_accept_spec)
    s.add_argument("--approved", action="store_true")
    s = sp("metrics", cmd_metrics)
    s.add_argument("kind", choices=list(KINDS))
    s.add_argument("key")
    for flag in ("calls", "failed", "batch", "reused"):
        s.add_argument("--" + flag, type=int, default=0)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
