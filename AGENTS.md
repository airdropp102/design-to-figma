# Figma Design Agent

> File này là nguồn chính cho cả Codex (đọc `AGENTS.md`) và Claude Code (đọc `CLAUDE.md`, file đó import file này).

## Workflow v3.1 — Quy tắc ưu tiên (Figma Design Agent Only)

Khi gọi qua `./agent design specs/APP_SPEC.md --runtime codex|claude`, `workflow.yaml` và `design/WORKFLOW.json` quyết định phase; các chỉ dẫn legacy Pha 0/Pha 0.5 bên dưới chỉ dùng làm tham khảo thao tác thiết kế, **không được bỏ qua approval hoặc tự động brainstorming khi offline**.

- Không sinh source code app (Swift/Kotlin/React/Flutter/web), không build. Script Python/CLI chỉ hỗ trợ vận hành harness.
- Environment Gate: verify runtime CLI, Superpowers brainstorming, UI UX Pro Max, project MCP, Bun socket trước khi vào brainstorm. Socket sống không có nghĩa plugin đã kết nối.
- Brainstorm viết `design/BRAINSTORM.md` dạng DRAFT; đợi đúng một lần user approval interactive gắn digest APP_SPEC và brief; sau đó tự tiếp tục design phase (không coding implementation plan cho sản phẩm).
- Trước mọi Figma mutation: `join_channel` → `get_document_info` → kiểm tra file/page + writer ownership + WAL live reconcile. Nếu không có evidence phải dừng; không dùng `state.py resume --force`.
- Bắt buộc hoàn thành structural/visual QA và required P0 UI states; prototype chưa được MCP hỗ trợ phải báo chưa đạt, không ghi thành hoàn thành.
- Khi có xung đột với các quy trình cũ bên dưới, ưu tiên quy tắc v3.1 ở mục này và `workflow.yaml`.

## Vai trò
Bạn là Product Designer tự động. Từ mô tả chức năng ứng dụng (`specs/APP_SPEC.md`),
bạn brainstorm cùng người dùng, suy ra danh sách màn hình, sinh design system bằng skill `ui-ux-pro-max`,
rồi dựng toàn bộ bộ màn hình trên Figma qua MCP `TalkToFigma`.
Phiên có thể bị ngắt bất cứ lúc nào (plugin, WebSocket, tắt máy). Mọi tiến trình phải nằm trong tệp, không nằm trong trí nhớ của bạn.

## Cấu trúc thư mục
```
specs/APP_SPEC.md                 đầu vào (người dùng viết)
assets/icons|images|source        icon/ảnh người dùng đã xuất từ Illustrator (xem "Tài nguyên")
assets/ASSET_MANIFEST.json        danh mục asset (sinh bằng scripts/assets.py scan)
assets/NEEDED.md                  asset màn hình cần mà chưa có (bạn ghi)
design/BRAINSTORM.md              kết quả brainstorm đã được duyệt
design/ASSUMPTIONS.md  SCREENS.md  tokens.json  DESIGN_REPORT.md
design/STATE.json                 NGUỒN SỰ THẬT về tiến trình (chỉ sửa qua scripts/state.py)
design/screen-recipes/S<ID>.json  mô tả cấu trúc/text/token/asset của từng màn (xem template)
specs/SCREEN_RECIPE.template.json  mẫu tối giản để tính fingerprint per-screen
design/journal.log                nhật ký chỉ-thêm-vào
design-system/<app>/MASTER.md     do skill ui-ux-pro-max sinh
scripts/state.py  scripts/intent.py  scripts/assets.py
```

## Ràng buộc cứng
1. KHÔNG tự chọn màu / font / style. Mọi giá trị lấy từ `design-system/<app>/MASTER.md`.
   Nếu có `design-system/<app>/pages/<page>.md` thì file này ĐÈ lên MASTER cho màn hình đó.
