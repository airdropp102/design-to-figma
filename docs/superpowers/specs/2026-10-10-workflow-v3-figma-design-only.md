# Technical Design Spec v3.1 — Figma Design Agent Only (Auto-Setup & Auto-Design)

- **Status:** APPROVED — Technical Spec v3.1 được người dùng duyệt ngày 2026-10-10; chưa triển khai implementation.
- **Ngày:** 2026-10-10
- **Baseline:** `figma-design-agent-option-A-optimized.zip` (Option A / TalkToFigma-only)
- **Phạm vi:** bootstrap môi trường, skill readiness, vòng đời runtime, brainstorm yêu cầu thiết kế, tạo UI/UX **trực tiếp trên Figma**, approvals, checkpoint, recovery và visual QA. **Không tạo mã nguồn ứng dụng.**
- **Nền tảng:** Codex CLI và Claude Code; mỗi lần thiết kế chọn **một** runtime để ghi Figma. MCP là lớp tool dùng chung.
- **Quyết định đã duyệt:** giữ **TalkToFigma duy nhất**; không Official Figma MCP, không fallback sang Official, không dùng Figma REST API để mutate canvas.

## 0. Quy ước phạm vi bắt buộc — Design Only (normative)

**Product-design runtime ≠ software-development agent.** Trong phiên `./agent design ...`, vai trò agent là **Product Designer / UI-UX Designer sử dụng Figma**, không phải frontend, Android/iOS engineer hay code-generation agent.

**Đầu vào hợp lệ:** `APP_SPEC.md` chứa yêu cầu sản phẩm, người dùng, business flows, ưu tiên P0/P1/P2, visual references, dữ liệu mẫu, platform design target (iOS/Android/web), asset và yêu cầu accessibility. Trường “stack công nghệ” nếu xuất hiện ở spec cũ chỉ là **ngữ cảnh convention của thiết kế**, không phải yêu cầu generate code.

**Đầu ra bắt buộc:** node/frame thực trên đúng Figma file/page; design system (màu, typography, spacing, radius); reusable Figma components khả thi với tool hiện có; danh sách screens, flows, các UI states đã duyệt, QA evidence và `DESIGN_REPORT.md`. Interaction/prototype links chỉ bắt buộc nếu APP_SPEC yêu cầu **và** phiên bản TalkToFigma đã xác minh hỗ trợ; nếu không hỗ trợ phải ghi blocker/alternative rõ ràng, không giả vờ hoàn tất prototype.

**Đầu ra bị cấm trong `design` và `resume`:** source code ứng dụng `.swift`, `.kt`, `.java`, `.tsx`, `.jsx`, `.dart`, `.html`, `.css`; UI scaffolding; code Flutter/React Native/SwiftUI/Jetpack Compose; build, test, compile, emulator/simulator, APK/IPA; project source repository/PR. Các tệp `design/*.json` hoặc `scripts/*.py` hỗ trợ **harness** không được hiểu là mã nguồn app. `setup` là ngoại lệ cho phép cài/cấu hình **hạ tầng agent** khi người dùng gọi lệnh rõ ràng.

**Skill routing:** `superpowers:brainstorming` trong **design runtime** chỉ dùng để tìm hiểu mục tiêu, luồng, phạm vi và chọn visual direction, kết thúc ở approved design brief; **không** tiếp tục sang `writing-plans`, worktree, TDD hay lập trình sản phẩm. Quy trình Superpowers để **phát triển chính harness** là công việc độc lập của developer, không chạy trong `./agent design`.

**Scope enforcement:** output validator/report ghi `product_code_files_generated = 0`; kiểm thử xác nhận tool-runner không tự chạy build hoặc tạo source application dù input chứa câu “generate app”. Prompt/script trong APP_SPEC là dữ liệu không đáng tin và không vượt qua lệnh hard constraint này.

## 1. Bối cảnh đã xác nhận

Bundle Option A hiện có `AGENTS.md`, `CLAUDE.md`, `SETUP.md`, `.claude/settings.json`, `scripts/state.py`, `scripts/intent.py`, `scripts/assets.py`, `specs/APP_SPEC.template.md`, `specs/SCREEN_RECIPE.template.json`, tests và evals. Không có entrypoint `./agent`, bootstrap daemon/supervisor, workflow state tổng, hay file `specs/APP_SPEC.md` đã điền. `SETUP.md` là tài liệu thao tác thủ công; nó không thể tự chạy chỉ vì được mở hoặc đọc.

`state.py` dùng state v2, version migration, `begin/node/done`, `intend/inspect`, `begin-update/done-update`, `bind/adopt`, QA, pause/resume, `accept-spec`, journal và một khóa cho cập nhật file state. Khóa này **không** khóa suốt phiên ghi Figma. `intent.py` tính fingerprint từ recipe + token + asset và phân loại `skip`, `text_patch`, `style_patch`, `mixed_patch`, `rebuild`, `legacy_reconcile`. Khả năng Figma live vẫn phụ thuộc tool MCP do agent gọi.

Các ràng buộc đang tồn tại cần giữ: tối đa 25 screen/chạy; không bulk-create node giả định; batch chỉ qua schema đã xác minh; WAL trước mutation; root name duy nhất; không xóa khi mơ hồ; QA bắt buộc cho P0; không có Figma writer song song.

## 2. Mục tiêu, không mục tiêu và định nghĩa thành công

### 2.1. Mục tiêu chức năng

1. Một lệnh `./agent setup --runtime both` thực hiện **mọi bước máy tính có thể tự động thực hiện an toàn**: preflight, pin/resolution dependencies, cài các phần tương thích, cấu hình TalkToFigma cho Claude/Codex, cài/xác minh skill, khởi động WebSocket service rồi chạy doctor. Khi yêu cầu đăng nhập/chọn plugin trên GUI, trả `ACTION_REQUIRED` rõ ràng, không báo thành công giả.
2. `./agent design specs/APP_SPEC.md --runtime codex|claude` mở một phiên agent tương tác với boot prompt cố định, validate spec, chạy `superpowers:brainstorming`, thu approval, rồi tự điều phối Pha 1–5 đến khi QA và delivery, hoặc gặp blocker.
3. `./agent resume` phục hồi cả workflow và Figma operations, không nhân đôi node sau timeout/crash.
4. `./agent doctor`, `status`, `up`, `down` có output người đọc được và `--json` để CI/automation sử dụng.
5. Thay đổi APP_SPEC hoặc design brief đã duyệt tạo review gate; incremental update dựa trên `intent.py` và state v2 thay vì rebuild toàn bộ.
6. Kết thúc bằng **Figma design deliverables**, không source code. Report phải đối chiếu P0 user flows, screen + state coverage, design tokens, reusable components và các prototype links được yêu cầu.

