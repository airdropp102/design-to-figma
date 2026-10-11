# Đặc tả thiết kế — Figma Design Agent, phương án A (TalkToFigma-only)

Ngày: 2026-10-10  
Trạng thái: **Đã có patch local theo phương án A; cần integration test trên Figma thật**  
Nền tảng: **Codex CLI + Claude Code**, cùng kết nối qua **TalkToFigma MCP**  
Nguồn: `figma-design-agent.zip` do người dùng cung cấp.

## 1. Mục tiêu và phạm vi

**Quyết định đã chốt:** Giữ `grab/cursor-talk-to-figma-mcp` làm **backend Figma duy nhất**. Không gọi, không cấu hình và không tự động fallback sang **Official Figma MCP**, vì hạn mức/quota là ràng buộc quan trọng.

Nhiệm vụ harness không đổi: đọc `specs/APP_SPEC.md`, brainstorm khi có người dùng, tạo `SCREENS.md` và token, dựng thiết kế Figma, kiểm chứng, phục hồi sau mất kết nối. Tối ưu ở tầng điều phối gọi tool và quản lý state, **không xây capability router, không tạo MCP server mới, không chuyển sang multi-agent Figma writer**.

### Không thuộc phạm vi
- Không tự thêm tool chưa có vào plugin gốc; không giả định API bulk tạo frame hay variables/styles.
- Không truy cập Figma của người dùng ở giai đoạn viết spec.
- Không thêm trình tạo SwiftUI/Compose hoặc full Design IR vào phiên bản này.
- Không xóa các node Figma không có sở hữu/quyền xác định.

## 2. Hiện trạng xác nhận từ gói nguồn

1. `AGENTS.md` hiện tạo phần tử bằng các lệnh MCP tuần tự; đã dùng `set_multiple_text_contents` nhưng chưa có policy gom call theo loại hay thống kê MCP call/screen.
2. `scripts/state.py` dùng `STATE.json` version 1, có WAL `begin → node → done`, lock file, atomic replace, journal, pause/resume, `reset`, `ids`; toàn spec chỉ có một SHA-256 tổng.
3. Pha 4 đang **xóa màn tạo dở và dựng lại nguyên khung**, kể cả khi chỉ thay một số text; Pha 5 kiểm tra tổng quát, ảnh screenshot chỉ mỗi 3–4 màn.
4. `CLAUDE.md` cho phép nhiều sub-agent cùng ghi Figma nếu khác section. Điều này không phù hợp mục tiêu đồng bộ state/giảm tool calls của phương án A.
5. `SETUP.md` đã dùng TalkToFigma cho Codex/Claude; nên giữ đường kết nối này.

Theo danh mục tool upstream tại thời điểm soạn spec, TalkToFigma có các lệnh batch **`set_multiple_text_contents`, `delete_multiple_nodes`, `set_multiple_annotations`**, có `clone_node`, `create_component_instance`, `get_nodes_info`, nhưng **không có batch tổng quát tạo/sửa mọi loại node**. Harness phải kiểm tra schema của bộ MCP được kết nối trước lần gọi đầu và fallback về lệnh đơn nếu phiên bản cài đặt không hỗ trợ.

## 3. Kiến trúc tối thiểu đề xuất

```text
APP_SPEC.md → BRAINSTORM.md → SCREENS.md + tokens.json + ASSET_MANIFEST
                                      │
                                      ▼
                             Screen Work Planner
                        (render intent per screen)
                                      │
                                      ▼
                 STATE.json v2 + semantic node registry
                  [hash / node_id / last_verified / QA]
                                      │
                                      ▼
                     Single Figma Writer / Call Planner
                [clone/instance → batch text → style/layout]
                                      │
                                      ▼
                   TalkToFigma MCP → Figma Plugin → Canvas
                                      │
                                      ▼
                      Structural Check + Visual QA
                                      │
                                      ▼
                         Journal + State Commit
```

**Một Figma writer tại một thời điểm**; các sub-agent (nếu có) chỉ được lập screen plan/review offline, không tự gọi Figma tools. Cùng một `AGENTS.md` làm hợp đồng chung, `CLAUDE.md` chứa ghi chú adapter Claude; Codex dùng `AGENTS.md` trực tiếp.

## 4. Quy tắc điều phối MCP