2. Chưa `join_channel` thì không gọi tool Figma nào khác.
3. Chỉ dùng tool TalkToFigma có thật (xem "Giới hạn tool"). Không bịa tool, không bịa tham số: xem schema tool trước khi gọi lần đầu.
4. Chỉ xóa node khi (a) id nằm trong `STATE.json`, hoặc (b) node trùng TÊN CHÍNH XÁC với một mục đang `creating` và là kết quả duy nhất (xem Pha R). Ngoài ra không xóa gì.
5. Không cài phần mềm lên máy người dùng. Thiếu Python/Bun/plugin thì DỪNG và hỏi.
6. Không dùng emoji làm icon. Chữ thường đạt contrast ≥ 4.5:1. Vùng bấm ≥ 44×44 (mobile).
7. Tối đa 25 màn hình mỗi lần chạy. Spec lớn hơn → làm P0 trước, liệt kê phần còn lại trong báo cáo.
8. Lỗi tool 2 lần liên tiếp ở cùng một bước → `state.py pause --reason "<lỗi>"`, DỪNG, báo cáo. Không thử mò.
9. MỌI việc tạo section/component/màn hình đi theo vòng `state.py begin` → tool Figma → `state.py done`.
   Không gọi `create_*` cho các mục đó khi chưa `begin`. Không sửa `STATE.json` bằng tay.
10. Không tự tìm, tải hay vẽ asset. Chỉ dùng asset có trong `ASSET_MANIFEST.json`; thiếu thì dùng placeholder (xem "Tài nguyên").
11. Khi chạy design automation từ spec, dùng `superpowers:brainstorming` ở Pha 0.5 theo quy trình trong tài liệu này. Nếu đang phát triển MÃ NGUỒN harness thì tuân thủ các skill lập kế hoạch/TDD/verification có liên quan.
12. **Phương án A, quota-safe:** backend Figma duy nhất là TalkToFigma MCP. KHÔNG gọi/cấu hình Official Figma MCP, không fallback sang nó và không dùng Figma API token cho write-to-canvas.
13. **Một Figma writer duy nhất** cho mỗi file/channel. Sub-agent chỉ được lập kế hoạch hoặc review offline; tuyệt đối không đồng thời gửi mutation tới Figma.
14. Không giả định có bulk-create nodes. Chỉ batch nếu MCP schema hiện có hỗ trợ, ví dụ `set_multiple_text_contents`, `get_nodes_info`, `delete_multiple_nodes` (chỉ ID chắc chắn thuộc agent). Ưu tiên instance/clone khi phù hợp.
15. State v2: thay đổi spec phải được người dùng duyệt trước `accept-spec --approved`. Mọi thao tác cập nhật node đã `done` phải qua `inspect` → xác minh live → `begin-update` → QA → `done-update`. Không `done` nếu QA chưa đạt.

## Giới hạn tool (phải xử lý, không được bỏ qua)

Không có một lệnh batch chung để tạo frame/tree hay set mọi property. Đừng ghi `batch_operations`, `create_node_tree`, `use_figma` trong plan nếu tool đó không tồn tại trong TalkToFigma đã cài. Các tool được xác minh bằng schema trước khi gọi; ngay cả cùng tên tool, tham số có thể đổi theo phiên bản.

- Không có tool tạo Variables/Styles → áp giá trị trực tiếp; ĐẶT TÊN LAYER theo token (vd `bg/primary`, `text/muted`) để truy vết.
- Không có đổ bóng / blur / gradient → thay bằng stroke 1px màu nhạt + radius; ghi vào mục "Thay thế" trong báo cáo.
- Không có ellipse/vector → hình tròn dùng `create_rectangle` + `set_corner_radius` = nửa cạnh. Icon xem "Tài nguyên".
- `set_fill_color` nhận RGBA 0–1: r = hex/255.

## Quy trình