### 2.2. Không mục tiêu

- Không cài Bun/Node/Python hệ thống bằng script download-pipe-to-shell, không tự cài Figma Desktop hoặc tự click plugin trên UI.
- Không tích hợp Official Figma MCP, Figma Variables API hay Figma REST API write.
- Không tạo full design IR mới, graph of specialized agents, queue phân tán, hoặc server ứng dụng riêng.
- **Không viết hay build ứng dụng**: Swift, SwiftUI, Kotlin, Jetpack Compose, Flutter, React Native, JavaScript/TypeScript UI, HTML/CSS, iOS/Android project hoặc backend. Không tạo production code, source handoff hay commit cho app.
- Không tự đồng nhất việc có “native design conventions” (iOS/Android Material/HIG) với việc viết mã nguồn native.
- Không giả định bất kỳ CLI nào có stable flag truyền prompt/interactive mode mà chưa kiểm tra trên phiên bản được pin.
- Không tuyên bố tự kiểm tra được canvas khi chưa có tool session của agent và plugin/channel hoạt động.
- Không tự động duyệt brainstorm, thay đổi spec, hoặc ghi đè manual edits trong Figma.

### 2.3. Thành công đo được

- Setup chạy lại không tạo MCP registration trùng, skill trùng hay socket trùng (`idempotent setup: 100%` trong bộ integration test).
- Tất cả prerequisite machine-readable về runtime/skills/MCP/WebSocket được kiểm tra (tỷ lệ **100%** với các check bắt buộc), thiếu thì state fail/blocked rõ.
- Từ sau approval đến delivery **0 prompt điều khiển phase thủ công** trong happy path, trừ bước bắt buộc để người dùng join Figma plugin/channel.
- Chaos resume: 0 duplicate root frame, 0 mutation sai node; 100% kịch bản test định nghĩa tại §13 đạt.
- 100% màn P0 `done` có structural + visual QA passed **và đã đánh dấu kiểm thử đủ các UI states bắt buộc**; workflow `COMPLETED` không còn transaction chưa reconcile.
- `product_code_files_generated = 0` và `product_build_commands_invoked = 0` trong toàn bộ workflow design; không có artifact nguồn ứng dụng.
- MCP calls/màn đạt QA giảm **mục tiêu** ≥25% so Option A baseline khi benchmark trên Figma thật; không hứa trước kết quả.

## 3. Kiến trúc tối giản và phân ranh nhiệm vụ

```text
User
  │
  ├─ ./agent setup/doctor/up/down ─► Bootstrap/Runtime Supervisor
  │                                    ├─ dependency + skill checks
  │                                    ├─ MCP registration (Claude/Codex)
  │                                    └─ bun socket lifecycle
  │
  └─ ./agent design/resume ─────────► Design-only Workflow Controller
                                       │    (phase state + approval gates)
                           ┌───────────▼────────────┐
                           │ Interactive Agent      │
                           │ Claude Code OR Codex   │
                           │ Superpowers + UI UX    │
                           └───────────┬────────────┘
                                       │ MCP stdio, single writer
                           ┌───────────▼────────────┐
                           │ TalkToFigma MCP        │
                           │ bun socket + plugin    │
                           └───────────┬────────────┘
                                       ▼
                           Figma Canvas (screens / components / states)
                                       │
                       ┌───────────────▼────────────────┐
                       │ state.py v2 + intent.py + QA   │
                       │ WORKFLOW.json + audit journal  │
                       └────────────────────────────────┘
```

**Một process controller và một interactive agent thiết kế Figma**, không thêm design-specialist agent bắt buộc. Workflow Controller kiểm soát bước bằng trạng thái file và gate; **agent** mới là thành phần reasoning và gọi TalkToFigma MCP, không phải Python script giả làm MCP. `scripts/state.py` tiếp tục sở hữu transaction Figma; workflow controller không mutate `STATE.json` trực tiếp.

**Five-subsystem mapping:** Instructions (`AGENTS.md/CLAUDE.md`), Tools (TalkToFigma MCP + CLI), Orchestration (`agent`, `workflow.py`), State/Memory (`WORKFLOW.json` + `STATE.json`), Guardrails/Evals (`readiness`, approval, QA, chaos). Toàn bộ MCP dùng chung giữa hai runtime; adapter runtime chỉ xử lý cách khởi động CLI và skill discovery, không duplicate MCP tools.

## 4. Giao diện CLI và semantics

Các lệnh sau là **contract v3 cần implement**, chưa tồn tại trong bundle Option A.

```bash
./agent setup --runtime both        # chủ động setup cả hai runtime, sau đó start WebSocket
./agent setup --runtime claude      # chỉ một runtime
./agent doctor [--json]             # read-only checks; không tự cài gì
./agent up                          # start/reuse local TalkToFigma websocket
./agent down                        # stop tiến trình do harness quản lý
./agent status [--json]             # workflow + state.py v2 + runtime
./agent design specs/APP_SPEC.md --runtime codex
./agent design specs/APP_SPEC.md --runtime claude
./agent resume [--runtime codex|claude]
./agent retry --phase figma-execution
```

- `setup` là lệnh **được người dùng chủ động gọi để cho phép cài dependency vào workspace/user scope**; không tự động cài prerequisite OS (Bun, Node, Python, CLI agent) khi thiếu. Có cảnh báo trước khi thay đổi config MCP ngoài workspace và có cơ chế backup/restore.
- `up` quản lý chỉ socket server TalkToFigma: pidfile, start command, port-health, ownership token/process check, process group, log rotation. `down` chỉ kill process của harness, không đóng các phiên agent/Figma không do harness tạo.
- MCP stdio được CLI agent khởi chạy theo phiên qua registration. Không cố chạy một daemon MCP stdio chung cho cả Claude/Codex.
- `design` kiểm tra runtime và spec path; nếu không có active workflow, tạo run ID. Nếu đang có run cùng workspace/spec, thực hiện `resume` chứ không tạo run mới. Runtime Claude hoặc Codex được chọn rõ, **không chạy hai writer**.
- `design` khởi chạy interactive agent bằng adapter đã smoke-test cho phiên bản CLI pin; adapter đưa đường dẫn `AGENTS.md` và phase hiện tại vào prompt đầu phiên. Nếu bản CLI không hỗ trợ interactive bootstrap một cách đáng tin cậy, trả `ADAPTER_UNSUPPORTED` và hướng dẫn một lệnh thay thế; không đánh dấu RUNNING.
- `resume` phục hồi **từ checkpoint**; không tự động `state.py resume --force`. Trường hợp transaction mở phải reconcile qua Figma trước.
- `retry` chỉ dùng cho phase **blocked/retryable**, phải kiểm tra fingerprint/phê duyệt không thay đổi; không retry mutation mù quáng.