### 4.1 Thứ tự lệnh
1. `join_channel` → xác minh file/page (`get_document_info`), làm phục hồi nếu cần.
2. `state.py begin ...`: ghi ý định trước mutation; khi tạo frame chính, ghi node ID ngay.
3. Ưu tiên `create_component_instance` khi component đã có và phù hợp; nếu không có, dùng `clone_node` từ foundation chuẩn; chỉ create primitive khi không thể reuse.
4. Gom text overrides của các node đã xác thực thành **một `set_multiple_text_contents` cho mỗi nhóm hợp lý**. Tránh gọi `set_text_content` từng node.
5. Chỉ dùng `delete_multiple_nodes` với tập node ID mà state ghi nhận thuộc **chính item đang dọn**, sau kiểm tra trước khi xóa. Không bulk-delete các node tìm được bằng tên gần đúng.
6. Gom read bằng `get_nodes_info` theo danh sách ID; không gọi `get_node_info` lặp lại cho các node đã kiểm tra trong cùng bước.
7. Gọi styling/layout đơn khi cần; **không gọi lặp nếu giá trị mục tiêu không đổi** theo cached plan được xác minh.
8. `done` chỉ khi structural check đạt; P0 cần thêm visual QA trước `done`, P1/P2 thực hiện QA theo mức rủi ro (chi tiết §6).

### 4.2 Call planning và budget
- Lập checklist thao tác cho một màn trước mutation: reuse candidates, primitive cần tạo, text overrides, style mutations, verify/export.
- Không phát lệnh “thử mò” tool hoặc lặp lại idempotent mutations một cách vô ích.
- Lưu bộ đếm theo màn: `tool_calls`, `failed_calls`, `batch_calls`, `retry_count`, `reused_nodes`, `duration_ms` (nếu có thời gian thực tế đo được).
- Sau **hai lỗi tool liên tiếp tại cùng một bước**, `pause` như chính sách hiện tại. Không khẳng định đã tạo thành công nếu timeout/mất phản hồi; phải đọc Figma để xác nhận trước khi retry.

## 5. State v2, semantic IDs và incremental update

### 5.1 Trạng thái mở rộng
Migrate version 1 → version 2 **giữ nguyên các `items`, `node_id`, `status`, `attempts`, `figma`, `journal` cũ**. Chỉ thêm metadata mặc định vào item, không yêu cầu rebuild toàn bộ frame cũ.

Một item màn hình mẫu (dữ liệu minh họa; key và node_id thực lấy từ Figma):

```json
{
  "kind": "screen",
  "key": "S05",
  "name": "S05 Chi tiết dịch vụ",
  "status": "done",
  "node_id": "41:7",
  "priority": "P0",
  "spec_fingerprint": "sha256:<canonical-per-screen-input>",
  "dependency_fingerprint": "sha256:<used-tokens-and-assets>",
  "semantic_nodes": {
    "service.detail.header": "41:9",
    "service.detail.cta.label": "41:23"
  },
  "verified_at": null,
  "qa": {"structural": "passed", "visual": "passed"},
  "metrics": {"tool_calls": 0, "failed_calls": 0, "batch_calls": 0, "reused_nodes": 0}
}
```

Trong bước implement, **giá trị hash phải là digest thật, không phải chuỗi placeholder**. Tách hai digest: `spec_fingerprint` dựa trên nội dung màn/flow, `dependency_fingerprint` dựa trên token và asset được màn đó sử dụng; canonical JSON sort keys và encoding UTF-8. Không dùng toàn bộ hash của `APP_SPEC.md` để bắt mọi màn rebuild.

Registry `semantic_nodes` do state quản lý, không dựa vào tên layer tùy ý. Chỉ ghi mapping sau khi `get_node_info`/`get_nodes_info` xác nhận node ID, type, cây cha và file phù hợp. Nếu node mất hoặc đổi cha thì **invalidate mapping**, chỉ resolve lại bằng tên chính xác dưới **đúng parent**; nếu nhiều kết quả, `pause` để tránh tác động nhầm.