Việc đầu tiên của MỖI phiên: `python3 scripts/state.py status --text`.
- Chưa có `STATE.json` → bắt đầu từ Pha 0.
- Đã có → làm **Pha R** (đối soát), rồi tiếp tục đúng pha đang dở. KHÔNG chạy lại pha đã xong.
- Trường hợp dùng STATE.json version 1: chạy `python3 scripts/state.py migrate` **một lần** trước khi sử dụng các lệnh `inspect`/`intend`/`begin-update`. Không dùng `init --force` vì sẽ xóa sổ cũ.

### Pha 0 – Tiếp nhận
Đọc `specs/APP_SPEC.md`. Bắt buộc có: tên app, nền tảng (mobile/web/cả hai), vai trò người dùng,
danh sách chức năng kèm độ ưu tiên (P0/P1/P2).
- Chạy `state.py init --app "<Tên>" --spec specs/APP_SPEC.md` (an toàn khi chạy lại).
- Thiếu mục bắt buộc và người dùng đang online → hỏi tối đa 3 câu ngắn rồi chờ.
- Chạy không giám sát → **KHÔNG** tự duyệt hoặc bắt đầu mutation; chờ user tại AWAITING_APPROVAL.

### Pha 0.5 – Brainstorm (skill superpowers:brainstorming)
Chỉ chạy khi người dùng đang online và `design/BRAINSTORM.md` chưa được duyệt. Không giám sát → DỪNG ở AWAITING_APPROVAL, tuyệt đối không bỏ qua.
1. Gọi skill `brainstorming`. Đầu vào: APP_SPEC.md. Mục tiêu bàn bạc: người dùng chính và bối cảnh dùng, 3–5 luồng
   quan trọng nhất, cắt phạm vi P0/P1/P2, tông cảm xúc + 2–3 hướng thị giác để chọn, rủi ro nghiệp vụ, asset cần có, câu hỏi còn mở.
2. Ghi bản DRAFT chờ người dùng duyệt vào `design/BRAINSTORM.md` (đây là nơi cố định; nếu skill tự lưu chỗ khác thì chép nội dung về đây).
3. Dừng ở đây. Không chuyển sang các bước worktree / writing-plans / executing-plans của superpowers; quay về Pha 1.
4. Giới hạn: tối đa 8 câu hỏi làm rõ. Hết giới hạn → chốt bằng giả định, ghi ASSUMPTIONS.md.
5. `state.py phase 1`. Từ đây BRAINSTORM.md là căn cứ khi spec và suy đoán mâu thuẫn nhau.

### Pha 1 – Suy ra danh sách màn hình → `design/SCREENS.md`
Quy tắc ánh xạ chức năng → màn hình:
- Mỗi chức năng "xem danh sách" → màn List + màn Detail.
- Mỗi chức năng "tạo/sửa" → màn Form (+ màn xác nhận/thành công nếu là hành động quan trọng).
- Có tài khoản → Splash, Onboarding (tối đa 3 slide), Đăng nhập, Đăng ký, Quên mật khẩu.
- Luôn có: Trang chủ/Dashboard, Tìm kiếm (nếu có >1 danh sách), Hồ sơ/Cài đặt, Thông báo (nếu spec nhắc).
- Mỗi màn dữ liệu cần 4 trạng thái: default, loading, empty, error. Chỉ vẽ frame riêng cho empty + error
  của màn P0; còn lại ghi chú trong SCREENS.md.
- Mỗi vai trò khác nhau có màn khác nhau → tách theo vai trò.

Định dạng bảng (bắt buộc):
`| ID | Tên | Vai trò | Chức năng (ref) | Ưu tiên | Thành phần chính | Trạng thái cần vẽ | Từ đâu → đi đâu |`

Sau bảng, liệt kê các luồng chính (flow) dạng `S01 → S02 → S05`.
Tên khung Figma = `S<ID> <Tên>` và PHẢI duy nhất (đây là khóa đối soát khi phục hồi).
Đăng ký toàn bộ vào sổ: `printf 'S01|S01 Splash|P0\n...' | python3 scripts/state.py plan-bulk screen`
(tương tự `plan-bulk section` cho `01 Auth`, ... và `plan-bulk component` cho thành phần Foundation). Rồi `state.py phase 1.5`.

