# Figma Design Agent Only — Workflow v3.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây CLI Auto-Setup và workflow thiết kế Figma end-to-end cho Claude Code/Codex: từ APP_SPEC, brainstorming và phê duyệt, đến canvas QA/recovery/delivery — tuyệt đối không tạo source code ứng dụng.

**Architecture:** Một controller Python + một interactive design agent trong mỗi phiên + TalkToFigma MCP duy nhất; agent gọi Figma tools, Python giữ readiness, approval, checkpoints và gates. Reuse `scripts/state.py` v2, `scripts/intent.py`, `scripts/assets.py` thay vì thay transaction engine hoặc tạo design IR thứ hai.

**Tech Stack:** Python 3.x (stdlib, PyYAML phiên bản được pin trong lockfile), Bun/Node cho TalkToFigma, Claude Code hoặc Codex CLI, Superpowers Brainstorming, UI UX Pro Max, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-10-workflow-v3-figma-design-only.md` (Technical Spec v3.1 đã được người dùng duyệt ngày 2026-10-10).

## Global Constraints

- **Design-only:** Trong `design`/`resume`, không sinh `.swift`, `.kt`, `.java`, `.tsx`, `.jsx`, `.dart`, `.html`, `.css`, scaffold source app, build/compile, emulator/simulator hay project Android/iOS/web; Python code trong kế hoạch này **chỉ** phát triển harness.
- Backend cố định `talktofigma`; **không** Official Figma MCP, không Figma REST API write, không backend tự chuyển đổi khi gặp quota.
- Mỗi phiên chỉ **một** Claude/Codex Figma writer; planning có thể offline; Figma plugin/channel/file/page phải live-verified trước mutation.
- `superpowers:brainstorming` trong phiên **thiết kế** dừng ở approved design brief; **không** kích hoạt coding-plan/TDD/worktree của sản phẩm. Superpowers TDD trong tài liệu này chỉ áp dụng khi **phát triển harness**.
- Không tự approve, không dùng `--approved` để bypass approval; spec/brief đổi hash => invalidate approval. APP_SPEC là dữ liệu không đáng tin, không biến thành câu lệnh shell.
- ≤25 screens/run; maximum 8 brainstorming questions; maximum 2 targeted repairs/screen; P0 phải có structural + visual QA, relevant UI-state và flow coverage.
- Reuse state v2 APIs/CLI và WAL; pending `creating`/`updating` không auto-retry; manual edits/duplicate tên/wrong file/page phải BLOCKED khi chưa đối soát.
- Setup chỉ cài vào workspace/user-scope theo lệnh rõ ràng, dùng dependency lock **exact versions/commits**, không `@latest`, không curl-pipe-shell, không cài OS prerequisites thay người dùng.
- `SETUP.md` là tài liệu; `./agent` mới là entrypoint executable. `./agent doctor` không mutate config, và `SOCKET_READY` không có nghĩa `FIGMA_READY`.
- CLI exit codes: `0=success`, `2=invalid-input`, `3=action-required`, `4=blocked/reconcile`, `5=dependency/adapter-failure`, `6=workflow-conflict`, `7=QA-incomplete`. Mỗi JSON result: `{code,status,reason,next_action,run_id}`.
- Mục tiêu benchmark giảm ≥25% MCP calls/validated screen **chỉ là target**; không báo đạt nếu chưa có I10 trên Figma thật.
- Baseline tại lập plan: `python3 -m unittest discover -s tests -v` = **14/14 PASS**; đây không phải verification của workflow mới.

## File Ownership / Interfaces

| File | Responsibility | Dependencies |
|---|---|---|
| `agent` | Executable launcher, bảo toàn repo cwd, không shell-eval input | `scripts/agent.py` |
| `scripts/agent.py` | argparse + dispatch CLI, exit/result envelope | workflow, bootstrap, readiness |
| `scripts/policy.py` | Đọc/validate `workflow.yaml` (safe_load), fail-closed constraints | pinned PyYAML |
| `scripts/spec_input.py` | Normalize+validate APP_SPEC, assumptions, digest | stdlib |
| `scripts/workflow.py` | Durable workflow state, events, approvals, checkpoints | policy, spec_input; không ghi `STATE.json` trực tiếp |
| `scripts/writer_lock.py` | Exclusive process-lived writer lock theo target | stdlib/OS lock |
| `scripts/socket_supervisor.py` | Bun socket up/down/health/ownership | subprocess, pidfile |
| `scripts/readiness.py` | Typed checks, doctor, evidence freshness | adapters + supervisor |
| `scripts/runtime_adapters.py` | Claude/Codex detect, MCP register, skill smoke test, interactive launch | pinned CLI help; no duplicated MCP tools |
| `scripts/bootstrap.py` | Idempotent dependency/setup orchestration | lockfile, adapters, supervisor, readiness |
| `scripts/design_session.py` | Role + phase boot prompts, checkpoint contract, guardrails | workflow, adapters, state CLI |
| `scripts/design_qa.py` | P0 screens/states/flows QA + reports | workflow + read-only state v2 |
| `config/dependencies.lock.json` | Exact Git SHA/tag/package versions, install provenance | maintainer-validated pins |
| `workflow.yaml` | Configuration policy; only backend `talktofigma` | policy.py |
| `AGENTS.md`, `CLAUDE.md`, `SETUP.md`, `specs/APP_SPEC.template.md` | Runtime instructions, UX entrypoint, user documentation | full pipeline |
| `tests/test_*.py` | Mock/fake runtime unit/integration; separate labeled Figma-live suite | unittest |

**Cross-module typed contracts (freeze before implementation):**

```python
# Payloads are ordinary JSON-serializable dictionaries; specific fields validated below.
load_policy(path: Path) -> WorkflowPolicy
validate_spec(path: Path, workspace: Path) -> NormalizedSpec
WorkflowStore.begin(spec_path: str, runtime: str) -> dict
WorkflowStore.advance(event: str, evidence_path: Path | None = None) -> dict
WorkflowStore.resume() -> dict
WorkflowStore.status() -> dict
ApprovalGate.record(spec_sha256: str, brief_sha256: str, run_id: str, interaction_ref: str) -> dict
WriterLock.acquire(figma_target_id: str) -> ContextManager
SocketSupervisor.up() -> dict
SocketSupervisor.down() -> dict
ReadinessDoctor.check(runtime: str | None = None) -> dict
RuntimeAdapter.launch_interactive(prompt: str, cwd: Path) -> int
DesignSession.phase_prompt(phase: str, ctx: dict) -> str
DesignQA.evaluate(approved: dict, state_v2: dict, evidence: dict) -> dict
```

`interaction_ref` phải là tham chiếu của người dùng trong phiên tương tác, không được thay bằng chuỗi `auto`, `agent` hay sự tồn tại của file. Controller nhận evidence event qua internal `./agent checkpoint --event <event> --evidence <JSON-path>`; đây là contract trao đổi giữa agent và controller, không phải quyền bypass bất kỳ gate nào. Evidence có nguồn từ tool results + file evidence; text tự khai của LLM không thay cho xác minh live.

## Review Focus — five high-risk cases, each assigned to a test below

1. Setup lại khi MCP config có server khác và checkout TalkToFigma đã chỉnh sửa: bảo toàn user config/files, báo drift (Task 8).
2. Spec chứa prompt injection hoặc đường dẫn `../outside`: không execute, không ghi ngoài workspace (Task 2 / Task 10).
3. Approval cũ và concurrent run: không chuyển phase, không sinh run ID thứ hai hoặc writer thứ hai (Task 4 / Task 5 / Task 10).
4. Tool timeout sau create có thể Figma đã commit: resume bắt buộc live reconcile, không create duplicate (Task 11).
5. Visual QA pass nhưng P0 thiếu `error` state hoặc prototype unsupported: không `COMPLETED`, report nêu requirement chưa đạt (Task 12).

## Build/verification conventions

- Chạy lệnh từ thư mục project; `PYTHONPATH` project root khi cần; thêm `scripts/__init__.py` mà **không** sửa import `state.py` chỉ để đổi package.
- Mỗi task: viết failing test → chạy riêng nhìn **expected failure** → implement nhỏ nhất → chạy lại test và full `python3 -m unittest discover -s tests -v` → review diff → commit khi thực thi trong git checkout. ZIP hiện không chứa `.git`: **không tự `git init` hay tuyên bố đã commit**; lưu changeset/checkpoint nếu vẫn làm trong bản ZIP.
- Lệnh cho từng test ở dưới dùng `python3 -m unittest tests.<module>.<TestClass>.<method> -v`; thêm `tests/__init__.py` ở Task 1 để imports nhất quán.
- Test giả lập chỉ chứng minh local behavior; live Figma requirements phải qua I01–I12 và có log/proof riêng trước khi release.

---

### Task 1: CLI skeleton, policy validator & fixed backend

**Files:** Create `agent`, `scripts/__init__.py`, `scripts/agent.py`, `scripts/policy.py`, `workflow.yaml`, `tests/__init__.py`, `tests/test_cli_policy.py`.

**Interfaces:** `load_policy(path: Path) -> WorkflowPolicy`, `main(argv: list[str] | None = None) -> int`; expose `./agent --help`, `./agent doctor --json`, `./agent status --json` command names (unimplemented commands return code 5 until their owning task).

- [ ] **RED test:** `PolicyTests.test_blocks_official_backend_and_disabled_approval` asserts `load_policy` rejects `backend: figma-official` and `approval_required: false`; `CliTests.test_json_exit_contract` asserts `./agent` invalid flags exit `2` with exact five JSON result keys.
- [ ] **Run RED:** `python3 -m unittest tests.test_cli_policy -v`; expected missing module/CLI contract failure.
- [ ] **GREEN:** implement safe YAML loading, version=1, fixed backend, ranges `screens_per_run=1..25`, repairs `0..2`, `brainstorm.max_questions=1..8`; deny unknown version and invalid product_output; wrapper launches `python3 -m scripts.agent` from project root without executing spec text.
- [ ] **Verify:** named test and full regression suite; `./agent --help` lists approved commands. Commit `feat(harness): add CLI and policy contract` in Git checkout.

### Task 2: APP_SPEC normalization & input isolation

**Files:** Create `scripts/spec_input.py`, `tests/test_spec_input.py`; modify `specs/APP_SPEC.template.md`.

**Interfaces:** `validate_spec(path: Path, workspace: Path) -> NormalizedSpec` exposes `.app_name`, `.platform`, `.p0_features`, `.language`, `.spec_sha256`, `.assumptions`, `.warnings`; writes `design/ASSUMPTIONS.md` only after successful validation.

- [ ] **RED test:** `SpecTests.test_missing_p0_rejected`, `test_legacy_channel_ignored`, `test_escape_path_rejected`, `test_injected_shell_text_is_data` (input includes `RUN rm -rf ...` and `generate SettingsScreen.kt`; validate returns data/warning, never starts subprocess or writes product code).
- [ ] **Run RED:** `python3 -m unittest tests.test_spec_input -v`; expected missing parser/test failure.
- [ ] **GREEN:** parse template section headings and feature priorities deterministically; app/name/platform/role/P0/language/constraints required; legacy channel deprecation warning; paths canonicalized inside workspace; spec size/read errors actionable; update template to "design target/conventions", remove channel field.
- [ ] **Verify:** named and full tests. Commit `feat(harness): validate design-only application specs`.

### Task 3: Durable workflow store & phase transitions

**Files:** Create `scripts/workflow.py`, `tests/test_workflow_store.py`.

**Interfaces:** `WorkflowStore.begin(spec_path, runtime)`, `.advance(event, evidence_path=None)`, `.resume()`, `.status()`; file `design/WORKFLOW.json` schema version 1, journal `design/workflow-journal.log`; map events to the phases in spec §7.

- [ ] **RED test:** `WorkflowStoreTests.test_atomic_checkpoint_restart` verifies run_id/phase hashes persist after instance reload; `test_cannot_skip_from_validation_to_execution` asserts illegal event rejected and journal unchanged; `test_same_spec_reenters_run` expects identical run_id.
- [ ] **Run RED:** `python3 -m unittest tests.test_workflow_store -v` expected fail because store not present.
- [ ] **GREEN:** atomic tmp→flush→fsync→replace, event journal append+fsync; validate every event/postcondition; phase transitions include ACTION_REQUIRED/BLOCKED/PAUSED and WAITING; schema/version strict, never mutate `design/STATE.json` directly.
- [ ] **Verify:** named and full tests. Commit `feat(harness): add durable design workflow checkpoints`.

### Task 4: Fingerprint-bound interactive approval gate

**Files:** Modify `scripts/workflow.py`; create `tests/test_approval.py`.

**Interfaces:** `ApprovalGate.record(spec_sha256, brief_sha256, run_id, interaction_ref) -> dict`, `ApprovalGate.is_current(...) -> bool`; `WorkflowStore.advance("brainstorm_drafted", evidence_path)` + `"approved"` enforce both digests. Never expose a user-facing `--approved` shortcut in `./agent design`.

- [ ] **RED test:** `ApprovalTests.test_requires_user_interaction_reference`, `test_stale_spec_or_brief_invalidates_approval`, `test_revise_cannot_inherit_approval`; assert `approved_by="interactive_user"` and exact digests, no mutation permission on mismatch.
- [ ] **Run RED:** `python3 -m unittest tests.test_approval -v` expected missing gate failure.
- [ ] **GREEN:** persist approved record with run_id/timestamp/hash pair; require interactive agent event and non-agent interaction ref; revision triggers `AWAITING_CHANGE_APPROVAL`; only after gate call v2 `accept-spec --approved` through bridge from Task 11.
- [ ] **Verify:** named and full tests. Commit `feat(harness): bind approval to immutable design brief`.

### Task 5: Single-writer process lifetime lock

**Files:** Create `scripts/writer_lock.py`, `tests/test_writer_lock.py`.

**Interfaces:** `WriterLock.acquire(figma_target_id: str) -> ContextManager`, file `.agent/locks/figma-writer.lock`; metadata includes target ID hash, PID, process-start identity and run_id; lock lifetime encloses all Figma mutations, state operations take their own shorter lock inside.

- [ ] **RED test:** `WriterLockTests.test_second_process_blocked_even_when_state_file_free` uses a separate subprocess to contend; `test_crash_releases_os_lock_and_demands_reconcile` verifies acquisition after killed owner does not falsely clear WAL.
- [ ] **Run RED:** `python3 -m unittest tests.test_writer_lock -v` expected failure (no OS lock).
- [ ] **GREEN:** use POSIX advisory flock on macOS/Linux/WSL, explicitly fail unsupported OS rather than pretend locking; store identity metadata, no TTL-only stale unlock, no lock held while waiting for user approval; reject simultaneous writer across target IDs conservatively in one workspace.
- [ ] **Verify:** named and full tests. Commit `feat(harness): serialize Figma canvas writers`.

### Task 6: Socket supervisor, process ownership & liveness

**Files:** Create `scripts/socket_supervisor.py`, `tests/test_socket_supervisor.py`.

**Interfaces:** `SocketSupervisor.up() -> dict`, `.down() -> dict`, `.health() -> dict`; runtime files `.agent/runtime/socket.pid.json` and bounded/rotated logs; process command comes **only** from pinned checkout, `bun socket`.

- [ ] **RED test:** `SocketSupervisorTests.test_up_twice_uses_same_owned_process`, `test_down_does_not_kill_unowned_listener`, `test_dead_pid_restarts_only_owned_process`; fake socket CLI and loopback port as fixtures.
- [ ] **Run RED:** `python3 -m unittest tests.test_socket_supervisor -v` expected failure.
- [ ] **GREEN:** `Popen` with controlled argv/cwd, process start identity+pid, port/protocol probe, no shell=True; refuse port occupied by unknown service; bind loopback by default; WSL 0.0.0.0 only explicit opt-in with warning.
- [ ] **Verify:** named and full tests. Commit `feat(harness): supervise local TalkToFigma socket`.

### Task 7: Typed readiness checks & read-only doctor

**Files:** Create `scripts/readiness.py`, `tests/test_readiness.py`.

**Interfaces:** `ReadinessDoctor.check(runtime: str | None = None) -> dict`, machine checks per spec §5.2: `PREREQS_READY`, `AGENT_READY`, `SOCKET_READY`, `FIGMA_READY`, `CANVAS_READY`, `ACTION_REQUIRED` or `BLOCKED` with per-dimension evidence and freshness.

- [ ] **RED test:** `DoctorTests.test_socket_alive_plugin_absent_is_figma_not_verified`, `test_stale_agent_probe_does_not_mark_canvas_ready`, `test_doctor_does_not_change_mcp_config`.
- [ ] **Run RED:** `python3 -m unittest tests.test_readiness -v` expected failure.
- [ ] **GREEN:** independent check results and `next_action`; `FIGMA_READY` only active/recent session evidence from successful MCP join+document identity, `CANVAS_READY` only after permission probe; doctor outside live session reports `FIGMA_NOT_VERIFIED`; never installs software.
- [ ] **Verify:** named and full tests. Commit `feat(harness): implement readiness and doctor checks`.

### Task 8: Pinned Claude/Codex adapters & safe MCP registration

**Files:** Create `scripts/runtime_adapters.py`, `tests/test_runtime_adapters.py`, `config/dependencies.lock.json`; modify `.claude/settings.json` only if needed to align to pinned instructions (preserve existing hooks).

**Interfaces:** `ClaudeAdapter`/`CodexAdapter`: `detect_version()`, `register_mcp()`, `verify_skill()`, `launch_interactive(prompt,cwd)`, `diagnostics()`; both point to the same pinned TalkToFigma checkout. Record verified CLI help/version capability per adapter.

- [ ] **RED test:** `AdapterTests.test_registration_preserves_unrelated_mcp_servers`, `test_dirty_checkout_blocks_mutation`, `test_unknown_interactive_prompt_flag_fails_closed`, `test_second_registration_idempotent`; fixture existing config with other servers and backup path.
- [ ] **Run RED:** `python3 -m unittest tests.test_runtime_adapters -v` expected failure.
- [ ] **GREEN:** lock schema requires pinned full Git commit for TalkToFigma, Superpowers/UI UX install source+version and PyYAML exact package version; values must be resolved from **maintainer-verified checkout/release** and checked into lock, never guessed from a latest tag. Use respective CLI registration/config syntax verified against the pinned `--help`; backup+atomic update, no unrelated config removal. An unsupported CLI returns `ADAPTER_UNSUPPORTED` code 5.
- [ ] **Verify:** named/full tests and **manual adapter smoke tests** for both pinned runtime versions; document commands/output (do not claim verified until run). Commit `feat(harness): register pinned TalkToFigma on both runtimes`.

### Task 9: Idempotent setup orchestration & user-scope skill readiness

**Files:** Create `scripts/bootstrap.py`, `tests/test_bootstrap.py`; modify `scripts/agent.py` to dispatch `setup/up/down/doctor`.

**Interfaces:** `setup(runtime: Literal["codex", "claude", "both"]) -> dict`, `up()`, `down()`; CLI `./agent setup --runtime both`, `./agent doctor --json` with specified exit envelope. Bootstrap uses stdlib before venv/PyYAML is installed.

- [ ] **RED test:** `BootstrapTests.test_setup_twice_has_one_registration_and_socket`, `test_missing_bun_does_not_run_download_shell`, `test_skill_not_smoke_tested_reports_action_required`, `test_failed_setup_preserves_custom_config`.
- [ ] **Run RED:** `python3 -m unittest tests.test_bootstrap -v` expected failure.
- [ ] **GREEN:** preflight OS/CLI/Bun/Node/git/checkout, pinned workspace-local dependency install, register adapters, verify Superpowers and UI UX skill separately per runtime, smoke-test search.py, start/reuse socket, doctor; partial results and exact manual steps for user Figma plugin/login. On rerun no version drift or duplicated registrations.
- [ ] **Verify:** named and full tests, setup twice on disposable config fixture; no real user configs modified by tests. Commit `feat(harness): add safe idempotent bootstrap`.

### Task 10: Design session launch, safe prompt & design-only scope

**Files:** Create `scripts/design_session.py`, `tests/test_design_session.py`; modify `scripts/agent.py`, `AGENTS.md`, `CLAUDE.md`.

**Interfaces:** `DesignSession.phase_prompt(phase: str, ctx: dict) -> str`, `DesignSession.launch(spec_path: Path, runtime: str) -> int`; CLI `./agent design <spec> --runtime codex|claude`, `./agent resume [--runtime ...]`.

- [ ] **RED test:** `DesignSessionTests.test_prompt_routes_to_brainstorm_not_coding`, `test_app_spec_injection_cannot_become_process_argv`, `test_relaunch_same_run_id`, `test_unverified_cli_launch_blocks_before_any_canvas_mutation`.
- [ ] **Run RED:** `python3 -m unittest tests.test_design_session -v` expected failure.
- [ ] **GREEN:** construct system/initial prompt in role→hard constraints→phase process→Figma output→one design-only example; spec text passed as labeled untrusted input/path, never shell command; interactive CLI launch only with tested adapter mechanism; no automatic brief approval; selected runtime only. Assert no coding skills in product-design phase and no source scaffolding commands initiated by harness.
- [ ] **Verify:** named/full tests plus manual interactive smoke test per adapter; commit `feat(harness): launch interactive design-only sessions`.

### Task 11: Phase controller ↔ state v2 bridge and safe Figma reconciliation

**Files:** Modify `scripts/workflow.py`, `scripts/design_session.py`, `scripts/agent.py`; create `scripts/state_bridge.py`, `tests/test_state_bridge.py`, `tests/test_resume_chaos.py`.

**Interfaces:** `StateBridge.plan_screens(plan_path: Path) -> dict`, `.inspect_screen(recipe: Path, tokens: Path, assets: Path) -> dict`, `.require_reconcile() -> list[dict]`, `.commit_qa(screen_id: str, evidence_path: Path) -> dict`; `./agent checkpoint --event ... --evidence <path>` validates phase events; only bridge calls existing `state.py` via subprocess (no edits to v2 format).

- [ ] **RED test:** `StateBridgeTests.test_never_replay_create_when_open_wal`, `test_live_fingerprint_required_before_mutation`, `test_calls_existing_inspect_instead_of_parallel_diff`, `ResumeChaosTests.test_timeout_after_create_requires_reconcile` and `test_wrong_file_or_duplicate_name_blocks`.
- [ ] **Run RED:** `python3 -m unittest tests.test_state_bridge tests.test_resume_chaos -v` expected failure.
- [ ] **GREEN:** after approved brainstorm, automatically enter design planning → design system → Figma connection → execution → QA → delivery via phase prompts/checkpoint evidence; screen order P0/P1/P2, `plan(-bulk)` / `inspect` / `begin-update --verified-live` / `qa` / `done(-update)` delegated through v2. On open WAL, create explicit reconcile instruction requiring tool `get_nodes_info`/document identity; **never** call `state.py resume --force` or retry unknown mutation.
- [ ] **Verify:** named/full tests; manually inspect phase prompts for exact TalkToFigma tool names available in pinned checkout. Commit `feat(harness): wire design workflow to v2 WAL safely`.

### Task 12: Design completeness, QA gate & Figma-only delivery report

**Files:** Create `scripts/design_qa.py`, `tests/test_design_qa.py`; modify `scripts/workflow.py` for QA/DELIVERY transitions.

**Interfaces:** `DesignQA.evaluate(approved: dict, state_v2: dict, evidence: dict) -> dict`; `DesignQA.report(...)` writes `design/DESIGN_REPORT.md`, `design/WORKFLOW_REPORT.json`; JSON includes `p0_completion`, `p0_state_coverage`, `p0_flow_coverage`, `prototype_status`, `product_code_files_generated`, `product_build_commands_invoked`.

- [ ] **RED test:** `DesignQATests.test_p0_missing_error_state_blocks`, `test_structural_pass_visual_fail_blocks`, `test_unresolved_wal_blocks_completed`, `test_prototype_unsupported_is_reported_not_claimed`, `test_design_only_generated_product_file_blocks_delivery`.
- [ ] **Run RED:** `python3 -m unittest tests.test_design_qa -v` expected failure.
- [ ] **GREEN:** require 100% verified approved P0 screens, applicable required UI states and documented flow edges; explicit N/A rationale for inapplicable states; structural+visual screenshot/inspection refs; two repair attempts, report placeholders, limitations, missing P1/P2, target file/page IDs, tool metrics and prototype support. Count **new** product source files since run start; build-command count only `0` when audit evidence genuinely covers executed commands, otherwise `unverified` and block unqualified release claim.
- [ ] **Verify:** named/full tests. Commit `feat(harness): enforce P0 QA and Figma-only delivery`.

### Task 13: End-to-end CLI & chaos fixtures, operator docs

**Files:** Create `tests/test_agent_e2e.py`, `tests/fixtures/` fake CLI/socket/plugin evidence, `evals/WORKFLOW_V3.md`; modify `SETUP.md`, `AGENTS.md`, `CLAUDE.md`, `evals/CHAOS.md`; optionally add `.gitignore` for `.agent/runtime/`, `.agent/locks/`, local secrets/cache.

**Interfaces:** full flow `setup → design → wait approval → approve → offline artifacts → wait Figma → verified mutation → QA → delivery`; `status --json`, `retry --phase figma-execution` only after blocked/retryable current gate; only pinned TalkToFigma backend.

- [ ] **RED test:** `AgentE2ETests.test_full_flow_stops_at_approval_and_plugin_gate`, `test_retry_refuses_stale_approval`, `test_two_runtimes_do_not_write_same_canvas`, `test_design_never_creates_app_source` (fake runtime logs all commands), plus `test_spec_limited_to_25_screens`.
- [ ] **Run RED:** `python3 -m unittest tests.test_agent_e2e -v` expected failure.
- [ ] **GREEN:** finish integration glue only; document `./agent setup --runtime both`, `doctor`, `design`, approval, plugin join, `resume`, `up/down`, exact `ACTION_REQUIRED` remediations, rollback/config backup, security boundaries. No instruction to paste channel ID into APP_SPEC, no `@latest` instruction or claim Markdown itself executes.
- [ ] **Verify:** `python3 -m unittest discover -s tests -v` with all legacy tests green; run `./agent doctor --json` and `./agent status --json` without live plugin and verify fail-closed; commit `test(harness): cover auto-design workflow and recovery`.

### Task 14: Live Figma acceptance & measured benchmark (release gate, not mock)

**Files:** Create `evals/LIVE_RESULTS.md`, `design/qa/` evidence produced **only during real tests**; update `evals/WORKFLOW_V3.md` with results and regressions. No source code application output.

**Interfaces:** I01–I12 from spec §11.2, live Claude and Codex adapter probes, exact Figma target identity, controlled baseline/reference snapshot.

- [ ] **Prepare:** validate developer/user machine has pinned CLIs+skills, a disposable Figma file with plugin joined, permission probe, and backups; select **one runtime writer at a time**.
- [ ] **Execute:** I01–I12 with saved evidence; inject safe crash/timeout only on disposable Figma file; verify zero duplicated roots after reconcile, no wrong-file changes and 100% P0 required states/flows.
- [ ] **Benchmark:** identical spec/model/file snapshot, 3 runs baseline Option A and 3 runs v3.1; measure median `mcp_calls / validated_P0_screen`, setup readiness latency and number of manual phase prompts. Report variance and both absolute numbers; ≥25% is target, not automatic PASS.
- [ ] **Verify release:** repeat full local test suite, review artifact inventory (no app source), inspect coverage report, document any missing or unsupported capabilities. `G5_EndToEnd` can be **PASS** only on recorded live evidence; otherwise `NOT_VERIFIED`, never `PASS` from fake unit tests. Commit measured results if in a Git checkout.

---

## Dependency ordering / execution checkpoints

| Milestone | Tasks | Independently reviewable output |
|---|---|---|
| M1: CLI & Spec Contracts | 1–2 | Strict policy, safe APP_SPEC validator |
| M2: Workflow State & Approval | 3–5 | Restartable state + consent + writer isolation |
| M3: Runtime Auto-Setup | 6–9 | Socket + doctor + pinned adapters + idempotent setup |
| M4: Auto Design | 10–11 | Interactive brainstorm approval → automatic Figma-phase prompts + WAL bridge |
| M5: QA & Release | 12–14 | Coverage gate + reports + full chaos/live acceptance |

For every task, reviewer validates (a) no app-code output, (b) one writer/backend, (c) tests really failed RED then passed GREEN, (d) legacy 14 remain green, (e) exact input/output contract retained. When a task has no Git checkout, record test logs and ZIP diff instead of claiming commit.

## Explicit interface and evidence caveats

- **Live capabilities:** tool names, CLI launch syntax, MCP registration syntax and interactive prompt injection mechanism must be checked against the **pinned** runtime and TalkToFigma tool schema before enabling mutation; test doubles must never substitute for live acceptance.
- **Approval provenance:** local agent events are audit controls, not cryptographic proof of a user's identity. Future stronger attestation may require host support; don't imply this exists.
- **OS lock scope:** local workspace process lock is not cross-machine/distributed locking. Do not claim protection against writers in another workspace/machine.
- **Application-code guard:** prompt restrictions and artifact scanning alone do not constitute an OS sandbox. Report `build_commands_invoked=unverified` absent reliable command audit; do not assert hard prevention beyond evidence.
- **Prototype:** unsupported TalkToFigma prototype linking remains explicit unmet requirement rather than fabricated interactive links.

## Plan self-review (2026-10-10)

- Spec §0–15 mapped: Task 1 policy, Task 2 input, Tasks 3–5 orchestration/approval/locks, Tasks 6–9 bootstrap/runtime, Tasks 10–11 design-only lifecycle/incremental, Task 12 QA/delivery, Tasks 13–14 verification/docs/benchmark.
- Review Focus 1–5 mapped to named tests in Tasks 8, 2/10, 4/5/10, 11, 12.
- No new design IR or application-source tasks; existing `state.py` v2 / `intent.py` continue as source of truth.
- Tests enumerated are **to be implemented**. Only the pre-existing 14 baseline unit tests have been executed while creating this plan.

## Execution handoff

**Recommended:** Native execution (`superpowers:executing-plans`) in a Git checkout, with a strong independent reviewer after M2/M4/M5. Tasks share a single evolving workflow state interface, so per-task subagent handoffs have extra coordination cost. For maximum independent scrutiny, `superpowers:subagent-driven-development` remains available with one implementer/reviewer per task.

**Do not begin implementing until the user reviews this plan and chooses the execution method.**