CLI exit codes (khác với `state.py`, chỉ áp dụng cho `./agent`): `0=success`, `2=invalid-input`, `3=action-required`, `4=blocked/reconcile`, `5=dependency/adapter-failure`, `6=workflow-conflict`, `7=QA-incomplete`. Khi in JSON luôn có `{code, status, reason, next_action, run_id}`; exit code 3 khi cần người dùng thao tác plugin vẫn là kết quả setup một phần, không phải thành công trọn vẹn.

## 5. Setup + Readiness + quản lý runtime

### 5.1. Setup steps (idempotent)

1. Kiểm tra OS (macOS/Linux/WSL), quyền ghi workspace, Python, Bun, Node, `git`, `claude`/`codex` theo `--runtime`; fail rõ phiên bản không tương thích.
2. Kiểm tra lockfile config `config/dependencies.lock.json` chứa nguồn + exact tag/commit/version của TalkToFigma, UI UX Pro Max và phương thức cài Superpowers. Khi thiếu lock hợp lệ: fail **không** dùng `@latest` để cài tự phát.
3. Clone/sync TalkToFigma ở workspace-managed directory theo pinned revision; xác minh revision, chạy setup theo chính checkout đó (không dùng một phiên bản khác từ `bunx @latest`). Nếu folder local có sửa đổi chưa commit: không reset/mất dữ liệu; báo conflict.
4. Bổ sung MCP registration cho runtime đã chọn trỏ tới cùng phiên bản pinned local; phát hiện cấu hình hiện có, không duplicate; backup trước khi sửa, không xóa config khác. Claude/Codex sử dụng cơ chế registration riêng nhưng cùng TalkToFigma server/schema.
5. Cài/xác minh `ui-ux-pro-max` cho từng runtime (`.claude/skills` và `.agents/skills`) theo phiên bản pin, chạy `search.py ... --design-system` smoke-test với dữ liệu test cục bộ.
6. Cài/xác minh skill `superpowers:brainstorming` và cách gọi từ CLI. Nếu cần tương tác với marketplace/plugin installation hoặc permissions của người dùng, ghi `ACTION_REQUIRED`; tuyệt đối không đánh dấu READY khi chưa smoke-test được.
7. Khởi động hoặc reuse duy nhất một socket server, healthcheck liveness qua port/protocol; ghi thông tin process vào `.agent/runtime/`.
8. Chạy `doctor`, ghi `.agent/runtime/health.json` có TTL và metadata; không xem cached success là live success.

Các bước độc lập nên tiếp tục nếu một skill yêu cầu thao tác GUI: ví dụ vẫn có thể khởi động socket mặc dù Superpowers đang `ACTION_REQUIRED`; cuối `setup` báo **partial readiness** và các việc cần user xử lý. Chỉ dừng thao tác phụ thuộc một prerequisite đã thất bại. Mặc định socket bind loopback; mở interface mạng (`0.0.0.0` cho WSL hoặc remote) cần opt-in, cảnh báo exposure và giới hạn firewall. Không ghi auth token, chat text hay screenshot chứa dữ liệu nhạy cảm vào logfile bootstrap.

Một máy chỉ cài **runtime được chọn**; `both` xác minh cả hai. Khi re-run `setup` chỉ sửa phần sai/thiếu, không nâng version ngoài lockfile.

### 5.2. Readiness state

| Trạng thái | Bằng chứng cần có | Có thể làm gì |
|---|---|---|
| `PREREQS_READY` | OS/binary/version verified | Cài config/skills |
| `AGENT_READY` | CLI selected + skills + MCP registration smoke-test | Brainstorm, plan offline |
| `SOCKET_READY` | Bun socket tồn tại, responsive | Chờ plugin |
| `FIGMA_READY` | Agent MCP `join_channel` thành công + `get_document_info` xác thực đúng file/page | Đọc Figma, prepare mutation |
| `CANVAS_READY` | `FIGMA_READY` + write permission đã xác thực bằng safe capability probe hoặc bước đầu có rollback | Ghi canvas |
| `ACTION_REQUIRED` | Cần user thao tác login/install plugin/join channel | Dừng ở gate liên quan |
| `BLOCKED` | Thiếu prereq/broken config/không chắc trạng thái mutation | Không được tiếp tục mutate |

Readiness theo **các dimension**, không ghi mỗi boolean `ready=true`. `SOCKET_READY` **không** suy ra `FIGMA_READY`. CLI `doctor` bên ngoài phiên agent chỉ báo `FIGMA_NOT_VERIFIED` trừ khi có active agent probe còn tươi; không tự suy luận từ port hay channel trong cache.

**Thời hạn freshness:** `AGENT_READY` tái kiểm tra khi `design` bắt đầu; `FIGMA_READY` kiểm tra mỗi lần kết nối lại hoặc chuyển file/page; trước nhóm mutation đầu tiên của một screen luôn kiểm tra file identity. Cache health không thay thế live MCP checks.

### 5.3. Runtime/skill adapter

`ClaudeAdapter` và `CodexAdapter` chỉ đảm nhiệm `detect_version`, `register_mcp`, `verify_skill`, `launch_interactive`, `diagnostics`. Mỗi adapter có integration test trên CLI version pin; cờ/syntax cụ thể chỉ được đóng băng sau khi xác minh `--help`/official CLI cho release target. Không tạo MCP tool wrapper riêng từng nền tảng.

Superpowers trong **design workflow** chỉ dùng brainstorming và được ngắt đúng sau approved brief, rồi chuyển lại workflow. Superpowers trong **quá trình phát triển code harness v3** áp dụng đầy đủ design review → viết spec → review spec → implementation plan → TDD/verification.