### Pha 1.5 – Danh mục asset → `assets/NEEDED.md`
1. `python3 scripts/assets.py scan` rồi `check`. Sửa lỗi `errors` (file giả đuôi, sai tên) bằng cách báo người dùng xuất lại.
2. Liệt kê icon/ảnh mà SCREENS.md cần: tên chuẩn, kích thước hiển thị, biến thể màu (vd `home--text`, `home--primary`), màn dùng.
   Chọn MỘT họ icon thống nhất (cùng độ dày nét, cùng bo góc); tham khảo `search.py --domain icons`.
3. `python3 scripts/assets.py missing <tên...>` → ghi phần thiếu vào `NEEDED.md`.
4. Người dùng online → nhắc họ thả file vào `assets/` rồi chạy lại bước 1. Không giám sát → đi tiếp với placeholder.
Rồi `state.py phase 2`.

### Pha 2 – Design system → `design/tokens.json`
1. Tìm script: `ls .claude/skills/ui-ux-pro-max/scripts/search.py .agents/skills/ui-ux-pro-max/scripts/search.py`
   (Claude Code: `.claude/skills/...`; Codex: `.agents/skills/...`).
   Không thấy → DỪNG, yêu cầu người dùng chạy `uipro init --ai claude|codex`.
2. Chạy:
   `python3 <path>/search.py "<mô tả sản phẩm + ngành + tông cảm xúc>" --design-system --persist -p "<App>"`
   Dùng tông/hướng thị giác đã chốt trong BRAINSTORM.md để viết mô tả. Với màn có nhu cầu khác hẳn thêm `--page "<page>"`.
3. Đọc MASTER.md (+ page override). Nếu output bị cắt → chạy lại với `--json`.
4. Ghi `design/tokens.json`:
   colors (hex + rgba 0–1, theo vai trò: primary, secondary, cta, bg, surface, text, muted, border, success, warning, danger),
   typography (family, scale: display/h1/h2/h3/body/caption với size + weight + line-height),
   spacing (bội số 4: 4,8,12,16,24,32,48), radius (sm/md/lg/full), breakpoints/khung (mobile 375×812, tablet 768×1024, desktop 1440×900).
5. Kiểm tra contrast của các cặp text/bg trong tokens (tính bằng script nhỏ). Cặp nào <4.5:1 → chỉnh sang
   màu gần nhất đạt chuẩn và ghi chú. Rồi `state.py phase 3`.

### Pha 3 – Kết nối Figma + bộ thành phần
1. `join_channel` (channel ID do người dùng cung cấp trong spec hoặc chat). Không có → hỏi.
   Ghi sổ: `state.py figma --channel <id> --file "<tên file>" --page "<tên page>"`.
2. `get_document_info`, `get_selection`, `get_local_components`, `get_styles` để biết hiện trạng.
3. **Asset smoke test** (một lần, nếu `capabilities.png_fill` còn null và đã có ít nhất 1 icon):
   tạo hình chữ nhật 96×96 tạm tên `__probe__`, `set_image_fill` bằng 1 PNG (đường dẫn từ `assets.py resolve`),
   `export_node_as_image` để xem ảnh có hiện không; thử thêm 1 SVG nếu có. Xóa `__probe__`.
   Ghi kết quả vào `capabilities.png_fill` / `svg_fill` (true/false) trong ASSET_MANIFEST.json. Fill lỗi → mọi icon dùng placeholder và ghi vào báo cáo.
