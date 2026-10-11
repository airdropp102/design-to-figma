# SCREENS — NET P0

25 root frame, mọi root đều P0. Các bảng state có các ví dụ con phải được kiểm chứng riêng.

| ID | Tên | Vai trò | Chức năng (ref) | Ưu tiên | Thành phần chính | Trạng thái cần vẽ | Từ đâu → đi đâu |
|---|---|---|---|---|---|---|---|
| S01 | S01 Trang chủ — Desktop | Khách | 1 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S02 | S02 Bộ sưu tập — Desktop | Khách | 2 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S03 | S03 Danh sách áo dài — Desktop | Khách | 3 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S04 | S04 Chi tiết áo dài — Desktop | Khách | 4 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S05 | S05 Tư vấn và đặt lịch — Desktop | Khách | 5 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S06 | S06 Đã nhận yêu cầu — Desktop | Khách | 5 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S07 | S07 Trang chủ — Mobile | Khách | 1 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S08 | S08 Bộ sưu tập — Mobile | Khách | 2 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S09 | S09 Danh sách áo dài — Mobile | Khách | 3 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S10 | S10 Chi tiết áo dài — Mobile | Khách | 4 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S11 | S11 Tư vấn và đặt lịch — Mobile | Khách | 5 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S12 | S12 Đã nhận yêu cầu — Mobile | Khách | 5 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S13 | S13 Trang chủ — Tablet | Khách | 1 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S14 | S14 Bộ sưu tập — Tablet | Khách | 2 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S15 | S15 Danh sách áo dài — Tablet | Khách | 3 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S16 | S16 Chi tiết áo dài — Tablet | Khách | 4 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S17 | S17 Tư vấn và đặt lịch — Tablet | Khách | 5 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S18 | S18 Đã nhận yêu cầu — Tablet | Khách | 5 | P0 | Header, nội dung, CTA, Footer | default | Xem flow bên dưới |
| S19 | S19 Menu mobile | Khách | 1 | P0 | Điều hướng, Đóng | open | Xem flow bên dưới |
| S20 | S20 Gallery ảnh | Khách | 4 | P0 | Ảnh placeholder, Trước/Sau, Đóng | open | Xem flow bên dưới |
| S21 | S21 Bảng size | Khách | 4 | P0 | Bảng demo, Cần tư vấn size, Đóng | open | Xem flow bên dưới |
| S22 | S22 States bộ sưu tập và danh sách | Khách | 2,3 | P0 | Skeleton; Không kết quả/Xóa bộ lọc; Lỗi/Thử lại | loading, empty, error | Xem flow bên dưới |
| S23 | S23 States chi tiết và gallery | Khách | 4 | P0 | Skeleton; Lỗi nội dung/ảnh; Size hết hàng/Hỏi về mẫu này | loading, error, unavailable | Xem flow bên dưới |
| S24 | S24 States trang chủ và xác nhận | Khách | 1,5 | P0 | Skeleton, Lỗi nội dung/Thử lại | loading, error | Xem flow bên dưới |
| S25 | S25 States form tư vấn | Khách | 5 | P0 | Đang gửi; Lỗi trường; Gửi lỗi giữ dữ liệu | loading, error, invalid | Xem flow bên dưới |

## Flows
Desktop: S01 → S02 → S04 → S05 → S06; S03 → S04; S03 → S22 → S03; S01 → S05 → S06.
Mobile: S07 → S08 → S10 → S11 → S12; S09 → S10; S07 ↔ S19.
Tablet: S13 → S14 → S16 → S17 → S18; S15 → S16.
Gallery/size: S04/S10/S16 ↔ S20/S21, giữ lựa chọn. Error/unavailable: S04/S10/S16 ↔ S23. Form errors: S05/S11/S17 ↔ S25; success không khẳng định lịch hẹn. S24 minh họa lỗi/skeleton của trang chủ/xác nhận.

## State coverage
S22: riêng bộ sưu tập và danh sách đều có skeleton, empty và error. S23: chi tiết/gallery loading, error nội dung, ảnh lỗi placeholder, biến thể size M hồng phấn không có. S24: trang chủ và xác nhận loading/error. S25: tên trống, điện thoại không hợp lệ, ngày quá khứ, đang gửi ngăn gửi lặp, lỗi gửi giữ dữ liệu. Các root default giữ state thành công/biến thể theo spec. Mỗi ví dụ con có tên/semantic ID riêng; hình ảnh và nội dung mặc định không đồng nghĩa QA state.

## Responsive
Desktop 1440/max content 1200/12 cột/4 card; tablet 768/2 card; mobile 390/2 card, 320 dùng 1 card nếu cần. Touch target 44, body 16. Sticky CTA có padding và nhường bàn phím; chú thích chuyển layout.

## Limitations
Tool chưa hỗ trợ create_page, component variants, style/variables, prototype links. Dùng sections theo page yêu cầu và clone/direct tokens khi gate mutation đạt. Prototype requirement vẫn chưa đạt khi không có tool. P1/P2 không được tính hoàn thành.


## Concept bổ sung do người dùng chọn
S26 Trang chủ — Gallery Monochrome [DRAFT], desktop1440, node67:102; alternative của S01, không bổ sung chức năng. Chưa được người dùng duyệt màn. S01 giữ nguyên để so sánh. Giới hạn25 root đã dựng/lần chạy vẫn áp dụng, bản concept này tiêu thụ một slot.
