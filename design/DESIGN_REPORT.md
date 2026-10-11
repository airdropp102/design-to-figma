# NET — Bàn giao tạm một màn hình

## Playable prototype wiring — applied
Channel oy9qymp2, Prototype plugin1.0.0:22 live reactions wired and independently read back across S28–S31. Homepage/detail have900px vertical scrolling viewports. Reverified131 nodes; exported and inspected all four viewports, saved under design/previews/*-prototype-viewport.png. First home export timed out; one retry after identity reconcile succeeded. Demo flow and Play URL in MOTION_PROTOTYPE.md. Playback click-through not independently tested; static color controls, sample-only appointment fields and no true3D remain limitations. Original full-spec coverage still incomplete.

## Editable Fashion v2 rebuild
S28 `69:204`, S29 `69:286`, S30 `69:310`, S31 `69:328`: editable visual layouts done,131 nodes in total read live with correct type/parent/text/image fills and containment, four exported PNGs inspected. Product pictures are separate AI concepts, not rasterized UI. Appointment fields are sample-only, not editable inputs/submission. No prototype reactions applied yet; local tested prototype plugin/MCP prepared, waiting for plugin reconnect. State has7 done visual roots, original full P0/state delivery still incomplete. See MOTION_PROTOTYPE.md and PROTOTYPE_INTENT.json.

Motion request: user accepted Fashion v2 visual direction on 2026-10-11 and requested a playable animated/3D prototype. This is not implemented. Current MCP cannot write prototype reactions/transitions; S27 is raster. See `design/MOTION_PROTOTYPE.md`. No prototype success or interaction QA is claimed.

## Cập nhật 2026-10-11 — Fashion v2 DRAFT
Theo yêu cầu mới, đã tạo ảnh campaign áo dài bằng image_gen và bản preview raster toàn trang với hero tràn khung, gallery bất đối xứng, khối chất liệu lớn, lưới sản phẩm không viền. Xem `design/FASHION_V2_DRAFT.md`, `design/IMAGE_PROMPTS.md`, `design/previews/NET-gallery-fashion-v2-draft.png`. Manifest hiện có 1 ảnh AI minh họa; các đoạn nói manifest trống bên dưới mô tả thời điểm dựng các root cũ.

Chưa cập nhật canvas: TalkToFigma phiên này thiếu tool `set_image_fill`, dù server dự án có đăng ký tool. Đã kiểm chứng live đúng file/page qua channel rvu4uiiw; không mutation, không đánh dấu QA/hoàn thành cho bản mới. State tạm dừng chờ nạp lại MCP. Preview là DRAFT thị giác; ảnh sản phẩm, màu SKU và nội dung nhỏ cần đối chiếu khi dựng layer. S01/S26 vẫn giữ nguyên.

Phạm vi: theo yêu cầu người dùng, chỉ dựng S01 Trang chủ — Desktop. Bộ 25 màn chưa hoàn tất.

| ID | Tên | Node | Trạng thái |
|---|---|---|---|
| S01 | Trang chủ — Desktop | 67:2 | done; structural/visual passed |

Root 1440×5948. Nội dung: header, hero với hai CTA; Dáng Việt; ba điểm phom/chất liệu/chi tiết; câu chuyện chất liệu; lựa chọn màu có tên/nhãn chọn; 4 sản phẩm; đặt lịch; footer demo.

## Kiểm chứng
Đọc đúng file Untitled/key rXrX1FHInMsxbejkvSP9Wl/Page 1 0:1 từ plugin identity 1.0.0. Root creation + live read xác minh quyền ghi. Writer lock giữ trong toàn phiên mutation. get_node_info/get_nodes_info xác minh 100 node và 99 child bindings, type/parent/text đúng; bounding boxes không tràn khung cha. Export PNG đã kiểm tra visual: design/previews/S01-desktop.png. 7 cặp contrast tokens ≥4.5:1. Kiểm tra harness: 49 tests passed; plugin identity behavior test passed.

## Thay thế và giới hạn
Ảnh đều là placeholder; manifest chưa có asset. Không có prototype, click không điều hướng; P0 flows chưa đạt nghiệm thu. Swatch tạm là button có tên màu và nhãn chọn; chưa có ảnh khi đổi màu. Font Inter thay cho Noto Serif editorial do tool không nhận fontFamily. Không tạo page/variants/variables/styles do schema thiếu; chỉ dựng một root trong Page 1. Nav Câu chuyện thuộc P1 chưa có màn đích. Không có nguồn/license ảnh thật vì chưa dùng ảnh.

## Sửa gate
Plugin local giữ upstream checkout nguyên vẹn, bổ sung live file name/key/editor/mode, bật private API trong manifest. Controller chỉ miễn yêu cầu WAL reconcile cho đúng một root probe rỗng, registered, live verified tại figma_ready. Không replay create hoặc cho phép update WAL qua gate.

## Việc còn lại
24 root màn/state, foundation/components, mobile/tablet, interaction/prototype, ảnh thật, P0 flow/state QA tổng thể. Workflow giữ DESIGN_EXECUTION, chưa đánh dấu toàn bộ sản phẩm complete.


## Gallery Monochrome — bản thử chờ duyệt
Người dùng chưa duyệt màn Modern Ivory; approval ban đầu là brief, không phải acceptance màn hình. Theo lựa chọn mới, dựng S26 Gallery Monochrome [DRAFT] tại node67:102 cạnh S01. Cả hai là concept; không tự xem hướng mới là thiết kế đã được duyệt.

Palette trắng #FAFAFA/đen #171717/xám #E5E5E5/cobalt #3155D9; Inter; booking nền đen và CTA trắng; layout gọn hơn, root1440×5536. Token/override riêng: design/tokens.gallery.json và design-system/net/pages/gallery-monochrome.md. 100 node đọc live, đúng type/parent/text, không overflow; PNG đã xem tại design/previews/S26-gallery-monochrome.png. 6 cặp contrast≥4.5:1. Không thay S01, không ảnh thật hoặc prototype.

Chỉ 2 root đã dựng trong run, giới hạn25 rendered roots vẫn được giữ. Nếu tiếp tục bộ25 màn gốc, concept bổ sung tiêu thụ một slot và một root phải chuyển sang lần chạy sau.


## MCP reloaded — 2026-10-11
set_image_fill is now exposed and tested successfully. Live identity reverified, existing done roots reconciled, writer lock held. S27 static raster preview created at 69:202, image child 69:203 (IMAGE/FIT), beside S01/S26. Root/child structure verified and exported PNG visually reviewed; png_fill=true. This QA covers image placement only, not individual UI semantics, contrast, exact SKU/color fidelity or interaction. Editable Fashion v2 layout and interactive prototype remain unfinished. Three rendered roots so far; respect 25-root limit on continuation.


## Completed An Nhiên image turntable

16 editable states, 2 colors × 8 approximate angles, all exported and visually inspected. 81 prototype reactions applied and freshly read back via TalkToFigma. Color changes retain angle; previous/next wrap. Selected color has no self-navigation. Existing detail entry now opens S32; appointment overlay and home remain connected. Original flow is preserved. AI inferred views, not continuous3D or verified garment geometry. Browser Play was not independently click-tested. State:23 done,40 original-scope pending; current trial complete, full APP_SPEC remains incomplete. Export recovered without a proven root-cause fix; diagnostics retained.

Play: https://www.figma.com/proto/rXrX1FHInMsxbejkvSP9Wl/Untitled?page-id=0%3A1&node-id=81-2&starting-point-node-id=81%3A2&scaling=scale-down&content-scaling=fixed

| Screen | Root ID |
|---|---|
| S32 | 81:2 |
| S33 | 81:24 |
| S34 | 81:46 |
| S35 | 81:68 |
| S36 | 81:90 |
| S37 | 81:112 |
| S38 | 81:134 |
| S39 | 81:156 |
| S40 | 81:178 |
| S41 | 81:200 |
| S42 | 81:222 |
| S43 | 81:244 |
| S44 | 81:266 |
| S45 | 81:288 |
| S46 | 81:310 |
| S47 | 81:332 |

Evidence: ROTATION_LIVE_REACTIONS.json; ROTATION_VISUAL_QA.json; previews/S32..S47-rotation.png; S29-rotation.png.