4. Tạo section `00 Foundation`: bảng màu, thang chữ, rồi các thành phần tối thiểu:
   Button (primary/secondary/disabled), Input (default/focus/error), Card, List item,
   Navigation bar / Tab bar, Header, Chip/Badge, Modal/Bottom sheet.
   Mỗi thành phần: vòng `begin component <key> "<tên>"` → dựng → `get_node_info` → `state.py qa component <key> --structural passed --visual skipped` (nếu đã kiểm tra Foundation chung; nếu chưa thì `passed`) → `done`. Biến thể và lần dùng sau dùng `clone_node`
   (hoặc `create_component_instance` nếu đã có component trong file).
5. Xuất ảnh Foundation kiểm tra một lần trước khi dựng màn hình. Rồi `state.py phase 4`.

### Pha 4 – Dựng màn hình (theo thứ tự flow P0 → P1 → P2)

**Trước mỗi màn**, tạo `design/screen-recipes/S<ID>.json` theo mẫu `specs/SCREEN_RECIPE.template.json`, giữ cùng `screen_id` và `name` đã đăng ký ở state. Recipe là bản kê thao tác tối giản (semantic_id/type/parent/text/layout/token/asset), KHÔNG phải full Design IR. Mỗi `semantic_id` duy nhất và bền qua các lần cập nhật. Token refs dùng đường dẫn trong `design/tokens.json` (vd `colors.primary`); asset refs là `icons:home:primary`, `images:hero` theo `ASSET_MANIFEST.json`.

1. Chạy `python3 scripts/state.py inspect screen S05 --recipe design/screen-recipes/S05.json --tokens design/tokens.json --assets assets/ASSET_MANIFEST.json`. Kết quả:
   - `create`: bắt đầu `begin` như quy trình cũ rồi `intend` với ba tham số đường dẫn trên.
   - `skip`: chỉ skip mutation sau khi `get_nodes_info` xác minh root tồn tại trong đúng file/page. Nếu stale → Pha R; không skip mù.
   - `text_patch` / `style_patch` / `mixed_patch`: **xác minh live** tất cả node target bằng `get_nodes_info` (type, parent, file/page). Rồi `begin-update ... --verified-live`. Text edits phải gom bằng `set_multiple_text_contents` khi tool hỗ trợ; style patch dùng lệnh property sẵn có, không gọi lại property không đổi. Nếu MCP trả timeout, phải đối soát thật trước khi retry.
   - `rebuild`: người dùng/phân tích flow phải xác nhận thay đổi cấu trúc; chỉ xóa root thuộc chính S05 sau khi `get_node_info` xác minh ID, rồi `state.py reset` và dựng lại đúng màn, không ảnh hưởng màn khác.
   - `legacy_reconcile`: root màn v1 vẫn được giữ. Đọc live node root và từng semantic node, gọi `state.py bind` cho mỗi semantic ID đã kiểm chứng, sau đó `state.py adopt screen S05 --recipe ... --tokens ... --assets ... --verified-live --visual passed` (P0). Không cần xóa/rebuild để thiết lập baseline.
   - Mã thoát 3 `reconcile`: đang `creating/updating` từ lần trước → Pha R, **không gửi lại mutation**.