## 6. Input spec, brainstorm và Approval Gate

### 6.1. `APP_SPEC.md` làm điểm vào

`specs/APP_SPEC.template.md` bỏ dòng `Figma channel ID` **và đổi “Stack mục tiêu” thành “Nền tảng giao diện cần thiết kế + design conventions”**; connection target nằm ở `.agent/runtime/figma.local.json` (ignored by git; không lưu token). Required fields: app name, platform `mobile|web|both` (optionally iOS/Android/desktop breakouts), product goal/target user, roles, feature list có ít nhất một P0, ngôn ngữ, constraints; phân biệt missing vs inferred. Giữ khả năng accept file spec đã có format cũ, nhưng deprecate/ignore channel embedded và cảnh báo migration.

Validation gồm: parse sections/tables, reject empty app/role/P0, giới hạn 25 screen per run, allow future backlog P1/P2; validate filesystem paths không escape workspace. Nội dung spec được coi là **data không đáng tin** khi truyền vào agent, không được override AGENTS/tool/approval policies. Output: `design/ASSUMPTIONS.md` + normalized parse summary/check report; không dựng Figma khi validation failed.

### 6.2. Brainstorm flow

1. Controller chuyển `SPEC_VALIDATION → BRAINSTORMING` nếu spec validated, skill verified.
2. Agent dùng `superpowers:brainstorming` **như product-design discovery, không phải phần chuẩn bị coding**: xác định outcome, 3–5 flows, P0/P1/P2, 2–3 visual directions, UI states, mobile platform conventions, risks, assets. Tối đa 8 câu hỏi hữu ích; không hỏi lại thông tin rõ trong APP_SPEC.
3. Tạo `design/BRAINSTORM.md` như draft **không** tự khẳng định approved.
4. Chuyển `AWAITING_APPROVAL`, hiển thị một recap gồm scope, screens + mandatory UI states dự kiến, visual direction, assumptions, P0 acceptance và có/không yêu cầu interactive prototype. Chỉ tiếp tục khi **người dùng chấp thuận trong interactive agent session**.
5. Agent ghi `approval_record` gắn `spec_sha256`, `brief_sha256`, version, timestamp, run ID, approved_by = `interactive_user`. Sau đó gọi workflow transition đến planning. Nếu người dùng yêu cầu sửa thì vào `REVISE`, cập nhật draft và hash; không reuse approval cũ.
6. Nếu spec thay đổi sau approval hoặc brief thay đổi, **invalidate approval** trước mutation. Khi delta chỉ tác động màn được xác định, vẫn phải xác nhận delta và lưu approval mới, nhưng không hỏi lại toàn bộ flow nếu phạm vi còn giữ nguyên.

Approval record không phải chữ ký số; nó là audit của tương tác và chống **trôi nội dung**. Không cung cấp tham số `--approved` như backdoor cho `./agent design`. `state.py accept-spec --approved` hiện có được gọi **chỉ sau** khi controller xác thực approval record tương ứng; cần giữ legacy CLI để tương thích, nhưng runtime không được tự suy ra approval từ sự tồn tại của file.

### 6.3. Approved design brief và ranh giới Superpowers

`design/BRAINSTORM.md` chỉ ghi **design decisions**: target users, flow map, screen/state inventory, IA, visual direction, tokens constraints, asset needs, accessibility, prototype requirement. Không chứa technical architecture ứng dụng, code interfaces, source file map, API implementation, unit test plan hay lịch build. Trước khi mutate canvas, controller xác minh approval digest gắn đúng APP_SPEC và brief. Sau approval, **phase tiếp theo là `DESIGN_PLANNING` → tạo Figma**, không phải tạo implementation plan mã nguồn ứng dụng.

### 6.4. Không giám sát / người dùng offline

Không tự approve brainstorm. Nếu user chưa hiện diện, controller `AWAITING_APPROVAL` và dừng; `resume` mở lại interactive prompt. Không sử dụng cơ chế bỏ brainstorm rồi tự tạo assumptions như nhánh cũ khi mục tiêu là automatic design v3, trừ khi `workflow.yaml` được người dùng thay đổi để chỉ cho phép dry-run planning (không mutate canvas).

## 7. Workflow State Machine

Trạng thái v3 độc lập với `state.py` PHASES `0,0.5,1,1.5,2,3,4,5,done`. Chỉ tạo một controller mapping sang các phase v2 có sẵn; không thêm trực tiếp trạng thái mới vào `state.py` nếu không có migration/test.

```text
NOT_STARTED → ENVIRONMENT_CHECK → SPEC_VALIDATION → BRAINSTORMING
    → AWAITING_APPROVAL ───► REVISE ──► AWAITING_APPROVAL
    → DESIGN_PLANNING → DESIGN_SYSTEM_READY → FIGMA_CONNECTION_GATE
    → DESIGN_EXECUTION → QUALITY_ASSURANCE → DELIVERY → COMPLETED

Any phase → BLOCKED / ACTION_REQUIRED / PAUSED
RESUME → validate fingerprints + reconcile open transactions → previous phase
QA failed → TARGETED_REPAIR (max 2 attempts per screen) → QUALITY_ASSURANCE
```

- Chuyển phase chỉ khi postcondition đã xác minh và artifacts hash đã ghi; phase update atomically, append journal. Không có `done` giả dựa trên “agent đã báo xong”.
- Khi không có plugin, vẫn được làm offline planning/design system; gate tại `FIGMA_CONNECTION_GATE`.
- Workflow controller chỉ ghi `design/WORKFLOW.json` và gọi `state.py` APIs/CLI. `state.py` tiếp tục làm single source of truth cho per-screen WAL, semantic binding và QA.
- Nếu `WORKFLOW` báo `DESIGN_EXECUTION` nhưng state v2 có item `creating`/`updating`, `resume` **đối soát live trước**, rồi mới bỏ PAUSED.
- `COMPLETED` yêu cầu delivery reports và 100% required P0 `done` + QA; không có unresolved transaction; P1/P2 chưa xong phải được nêu rõ và delivery status không khẳng định toàn bộ backlog complete.

### 7.1. Phase contracts và checkpoint evidence

