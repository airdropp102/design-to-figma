# Chaos test: kiểm tra phục hồi sau khi bị ngắt

Chạy trên brief B01 (8–10 màn). Mục tiêu: sau MỖI sự cố, tiếp tục được mà không làm trùng và không làm lại màn đã xong.

| ID | Sự cố gây ra | Khi nào gây | Kỳ vọng |
|---|---|---|---|
| C1 | Tắt `bun socket` | Giữa lúc dựng màn thứ 3 | Agent dừng sau ≤ 2 lỗi, `state.py pause`. Bật lại socket, mở plugin, nói "tiếp tục": Pha R chạy, màn 3 dựng lại từ đầu, màn 1–2 giữ nguyên |
| C2 | Đóng plugin Figma rồi mở lại (channel đổi) | Giữa màn thứ 4 | Agent hỏi channel mới, `figma --channel` được cập nhật, không tạo lại màn 1–3 |
| C3 | `kill -9` tiến trình agent | Sau `create_frame`, trước `done` | Phiên mới: `begin` trả mã 3, Pha R xóa đúng 1 khung dở (theo nodeId hoặc theo tên) rồi dựng lại |
| C4 | `kill -9` ngay sau `begin`, trước `create_frame` | — | Pha R tìm theo tên thấy 0 khung → reset và dựng, không xóa gì |
| C5 | Sửa `APP_SPEC.md` giữa hai phiên | Giữa Pha 4 | Agent báo `spec_changed` và HỎI, không tự dựng lại |
| C6 | Mở nhầm file Figma khác | Đầu phiên mới | Pha R bước 3 phát hiện tên file không khớp, dừng và hỏi |
| C7 | Xóa tay một màn đã `done` trong Figma | Giữa hai phiên | `get_nodes_info` báo thiếu id, màn đó được `reset lost` và dựng lại, màn khác giữ nguyên |
| C8 | Tạo tay 2 khung cùng tên với mục `creating` | Trước Pha R | Agent KHÔNG xóa gì, `pause`, hỏi người dùng |

## Chỉ số đạt
- Số khung trùng tên `S<ID>` trong Figma sau mọi sự cố: **0**
- Số màn `done` bị dựng lại không cần thiết: **0** (C7 chỉ dựng lại đúng màn bị xóa)
- Số khung dở dang còn sót trong Figma: **0**
- Agent dừng trong ≤ 2 lệnh lỗi sau C1: **có**
- `STATE.json` luôn parse được (kể cả sau `kill -9`): **có** (ghi tệp tạm rồi đổi tên nguyên tử)

## Kiểm tra nhanh trong Figma
Sau mỗi sự cố, đếm khung theo tên: mỗi `S<ID>` chỉ xuất hiện đúng 1 lần. So số khung `done` trong `state.py status` với số khung thực tế.

## Chaos v2 — incremental patch (TalkToFigma-only)

| ID | Sự cố | Kỳ vọng |
|---|---|---|
| C9 | Sau batch text được Figma áp dụng, trước `done-update` thì kill agent | Màn ở `updating`; phiên mới không tự phát lại batch, đọc live node, xác minh rồi commit |
| C10 | User xóa semantic text node sau khi `done` | ID stale bị phát hiện bằng `get_nodes_info`; không patch node khác theo tên gần đúng |
| C11 | User di chuyển node đã cache sang parent khác | Bỏ cache ID / pause; không cập nhật nhầm vị trí |
| C12 | APP_SPEC đổi và người dùng chưa duyệt | `accept-spec` không được gọi, không tự rebuild |
| C13 | Visual export P0 lỗi | `qa.visual=blocked` và `done` bị từ chối |
| C14 | Nhiều semantic IDs ánh xạ cùng node | `bind` từ chối; không dùng cache mơ hồ |
| C15 | Agent thứ hai định ghi canvas song song | Từ chối theo AGENTS.md (one-writer); không tin state lock là lock Figma |