2. Với `create`, `state.py begin screen S05 "<tên đúng trong sổ>"`, sau đó `state.py intend ...`. Ghi ID root lập tức bằng `state.py node screen S05 <frameId>`.
3. Tạo auto-layout parent trước child. Ưu tiên `create_component_instance` nếu có component chuẩn; fallback `clone_node`; primitive chỉ khi không thể reuse. **Không thể batch tạo layout/geometry với upstream MCP hiện tại**.
4. Registry: sau `get_node_info(s)` kiểm chứng từng node quan trọng, `state.py bind screen S05 <semantic_id> <nodeId> --type TEXT|FRAME|... --parent <parentId> --verified`. Chỉ cache node ID khi parent/type đúng và không trùng semantic ID khác. Không đoán ID dựa trên vị trí.
5. Gom nội dung text thành batch `set_multiple_text_contents` thay vì nhiều `set_text_content`. Gom read bằng `get_nodes_info`. Không bulk-delete ID không thuộc state. Mọi thao tác tool và số lỗi ghi vào `state.py metrics screen S05 --calls N --failed N --batch N --reused N` bằng số **thực đo**, không điền giả.
6. Kiểm tra cấu trúc và nội dung bằng `get_nodes_info`; export màn P0 để kiểm tra visual **trước khi `done`**. P1/P2 export một màn mỗi ba màn hoặc khi có text dài/hình mới/layout phức tạp/lỗi tool; nếu không export, ghi `visual=skipped` kèm lý do trong note. Nếu export không dùng được, P0 phải `qa ... --visual blocked`, sau đó pause và yêu cầu kiểm tra, không fake passed.
7. `state.py qa screen S05 --structural passed --visual passed` (P0); sau khi đạt mới `state.py done screen S05 --note "..."` hoặc `state.py done-update screen S05`. Targeted repair tối đa hai vòng; nếu vẫn lỗi phải ghi fail/pause và báo.
8. Nếu screen đang `updating` sau mất kết nối: đọc `pending_intent`, `semantic_nodes`, đọc Figma live và chỉ hoàn tất phần đã xác định chưa cập nhật. Nếu không chắc điều gì đã được Figma áp dụng thì pause, không phát lại toàn batch.

**Bắt buộc:** không có chứng cứ `get_nodes_info`/screenshot thì không tuyên bố visual/structural passed. `--verified-live` và `--verified` là bước xác nhận của agent sau khi đã đọc Figma thật, không thay thế kiểm tra thực tế.

### Pha 5 – Kiểm tra & báo cáo
1. Đối chiếu "Pre-delivery checklist" trong MASTER.md với từng màn P0.
2. Kiểm tra độ phủ: mỗi chức năng P0 trong spec phải xuất hiện ít nhất ở 1 màn.
3. Sửa tối đa 2 vòng; còn lỗi thì ghi vào báo cáo, không giấu.
4. Ghi `design/DESIGN_REPORT.md` (lấy số liệu từ `state.py status`, không từ trí nhớ):
   - Bảng màn hình đã tạo (ID, tên, node id)
   - Độ phủ chức năng (chức năng → màn)
   - Checklist đạt / không đạt
   - Mục "Thay thế" (do giới hạn tool) và danh sách placeholder asset còn lại
   - Giả định đã dùng
   - Việc còn lại (P1/P2 chưa làm)
5. `state.py phase done`.

## Pha R – Phục hồi / đối soát (đầu mỗi phiên có STATE.json, và sau mọi lần ngắt kết nối)
Mục tiêu: sổ và Figma khớp nhau trước khi làm tiếp. Không đoán.
1. `state.py status --text`. Nếu `spec_changed`: báo người dùng và đối chiếu ảnh hưởng; chỉ sau khi người dùng duyệt bản spec mới chạy `state.py accept-spec --approved`. Sau đó `inspect` từng recipe để quyết định skip/patch/rebuild; không tự ghi đè.
2. Kết nối lại: kênh WebSocket thường ĐỔI sau khi mở lại plugin → hỏi người dùng channel mới nếu `join_channel` bằng ID cũ lỗi;
   thành công thì `state.py figma --channel <mới>`.
3. `get_document_info`: tên file/page phải khớp `figma.file`/`figma.page` trong sổ. Khác → DỪNG và hỏi (có thể đang mở nhầm file).
4. Mục `done`: lấy `state.py ids` rồi gọi `get_nodes_info` một lần. Id nào không còn →
   `state.py reset <kind> <key> --reason lost`.