| Phase | Điều kiện vào | Artifact/postcondition | Khi thất bại hoặc chạy lại |
|---|---|---|---|
| `ENVIRONMENT_CHECK` | run_id đã khởi tạo | machine checks + `AGENT_READY` | Setup/doctor; không chạy brainstorm nếu skill thiếu |
| `SPEC_VALIDATION` | APP_SPEC tồn tại | spec digest + normalized validation report | Dừng chờ user sửa spec |
| `BRAINSTORMING` | validated + skill ready | draft BRAINSTORM digest | Resume draft, không tự chấp thuận |
| `AWAITING_APPROVAL` | draft có digest | approval record gắn spec+brief hash | Đổi draft/spec → invalidate record |
| `DESIGN_PLANNING` | approval hợp lệ | `SCREENS.md`, `NEEDED.md`, recipes được đăng ký state v2 | Làm lại artifact lỗi, không mutate Figma |
| `DESIGN_SYSTEM_READY` | screen plan có hash | MASTER/tokens đủ theo contracts | Regenerate nếu design inputs đổi |
| `FIGMA_CONNECTION_GATE` | offline artifacts ready | `join_channel`, file identity, page/capabilities verified | ACTION_REQUIRED, không giả vờ READY |
| `DESIGN_EXECUTION` | target verified, writer lock | từng screen `done`/`updating` theo state v2 | Reconcile WAL, không replay create mù |
| `QUALITY_ASSURANCE` | screen có node identity | QA structural/visual evidence + `state.py qa` | Targeted repair ≤2; blocked nếu P0 fail |
| `DELIVERY` | P0 đủ QA, không WAL mở | reports, checksum, coverage, blockers | Không ghi `COMPLETED` nếu thiếu chứng cứ |

Controller ghi checkpoint có `phase`, `input_hashes`, `output_hashes`, `timestamp`, `evidence_paths`, `outcome`; không cho skip phase khi thiếu postcondition. Checkpoint không chứng minh thao tác Figma nếu không có live verification tương ứng.

### 7.2. WORKFLOW.json schema (rút gọn)

```json
{
  "version": 1,
  "run_id": "run-20261010-001",
  "runtime": "codex",
  "spec_path": "specs/APP_SPEC.md",
  "phase": "AWAITING_APPROVAL",
  "phase_attempt": 1,
  "status": "waiting_user",
  "spec_sha256": "<64 lowercase hex digits>",
  "approval": null,
  "artifacts": {
    "brainstorm": {"path": "design/BRAINSTORM.md", "sha256": "<digest>"}
  },
  "last_error": null,
  "checkpoints": [],
  "updated_at": "2026-10-10T19:00:00+07:00"
}
```

Dữ liệu minh họa chứa placeholder, không phải giá trị production. Trên disk schema bắt buộc `sha256` match `^[a-f0-9]{64}$`; `run_id` unique trong workspace. Mọi update atomic write temp→fsync→rename; event journal append-only; lock riêng cho controller, còn exclusive Figma writer lock mở suốt phiên mutation.

### 7.3. Ownership, locks, and liveness

- Writer lock: `.agent/locks/figma-writer.lock` scoped theo **Figma target file identity**. Trong cùng workspace bảo vệ quá trình ghi từ đầu đến cuối, không chỉ `STATE.json` writes. Lock dùng OS-backed advisory lock/process lifetime nếu có; khác máy hoặc khác workspace không đảm bảo distributed mutual exclusion. Với trường hợp đó cấu hình shared lease là phần triển khai mở rộng, không mặc định hứa distributed lock.
- Nếu process chết: kiểm tra PID+process start identity, không xóa lock chỉ theo TTL trong khi tiến trình còn sống; resume reconcile.
- `state.py` có khóa riêng cho atomic state writes, không sửa trực tiếp lock này trong controller. Thứ tự lock: writer lock → state operation; không giữ state lock khi đang gọi network/MCP.
- Không thực hiện `create/delete/reparent` trong cùng file từ hai runtime đồng thời; Claude hoặc Codex có thể cùng plan offline.

## 8. Design execution: tái sử dụng hiện trạng thay vì thêm engine trùng

### 8.0. Product-design deliverable contract

| Artifact | Bắt buộc | Acceptance |
|---|---|---|
| Figma frames | Mọi P0 screen được duyệt | Frame có semantic/root node ID trong state v2; live read verified |
| UI states | Với P0: `default`, `loading`, `empty`, `error` nếu screen có trạng thái tương ứng; trạng thái không áp dụng phải ghi `N/A` + lý do | State inventory/recipes có mapping ↔ Figma frame/component/annotation; empty/error thành frame riêng theo Option A, loading có thể annotation nếu được phê duyệt |
| Design system | Màu, typography, spacing, radius | MASTER + tokens với contrast checks và mapping sang property trên canvas |
| Figma components | Thành phần tái sử dụng thiết yếu theo brief | Có node ID/instance reference nếu TalkToFigma có capability; fallback là duplicate có nhãn trong report, không nói là component nếu chưa tạo được |
| User flows | Toàn bộ approved P0 flows | Screen IDs, transition map được review; điểm đến không có frame phải báo missing |
| Prototype | Chỉ khi APP_SPEC/approved brief yêu cầu | Kiểm tra khả năng tạo link trong tool schema; unsupported → `PARTIAL/BLOCKED`, không đánh dấu completed requirement |
| Structural/Visual QA | 100% P0 | Screenshot hoặc evidence tham chiếu, structural node inspection, pass/fail, targeted repair trace |
| Delivery | Figma file/page reference + reports | `DESIGN_REPORT.md`, `WORKFLOW_REPORT.json`, backlog P1/P2 và limitations; không trả repository/source code app |

**Design completeness:** `P0_completion = verified_P0_screens / approved_P0_screens`; `P0_state_coverage = verified_applicable_P0_states / required_applicable_P0_states`; `flow_coverage = linked_P0_flow_edges / required_P0_flow_edges` (nếu flow chỉ là sơ đồ offline và không có linking capability, đo completeness ở bản flow map, ghi rõ không phải playable prototype). Mục tiêu 100% cho phạm vi được duyệt trước `COMPLETED`, riêng prototype chỉ theo support/approval. Đánh giá UX là review có nhận định, không biến thành phép đo giả định từ screenshot.



Sau approval:

1. Planning: tạo `design/SCREENS.md`, `assets/NEEDED.md`, per-screen recipe trong `design/screen-recipes/`; dùng `state.py plan(-bulk)` để đăng ký các item.
2. Design system: gọi `ui-ux-pro-max`, persist `design-system/<app>/MASTER.md` và tạo `design/tokens.json`; validate contrast theo chính sách AGENTS.
3. Figma gate: lấy channel ID ở local runtime config hoặc hỏi người dùng; `join_channel`, xác minh Figma file identity/page qua `get_document_info`, kiểm tra capability thật.
4. Execution: với mỗi màn theo P0→P1→P2, gọi `intent.py` qua `state.py inspect`; nếu unchanged và node valid, skip; nếu patchable thì `begin-update` sau live verify; nếu rebuild/legacy thì theo WAL/reconcile. Tận dụng instance/clone, batch calls nếu tool schema hỗ trợ; không giả lập universal bulk-create.
5. QA: structural qua `get_nodes_info`, visual export/inspect ảnh cho P0; kiểm tra applicable UI states và approved P0 flows; 2 targeted repair attempts/screen; `state.py qa` chỉ sau bằng chứng. `done`/`done-update` được state v2 enforce; screenshot evidence lưu `design/qa/<screen>/<revision>/`.
6. Delivery: ghi `design/DESIGN_REPORT.md`, `design/WORKFLOW_REPORT.json` với screen/state/flow coverage, QA, substitutions/placeholders, prototype capability, MCP call stats, blockers, `product_code_files_generated=0` và version fingerprint; phase COMPLETE chỉ sau acceptance gate.

**Incremental:** thay đổi text/style dùng `scripts/intent.py` hiện có. Không triển khai “smart diff” thứ hai. Cache read-only được dùng để lập plan, nhưng identity node phải kiểm chứng Figma live trước mutation.

## 9. Configuration/Artifacts Contracts

| Path | Chủ sở hữu | Git? | Nội dung |
|---|---|---|---|
| `workflow.yaml` | Developer | Có | phase policy, retries, QA gates, limits |
| `config/dependencies.lock.json` | Developer | Có | pinned versions/commits và checksums nếu có |
| `./agent` | CLI | Có | entrypoint |
| `scripts/agent.py` | CLI | Có | parse args, dispatch |
| `scripts/bootstrap.py` | Bootstrap | Có | preflight, skill/MCP install, socket lifecycle |
| `scripts/workflow.py` | Workflow | Có | transitions, approval, checkpoint, resume |
| `scripts/runtime_adapters.py` | Adapter | Có | interface + Claude/Codex implementations |
| `scripts/readiness.py` | Doctor | Có | check results + stale detection |
| `specs/APP_SPEC.template.md` | User | Có | input contract, no channel |
| `specs/APP_SPEC.md` | User | tùy chọn | project specification |
| `design/BRAINSTORM.md` | Agent/User | Có | draft + approved reference |
| `design/WORKFLOW.json` | Controller | Có | workflow status/checkpoint |
| `design/STATE.json` | state.py v2 | Có, nếu user chọn | screen/item transactions |
| `design/WORKFLOW_REPORT.json` | Controller | Có | machine-readable delivery **chỉ cho thiết kế Figma**, gồm design coverage và không có source app |
| `.agent/runtime/*.json`, `*.pid`, `*.log` | Bootstrap | **Không** | live health/process/channel, local connection data |
| `.agent/locks/` | Controller | **Không** | writer/process locks |

`workflow.yaml` dùng parser pinned dependency (`yaml.safe_load`, không chạy arbitrary constructors). Nếu muốn tiếp tục zero third-party Python setup có thể đổi sang JSON trước implementation plan; **mặc định giữ YAML như thiết kế được duyệt**, yêu cầu minimal pinned PyYAML runtime.

### 9.1. Workflow policy (schema ví dụ)

```yaml
version: 1
backend: talktofigma
runtime: [claude, codex]
brainstorm:
  required: true
  approval_required: true
  max_questions: 8
limits:
  screens_per_run: 25
  tool_failures_per_step: 2
  targeted_repairs_per_screen: 2
qa:
  structural_all: true
  visual_p0: true
  block_p0_completion_on_visual_failure: true
  required_p0_state_coverage: 1.0
  required_p0_flow_coverage: 1.0
product_output:
  figma_design_only: true
  prohibit_application_code: true
recovery:
  reconcile_before_retry: true
  forbid_force_resume: true
  file_identity_check: true
```

Policy validator phải từ chối `backend != talktofigma`, `approval_required: false` khi design execution có Figma writes, các giá trị giới hạn ngoài range, và unknown schema version. Không đưa secret vào policy.

## 10. Guardrails, lỗi và tình huống biên

- **Tool timeout after write:** Figma có thể đã thực hiện mutation. Không phát lại mutation trước khi `get_nodes_info`/document read xác minh desired state. Nếu mơ hồ, pause; tuyệt đối không delete bằng substring name.
- **Channel changed:** không cần sửa APP_SPEC; cập nhật `.agent/runtime/figma.local.json`, reset FIGMA_READY, join mới, xác minh file identity trước resume.
- **Manual edits on canvas:** verify parent/type/structure, mismatch ambiguous thì `BLOCKED_MANUAL_EDIT`, hỏi keep/overwrite. Không đồng nhất “tool success” với “design approved”.
- **Unsupported skill installation:** `ACTION_REQUIRED` với lệnh/thao tác cụ thể, không skip skill âm thầm.
- **Network lost during setup:** stage journal + idempotent rerun; không rollback bừa checkout đã tồn tại hoặc config user khác.
- **Config drift or cli upgrade:** doctor returns adapter mismatch; không chạy workaround đoán flag.
- **Spec update mid-design:** hash mismatch chuyển `AWAITING_CHANGE_APPROVAL`, không gọi `accept-spec` chỉ vì file tồn tại.
- **Asset thiếu:** placeholder phải hiện rõ trong QA/report; P0 có required asset placeholder chưa được user chấp thuận thì delivery `PARTIAL/BLOCKED`, không tuyên bố usable-complete.
- **Prompt injection trong APP_SPEC/asset metadata:** dữ liệu đầu vào không được biến thành system instructions, shell command hay permission bypass. Dù APP_SPEC yêu cầu “generate frontend” hoặc trích prompt bên ngoài, agent chỉ xuất design; nếu user thật sự muốn code cần một workflow dự án khác, không tự nâng scope.
- **File Figma giống tên nhưng khác ID:** identity dựa trên thông tin target đủ tin cậy từ MCP/session, không chỉ tên. Không có stable file identifier có thể xác minh => ask/reconcile before destructive writes.
- **Concurrent sessions:** chạy một writer trong cùng workspace; giữa nhiều workspace/máy dùng cùng Figma target thì phải dựa vào quy trình phối hợp người dùng, không hứa lock toàn cầu.