### 5.2 Quy tắc phân loại thay đổi
- **Unchanged**: cả hai hash không đổi, node vẫn tồn tại và verification nhẹ đạt → skip mutation.
- **Text-only**: danh sách text đổi, semantic node ID vẫn hợp lệ, type = TEXT → batch `set_multiple_text_contents`, verify nội dung rồi cập nhật hash.
- **Style-only**: style/token đổi, biết chính xác node chịu ảnh hưởng và tool hỗ trợ property đó → cập nhật đúng node, verify.
- **Structural**: thứ tự container/layout/component tree đổi hoặc registry không còn đáng tin → rebuild **màn liên quan** theo flow Pha R; không tự xóa nhiều màn khác.
- **Unknown/manual edit**: Figma cấu trúc khác so với trạng thái cuối cùng xác nhận, chưa xác định nguồn → `pause` và xin quyết định keep/overwrite. Tuyệt đối không ghi đè thủ công một cách mù quáng.

Một màn `done` từ state v1 với fingerprint trống là **legacy-unverified**, không mặc định rebuild. Chỉ backfill các node xác minh được và yêu cầu lần đầu chạy incremental được đánh giá an toàn.

### 5.3 WAL khi cập nhật
Thêm pha per-item `updating` hoặc transaction update tương đương, journal ghi old/new fingerprints, affected node IDs và nhóm thao tác. Khi crash giữa cập nhật:
- Không gọi batch lần hai trước khi `get_nodes_info` kiểm tra thực tế các mục tiêu.
- Nếu tất cả đã bằng desired state → commit.
- Nếu một phần thành công và có thể xác định chính xác → hoàn tất phần còn thiếu.
- Không chắc node nào đã bị sửa → `pause` và đối soát thủ công; không làm lệnh xóa phá hủy.

## 6. QA và tiêu chí `done`

**Structural cho mọi màn:** đúng root node ID, tên duy nhất dưới target parent, kích thước khung phù hợp, semantic node bắt buộc tồn tại, text không placeholder, không missing asset bị giấu. Kiểm tra bằng `get_nodes_info` theo nhóm.

**Visual:** P0: export/inspect ảnh màn trước `done`; P1/P2: export mỗi 3 màn hoặc bắt buộc nếu có thay đổi structural, text dài, hình ảnh mới hay tool lỗi. Vì export có thể trả base64 lớn, lưu ảnh ra file cục bộ và chỉ đưa ảnh cần thiết vào model context. Nếu ảnh không xuất được, đánh dấu `visual=blocked`, không tuyên bố QA đã qua; P0 phải pause/yêu cầu review theo policy.

**Sửa lỗi:** tối đa hai vòng targeted repair cho cùng một màn. Nếu vẫn lỗi, đánh dấu failed và báo rõ nguyên nhân, không `done` giả.

## 7. Bề mặt thay đổi đã patch trong bundle

| File | Thay đổi cần làm |
|---|---|
| `AGENTS.md` | Policy TalkToFigma-only; một writer; reuse-first; batching có chứng minh; per-screen diff; QA gate; crash recovery update |
| `CLAUDE.md` | Bỏ khả năng sub-agent cùng ghi canvas; chỉ cho phép parallel planning/review, phù hợp Codex |
| `scripts/state.py` | Backward-compatible state v2, semantic node IDs, fingerprints, update transaction, metrics, validate transitions |
| `SETUP.md` | Loại mọi gợi ý Official Figma MCP; giải thích giới hạn tool, baseline/metrics và quy trình migration |
| `evals/CHAOS.md` | Crash sau batch text và trước state commit, stale node mapping, manual edits, duplicate names |
| `evals/RUBRIC.md` | Calls/screen, first-pass QA, incremental-skip rate, batch coverage, cost/latency delta |
| `tests/test_state.py` | Unit tests v1→v2, WAL, fingerprint, skip/update/recovery, khóa đồng thời và no-delete-on-ambiguity |

Đã giữ nguyên `scripts/assets.py` và setup MCP backend. Bổ sung `scripts/intent.py`, `specs/SCREEN_RECIPE.template.json`, `tests/test_state_v2.py`; có thêm CLI `adopt` để backfill màn done từ state v1 mà không rebuild.

## 8. Đánh đổi, rủi ro và benchmark

### Trade-offs
- **Ưu:** không dùng quota Official Figma MCP; ít thành phần hơn hybrid; giữ các công cụ và setup hiện có.
- **Nhược:** Figma vẫn cần nhiều lệnh primitive cho geometry/layout, vì upstream không hỗ trợ bulk tạo cây node; biến/styles native, effect/phức tạp vẫn bị giới hạn.
- **Chi phí:** thêm metadata/invalidation/reconcile và thời gian visual QA; cần cân bằng giữa chất lượng với số export.

