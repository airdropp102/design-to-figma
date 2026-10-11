# NÉT — Áo dài đương đại · Design brief DRAFT

Status: DRAFT — chưa được người dùng duyệt.
Run: run-c52ba6489dae
APP_SPEC SHA-256: bd46d279737485807eb70873ec69582329ae3606a5968e8165d040f66177a32e

## Mục tiêu và đối tượng
Thiết kế website thời trang áo dài trên Figma cho khách hàng chủ yếu nữ 25–45 tuổi. Trải nghiệm giúp khám phá mẫu, chọn màu/size và gửi yêu cầu tư vấn hoặc đặt lịch thử. Thành công: từ trang chủ đến sản phẩm tối đa 2 thao tác, từ sản phẩm đến form tối đa 1 thao tác; có đường quay lại và phục hồi lỗi.

Không xây ứng dụng, không có quản trị, tài khoản, checkout hoặc thanh toán trong lần này.

## Ba hướng thị giác
1. Modern Ivory — đề xuất: nền trắng ngà, khoảng trắng rộng, tiêu đề ngắn, hình áo dài toàn thân và điểm nhấn đỏ rượu. Phù hợp nội dung kể chuyện và dữ liệu trong spec; hạn chế là chất lượng cảm xúc phụ thuộc ảnh thật.
2. Editorial Contrast: các chương nền sáng/tối xen kẽ và bố cục tạp chí. Cá tính hơn, cần bộ ảnh mạnh và kiểm tra tương phản cẩn thận.
3. Soft Vietnamese: be cát, sage và serif tiết chế. Mềm mại, gần gũi; cần phân biệt rõ các lớp nội dung để tránh nhạt.

Đề xuất chọn Modern Ivory. Màu/font đề xuất từ spec: #F7F5F0, #202020, #EAE4DA, CTA #722F37/chữ trắng; #B99A61 chỉ trang trí. Inter cho UI, Noto Serif cho tiêu đề editorial. Sau approval, UI UX Pro Max sinh MASTER phù hợp các ràng buộc này; mọi giá trị dùng trên canvas phải được ghi vào MASTER/tokens và kiểm tra contrast.

Tham chiếu đã đọc: https://www.apple.com/vn/iphone-duo/ . Chỉ tham khảo nhịp kể chuyện theo chương, điểm nổi bật và lựa chọn biến thể; không dùng nội dung/asset Apple.

## Phạm vi và sitemap
P0: Trang chủ → Bộ sưu tập → Danh sách áo dài → Chi tiết → Tư vấn/đặt lịch → Đã nhận yêu cầu. Menu mobile, gallery và bảng size là overlay. Lọc/sắp xếp thuộc danh sách.
P1: tìm kiếm, lookbook, câu chuyện thương hiệu chưa triển khai; điều hướng liên quan cần ghi chú ngoài phạm vi, không giả là flow đã hoàn tất.
P2: yêu thích, giỏ hàng/thanh toán loại khỏi prototype.

## Luồng chính
1. Trang chủ → Bộ sưu tập Dáng Việt → Chi tiết An Nhiên → chọn màu/size → Tư vấn → Đã nhận yêu cầu.
2. Danh sách → lọc/sắp xếp → Chi tiết; không có kết quả → Xóa bộ lọc → Danh sách.
3. Trang chủ → Đặt lịch thử → thông tin/ngày/giờ → Đã nhận yêu cầu.
4. Chi tiết → Gallery hoặc Bảng size → đóng → Chi tiết giữ lựa chọn.
5. Form lỗi trường hoặc gửi thất bại → sửa/thử lại → Đã nhận yêu cầu.

## Trang chủ
Giữ đủ 9 chương của spec: header, hero “Nét Việt. Dáng hôm nay.” với 2 CTA; bộ sưu tập Dáng Việt; ba điểm phom/chất liệu/chi tiết; câu chuyện chất liệu; chọn màu có tên và dấu chọn; 4 sản phẩm tuyển chọn; đặt lịch thử; footer có nhãn thông tin demo. Không dùng slider tự chạy, chữ không đặt trên ảnh khó đọc, hero giữ toàn bộ tà áo.