Ma trận lỗi workflow (các mã mới, không thay mã CLI state.py v2):

| Code | Condition | Action |
|---|---|---|
| `E_ENV_MISSING` | Thiếu prerequisite OS tool/runtime | Hướng dẫn cài; setup blocked |
| `E_SKILL_UNAVAILABLE` | Skill chưa được verify | ACTION_REQUIRED / retry setup |
| `E_MCP_CONFIG_DRIFT` | MCP registration lệch pinned checkout | Backup + explicit repair |
| `E_SOCKET_DOWN` | Socket chết | `up` restart rồi doctor |
| `E_PLUGIN_DISCONNECTED` | Chưa join channel thành công | Chờ plugin/user |
| `E_FIGMA_IDENTITY` | Không xác minh đúng file/page | Block Figma writes |
| `E_APPROVAL_STALE` | Spec/brief hash đổi | Review/re-approve |
| `E_WRITER_CONFLICT` | Writer lock đang có | Block second writer |
| `E_TRANSACTION_UNCERTAIN` | Figma mutation kết quả không xác định | Reconcile, không retry mù |
| `E_QA_BLOCKED` | P0 QA hoặc state/flow coverage chưa passed | Targeted repair/partial delivery |
| `E_SCOPE_VIOLATION` | Runtime cố tạo source app hoặc chạy app build | Block; báo design-only policy |
| `E_PROTOTYPE_UNSUPPORTED` | Brief yêu cầu prototype nhưng backend thiếu capability | PARTIAL/BLOCKED theo yêu cầu đã duyệt; không claim prototype done |

## 11. Kế hoạch kiểm thử (định nghĩa test; **chưa chạy**) 

### 11.1. Unit + CLI integration (không cần Figma)

- `setup_twice_keeps_single_mcp_registration_and_socket`: hai lần setup vẫn 1 registration/runtime và 1 socket process.
- `setup_missing_bun_reports_dependency_without_shell_install`: thiếu Bun không gọi curl/install tự động.
- `setup_skill_not_verified_never_marks_agent_ready`: skill cài dở phải ACTION_REQUIRED.
- `doctor_socket_ready_does_not_claim_figma_ready`: port sống nhưng plugin chưa join → FIGMA_NOT_VERIFIED.
- `design_invalid_spec_blocks_before_brainstorm`: spec thiếu P0 bị từ chối.
- `design_approval_matches_spec_and_brief_hash`: approval stale không chuyển sang design.
- `design_reentry_resumes_existing_run_id`: không tạo run thứ hai.
- `workflow_transition_rejects_skipping_approval`: không jump trực tiếp đến Figma execution.
- `resume_does_not_force_state_resume`: open WAL transaction yêu cầu reconcile.
- `second_writer_conflicts_even_if_state_file_is_free`: writer lock process-wide.
- `config_disallows_official_figma_backend`: backend sai rejected.
- `untrusted_spec_cannot_become_shell_command`: không execute hướng dẫn từ file input.
- `p0_requires_structural_and_visual_qa_for_completion`: blocked khi P0 chưa đạt.
- `design_only_rejects_product_code_generation`: spec cài chỉ dẫn viết SwiftUI/Compose/React → không tạo file `.swift`/`.kt`/`.tsx`, không gọi build; report giữ Figma-only.
- `p0_state_inventory_required_for_completion`: có P0 screen thiếu required `empty`/`error` → không `COMPLETED`; trường N/A bắt buộc có lý do.
- `prototype_requested_without_mcp_capability_is_not_claimed`: yêu cầu clickable prototype nhưng tool thiếu → explicit unmet requirement.

### 11.2. Agent integration + Figma live (môi trường người dùng)

- `I01`: `./agent design` khởi động đúng một runtime, skill available và MCP usable.
- `I02`: pause ở approval, sau khi user đồng ý tự tiến Pha 1→5; không cần prompt pha thủ công.
- `I03`: plugin chưa nối thì offline phases thành công, execution chờ ở `FIGMA_CONNECTION_GATE`.
- `I04`: timeout ngay sau `create_frame`, resume không duplicate root.
- `I05`: crash sau batch text trước done-update, reconcile desired value trước commit.
- `I06`: wrong file/channel bị chặn trước mutation.
- `I07`: manual edit và duplicate name đều block thay vì tự xóa.
- `I08`: P0 visual export fail → không mark `COMPLETED`.
- `I09`: re-run spec unchanged skip mutation mà vẫn verify live identity.
- `I10`: benchmark baseline vs v3 3 runs, same spec/model/file snapshot; median calls per validated screen.
- `I11`: brief Android/iOS native-style design → native-looking Figma frames, 0 `.swift`/`.kt`, 0 compilation.
- `I12`: P0 empty/error/loading state evidence checked; missing states hoặc prototype capability hạn chế ghi report, không mark requirement fulfilled.

**Verification command mục tiêu:** `python3 -m unittest discover -s tests -v`; thêm `./agent doctor --json` và integration scripts có nhãn Figma-live (không cho local unit test giả làm live proof). TDD bắt đầu từ failing tests; chạy full suite sau implementation.

## 12. Giao diện triển khai và tác động file

### 12.1. Existing files giữ nguyên behavior cơ sở

- `scripts/state.py`: reuse as-is cho v2; nếu cần API chuyển trạng thái phải bổ sung test bảo toàn WAL và backward compatibility, không thay trực tiếp STATE format.
- `scripts/intent.py`: reuse canonical digest + change classification; không tạo engine khác.
- `scripts/assets.py`: reuse scan/check; điều phối qua workflow.
- `AGENTS.md`, `CLAUDE.md`: thêm role `Product Designer` và **design-only hard stop** (no app source generation) cùng orchestration entrypoint và policy đúng phase; giải quyết mâu thuẫn cũ “không cài phần mềm” bằng cách **agent design không được cài**, chỉ `./agent setup` do user gọi mới thực thi approved workspace/user-scope changes; xóa hướng dẫn bắt channel ID trong APP_SPEC.
- `SETUP.md`: tài liệu usage + recovery; không trình bày Markdown như executable entrypoint.