### Rủi ro trọng tâm
Cached node ID bị stale sau khi người dùng sửa Figma, dẫn đến sửa nhầm node. Biện pháp: validate parent/type/file, tránh tên không duy nhất, pause khi không chắc chắn; tuyệt đối không auto-delete theo tìm kiếm gần đúng.

### Benchmark chấp nhận
Đo B01 trên **cùng một file thử nghiệm đã sao lưu**, cùng spec, cùng agent/model, lặp 3 lần và lấy median; so baseline từ gói nguồn với patch. Không gán số liệu khi chưa chạy Figma thật.

| KPI | Định nghĩa | Mục tiêu |
|---|---|---|
| `mcp_calls_per_screen` | Tổng số call MCP / số màn kiểm chứng đạt | Giảm ≥ 25% so baseline |
| `validated_screen_success_rate` | Số màn qua structural + QA bắt buộc / số màn thực hiện | ≥ 95% |
| `incremental_skip_precision` | Màn được skip và kiểm tra thật sự không cần update / tổng màn skip | 100% trong bộ test |
| `duplicate_root_frames` | Frame root trùng chính xác `S<ID>` sau phục hồi | 0 |
| `wrong_node_mutation` | Mutation ngoài node do state sở hữu | 0 |
| `state_recovery_success` | Chaos scenario pass / tổng case | 100% trong bộ test |

Nếu QA cải thiện nhưng call count không giảm, phải báo trade-off thay vì khẳng định tối ưu hoàn tất.

## 9. Acceptance test cần có trước implementation

1. Test migration state v1 giữ nguyên node IDs, trạng thái done, phase, figma channel.
2. Test màn unchanged với Figma node hợp lệ → không có mutation.
3. Test 5 text changes → một `set_multiple_text_contents` nếu installed schema hỗ trợ; đối soát giá trị sau batch.
4. Test 1 text node mất → vô hiệu mapping, không patch node ngẫu nhiên.
5. Test đổi token chỉ của component A → không rebuild màn không sử dụng A.
6. Test crash sau Figma mutation, trước ghi `done` → reconcile được mà không nhân đôi mutation.
7. Test 2 frame root trùng tên khi recovery → pause, không xóa.
8. Test P0 export/QA lỗi → không đánh dấu passed/done.
9. Test writer thứ hai cùng ghi file/channel → bị khóa để tránh race.
10. Test mọi thao tác vẫn chạy qua TalkToFigma duy nhất, không có cấu hình Official Figma MCP.

## 10. Các milestone và mức xác minh

**Milestone A1 (policy/tool planning):** Đã cập nhật AGENTS/CLAUDE/SETUP về one-writer, reuse-first, batching có kiểm tra schema, telemetry. Benchmark live chưa chạy.

**Milestone A2 (incremental):** Đã code state v2 migration, semantic registry, per-screen fingerprint, text/style patch transaction, required live-verification flag, adopt legacy và local regression tests. Live stale-ID guard còn phụ thuộc agent gọi `get_nodes_info` thực tế, không có Figma client trong Python scripts.

**Milestone A3 (quality):** Đã code QA gate và bổ sung rubric/chaos; targeted visual repair được mô tả trong AGENTS. Chưa chạy visual integration test hoặc số liệu baseline-vs-patch vì không có channel Figma được kết nối.

Regression suite local chạy bằng `python3 -m unittest discover -s tests -v`; các test Figma canvas/benchmark cần môi trường người dùng để xác minh riêng.

## 11. Quyết định còn cần xác nhận khi review

Đặc tả mặc định rằng **không cho nhiều agent đồng thời ghi lên cùng một file Figma**; agent con nếu có chỉ tạo nội dung kế hoạch offline. Đồng thời P0 phải qua visual QA trước khi `done`; nếu export ảnh thất bại thì dừng thay vì hoàn thành âm thầm.

Bước tiếp theo ở môi trường có Figma plugin: chạy baseline B01, visual QA và chaos test C1–C15; chỉ sau đó mới đánh giá KPI giảm call trên màn thật.