## Responsive và giới hạn 25 màn
6 màn default × 3 kích thước desktop 1440/tablet 768/mobile 390 = 18 frame.
3 overlay: menu mobile, gallery, bảng size = 3 frame.
4 bảng trạng thái P0 = 4 frame: (1) loading/empty/error của bộ sưu tập và danh sách; (2) loading/error gallery và biến thể unavailable; (3) loading/error nội dung trang chủ và xác nhận; (4) lỗi trường/gửi thất bại/đang gửi của form.
Tổng 25 root frame. Mỗi bảng trạng thái chứa các ví dụ con được đặt tên, kiểm tra riêng; không coi bảng có tên là đã đủ state. Nếu cần tách nhiều root hơn, phải chia lần chạy và báo phần còn lại.
Desktop: 12 cột/max-width 1200, sản phẩm 4 cột. Tablet/mobile: 2 cột, giảm 1 cột khi nội dung không đủ chỗ. Ghi quy tắc xuống 320px. Touch target ≥44×44, body ≥16px; CTA mobile giữ khoảng đệm tránh che nội dung.

## Nghiệp vụ và nội dung
Giá, sản phẩm, chất liệu, bảng size và thương hiệu là demo. Bán sẵn và đặt may theo trạng thái từng mẫu trong spec. CTA ưu tiên tư vấn/đặt lịch; không mua ngay.
Họ tên/điện thoại bắt buộc. Cho phép “Cần tư vấn size”. Ngày không quá khứ. Gửi thành công chỉ xác nhận nhận yêu cầu, không xác nhận lịch. Gửi lỗi giữ dữ liệu. Size M/hồng phấn của Ngọc Sương có trạng thái hết hàng và đường hỏi tư vấn.

## Asset và giới hạn Figma
Không có ảnh đã duyệt: chỉ dùng placeholder ghi rõ; không tìm/tải/tự vẽ asset. Cần hero editorial toàn thân, ảnh bộ sưu tập, ảnh từng điểm nổi bật, texture và 4 ảnh mỗi sản phẩm. Icon chỉ từ manifest; thiếu dùng placeholder hoặc nhãn chữ cho thao tác.
Figma đích do người dùng cung cấp: Untitled, key rXrX1FHInMsxbejkvSP9Wl, Page 1 0:1, channel lưu local. MCP đọc được page nhưng chưa cung cấp live file key/name. Phải giải quyết identity/writer ownership/WAL trước mutation.
Page Brief/Foundations/Components/Desktop/Mobile/Tablet/Prototype là yêu cầu spec; chỉ tạo page/component variants/styles nếu schema thực tế hỗ trợ. Nếu thiếu, đề xuất section có tên tương ứng, clone và giá trị trực tiếp/layer token, ghi rõ thay thế trong bàn giao.
Interactive prototype chưa được xác minh hỗ trợ. Nếu thiếu tool, bàn giao sơ đồ và chú thích tương tác; nghiệm thu prototype vẫn ghi chưa đạt, không tự coi flow diagram là prototype.

## QA và giả định chờ duyệt
Kiểm tra structural cho mọi root và state; xuất ảnh và kiểm tra visual P0 trước done. Contrast ≥4.5:1, không tràn ngang, focus/swatches rõ, demo labels, giữ lựa chọn và đường quay lại nhất quán. Targeted repair tối đa 2 vòng.
Giả định chờ duyệt: tên NÉT, Modern Ivory, giá/chất liệu demo, CTA tư vấn/đặt lịch, placeholder asset, phạm vi chỉ P0, tổ chức 25 root frame như trên. Thông tin liên hệ/chính sách chưa có dùng nhãn demo.

## Approval
Chưa có approval. Người dùng duyệt đúng brief này và digest APP_SPEC; thay đổi brief/spec phải được đối chiếu trước khi ghi approval.