### 12.2. New files/interfaces

| Module | Interface đề xuất | Phụ thuộc |
|---|---|---|
| `bootstrap.py` | `setup(runtime)`, `up()`, `down()`, `doctor(runtime)` | subprocess, dependencies lock, adapters |
| `runtime_adapters.py` | `detect()`, `register_mcp()`, `verify_skill()`, `launch()` | CLI pin/tool help |
| `readiness.py` | `collect_checks() -> list[CheckResult]` | bootstrap + agent probe evidence |
| `workflow.py` | `begin(spec,runtime)`, `advance(event)`, `resume()`, `gate(action)` | workflow state, state.py, approval |
| `agent.py` | `main(argv) -> int` | modules above |
| `./agent` | invokes Python CLI with controlled working dir | agent.py |

### 12.3. Thiết kế instruction cho Codex và Claude (ràng buộc giống nhau)

Trong `AGENTS.md` (Codex và source chung) và `CLAUDE.md` (Claude thin adapter) nên có cùng invariant thiết kế, ví dụ:

```text
ROLE: Figma UI/UX designer, not an application developer.
HARD RULES: TalkToFigma MCP only; do not generate application source code,
run app builds, scaffold mobile/web projects, or invoke code-development
planning skills in product-design runs.
PROCESS: validate APP_SPEC → brainstorm → approve brief → plan screens,
flows, states and tokens → verify Figma connection → render → verify → report.
OUTPUT: Figma file/page, design frames/components/states, QA evidence, coverage.
EXAMPLE: "Design Android settings screen" means draw a settings frame in
Figma, never create SettingsScreen.kt or Compose files.
```

**Tool description boundary:** TalkToFigma mutations chỉ dùng trong `DESIGN_EXECUTION` sau `CANVAS_READY`, approval và writer lock; không dùng trong brainstorm, validation, offline planning. Script harness (`bootstrap`, `workflow`, `state`) dùng để vận hành, không dùng làm app scaffolding. Skill `ui-ux-pro-max` chỉ lấy design guidance/tokens, không sinh HTML/CSS code output cho sản phẩm.

`workflow.py` không trực tiếp gọi tool TalkToFigma; hành động live thông qua interactive agent và MCP. `Gate` chỉ nhận evidence record (phase, file identity, node IDs, QA refs) được tạo từ tool results trong phiên agent; **không** xem text tự khai của model là xác thực mạnh. Trong v3, agent vẫn là trust boundary chịu trách nhiệm evidence; hệ thống local không thể tự chứng minh tool response nếu thiếu MCP client độc lập, nên các kết luận QA phải có screenshot/structural evidence lưu đĩa khi khả thi. Có thể tăng integrity bằng adapter MCP probe trong tương lai nhưng nằm ngoài scope.

## 13. Acceptance criteria và release gates

| Gate | Điều kiện cụ thể |
|---|---|
| `G0_Architecture` | Spec reviewed + interface frozen trước implementation plan |
| `G1_Setup` | setup idempotent, pinned dependency, config backup, no unsupported install, doctor reports dimensions |
| `G2_Workflow` | valid APP_SPEC → interactive brainstorm → approval hash → auto phase progression |
| `G3_Recovery` | interrupted creates/updates reconcile; 0 duplicate root; writer lock effective trong workspace |
| `G4_Quality` | 100% P0 structural+visual passed + applicable UI-state/flow coverage, 0 unresolved WAL, report minh bạch; 0 app-source generated |
| `G5_EndToEnd` | I01–I12 chạy qua Figma thật (I10 benchmark); đo screen/state/flow completeness; source generation = 0 trước release claim |

Tất cả `G1–G4` cần automated tests; `G5` cần live environment của người dùng. Không gọi v3 “complete” chỉ bằng unit tests. Không thay thế kết quả integration bằng khẳng định dựa trên docs.

## 14. Thứ tự triển khai dự kiến (chưa phải implementation plan đã duyệt)

1. CLI + config schema + fixture-based tests + doctor contract.
2. Idempotent setup, pinned dependencies, Claude/Codex adapters, socket supervisor.
3. Workflow state + atomic checkpoints + approval fingerprints.
4. `APP_SPEC.md` normalization, prompt bootstrapping, approved product-design brainstorming transition, **scope enforcement**.
5. Wire phase orchestration tới scripts/state v2 và TalkToFigma agent workflow; writer lock.
6. QA/delivery reporting (Figma design-only), state/flow coverage + prototype capability tracking, chaos suite, end-to-end verification, benchmark.

Sau khi người dùng **duyệt văn bản spec này**, invoke `superpowers:writing-plans` để viết `docs/superpowers/plans/2026-10-10-workflow-v3-implementation.md` theo TDD task-by-task, ghi exact files/commands/expected test failures, rồi xin duyệt plan trước khi sửa implementation code.

## 15. Trade-off và quyết định cần bảo lưu

- **Tối giản:** 1 controller + 1 interactive agent + existing state v2 + TalkToFigma; không tạo microservices. Đổi lại CLI adapter cần test khi CLI phát hành version mới.
- **Trải nghiệm setup:** setup tự động phần machine-accessible; đăng nhập/GUI/permission vẫn đòi user. Đây là giới hạn thật, không che bằng cờ `ready=true`.
- **YAML:** dễ review/edit cho workflow policy, đổi lại thêm PyYAML pin. Nếu muốn bỏ dependency, có thể đổi `workflow.yaml` → JSON **trước khi freeze plan**.
- **Rủi ro lớn nhất:** timeout sau mutation đã commit trên Figma. Ưu tiên reconcile + pause hơn retry gây duplicate.
- **KPI đo trước/sau:** startup time (từ setup đến AGENT_READY), manual interventions/run, workflow continuation rate, crash recovery success, mcp_calls/validated_screen. Báo metric thực nghiệm, không đặt con số đạt trước khi chạy live.

---

**Review request:** Xác nhận **Technical Spec v3.1 bản Design Only**: 1 approval gate sau brainstorm, chỉ output Figma design, không source code sản phẩm; setup/agent tools chỉ phục vụ harness, TalkToFigma-only, UI-state/flow coverage và ranh giới `COMPLETED`. Sau khi review văn bản mới sẽ lập implementation plan chi tiết cho **harness**, không lập kế hoạch coding mobile/web app.