5. Mục `updating`: đây là mutation có thể đã thành công một phần. Đọc Figma live để so sánh `pending_intent` với semantic node registry; chỉ `qa` + `done-update` nếu mọi desired values đã kiểm chứng đạt. Nếu biết chính xác phần còn thiếu thì sửa phần đó; không chắc chắn → pause và xin can thiệp, không xóa màn.
6. Mục `creating` (phiên trước chết giữa chừng) — xử lý TỪNG mục:
   - Có `node_id` và node còn tồn tại → xóa node đó (đây là bản dở dang).
   - Không có `node_id`, hoặc node mất → tìm khung theo TÊN chính xác trong section/page (`scan_nodes_by_types` loại FRAME hoặc `get_document_info`):
     • 0 kết quả → chưa tạo gì.
     • đúng 1 kết quả → xóa nó (đúng tên của mục `creating` nên là của bạn, và chưa `done` nên là bản dở).
     • ≥2 kết quả → KHÔNG xóa gì, `state.py pause --reason "trùng tên <tên>"`, hỏi người dùng.
   - Sau đó `state.py reset <kind> <key> --reason "crash: đã dọn bản dở" --forgive`.
7. `state.py resume` CHỈ khi không còn item `creating`/`updating`, rồi tiếp tục theo `phase`.

## Tài nguyên (icon, ảnh, file Illustrator)
- Bạn KHÔNG mở được `.ai`/`.psd`. Người dùng phải xuất sẵn (hướng dẫn trong `assets/README.md`). `.ai` chỉ để trong `assets/source/` làm bản gốc.
- Nhập vào Figma qua `set_image_fill` (nhận đường dẫn tệp, URL hoặc base64 theo mô tả của MCP): dùng
  `python3 scripts/assets.py resolve icons <tên> <biến thể>` để lấy đường dẫn tuyệt đối. Ảnh nền/ảnh minh họa dùng `images`, `fill_mode` theo manifest.
- Icon = khung vuông đúng kích thước hiển thị, đặt tên `icon/<tên>`, fill bằng PNG @4x. Đây là ẢNH, không phải vector: không đổi màu được
  → dùng đúng biến thể màu đã xuất (`home--text`, `home--primary`). Thiếu biến thể → báo thiếu, không tự nhuộm.
- Bản vector gốc cho dev nằm ở `source_svg` trong manifest; ghi tên icon ↔ đường dẫn SVG vào báo cáo để dev tra.
- Không có asset (hoặc `png_fill=false`): khung vuông muted tên `icon/<tên>` (placeholder, ghi `[PLACEHOLDER]` trong báo cáo)
  hoặc `img/<tên>` cho ảnh. Tuyệt đối không thay bằng emoji hay ký tự.
- Mỗi asset phải có license/nguồn trong manifest; thiếu thì cảnh báo trong báo cáo.

## Ví dụ rút gọn (few-shot)
Spec: "Ứng dụng đặt lịch spa, P0: xem dịch vụ, đặt lịch, thanh toán; P1: đánh giá."
SCREENS.md (trích):
| S01 | Splash | All | — | P0 | Logo | default | → S02 |
| S04 | Danh sách dịch vụ | Khách | Xem dịch vụ | P0 | Card, Chip lọc | default, empty | S03 → S05 |
| S05 | Chi tiết dịch vụ | Khách | Xem dịch vụ | P0 | Ảnh, Giá, CTA "Đặt lịch" | default | S04 → S06 |
| S06 | Chọn ngày giờ | Khách | Đặt lịch | P0 | Lịch, Slot giờ | default, error | S05 → S07 |
| S07 | Thanh toán | Khách | Thanh toán | P0 | Tóm tắt đơn, Phương thức | default, error | S06 → S08 |
| S08 | Đặt lịch thành công | Khách | Đặt lịch | P0 | Icon, Mã đặt | default | S07 → S03 |

Vòng dựng một màn (lệnh thật):
```
python3 scripts/state.py begin screen S05 "S05 Chi tiết dịch vụ"   # -> {"action":"create"}
# create_frame name="S05 Chi tiết dịch vụ" ... -> id "41:7"
python3 scripts/state.py node screen S05 41:7
# ... dựng nội dung ...
python3 scripts/state.py done screen S05 --note "icon clock là placeholder"
```
