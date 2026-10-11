# APP_SPEC — Figma Design Agent Only

> Phạm vi: thiết kế UI/UX website áo dài trên Figma. Không sinh mã nguồn, không xây dựng hoặc triển khai website. Không đưa channel ID/token vào file.
> Đây là spec đề xuất để duyệt. Tên thương hiệu, tên bộ sưu tập, sản phẩm và giá dưới đây là dữ liệu demo, không phải thông tin kinh doanh đã xác nhận.

## Thông tin chung
- Tên ứng dụng: NÉT — Áo dài đương đại (tên thương hiệu đề xuất).
- Mục tiêu sản phẩm: giới thiệu áo dài như một sản phẩm thời trang hiện đại, giúp khách khám phá thiết kế, chọn mẫu phù hợp và gửi yêu cầu tư vấn/đặt lịch thử.
- Mô tả ứng dụng: website thương hiệu áo dài cao cấp kết hợp trải nghiệm khám phá bộ sưu tập và danh mục sản phẩm. Trang chủ là một câu chuyện thị giác dài, dẫn dắt từ vẻ đẹp tổng thể đến phom dáng, chất liệu, chi tiết may và sản phẩm cụ thể.
- Nền tảng: web, responsive cho desktop, tablet và mobile.
- Ngôn ngữ giao diện: Tiếng Việt.
- Đối tượng sử dụng: khách hàng yêu thời trang Việt, chủ yếu nữ 25–45 tuổi, tìm áo dài dự sự kiện, cưới hỏi, lễ Tết hoặc sử dụng trong công việc.
- Quy ước giao diện: responsive web; ưu tiên trải nghiệm mobile, đồng thời giữ bố cục giàu hình ảnh trên desktop.
- Tham chiếu phong cách: https://www.apple.com/vn/iphone-duo/ — tham khảo cách tổ chức nội dung sản phẩm theo từng chương, tiêu đề ngắn, hình ảnh chủ đạo, các điểm nổi bật và lựa chọn biến thể. Chuyển tinh thần này sang thời trang với khoảng trắng rộng, ảnh editorial và nhịp cuộn có chủ đích. Không dùng logo, nội dung hay hình ảnh của Apple.
- Tiêu chí thành công: khách nhận diện được thương hiệu và bộ sưu tập ngay màn hình đầu; từ trang chủ đến sản phẩm tối đa 2 thao tác; từ chi tiết sản phẩm đến biểu mẫu tư vấn tối đa 1 thao tác; các flow P0 không có điểm cụt trong prototype.

## Vai trò người dùng
| Vai trò | Mục tiêu chính |
|---|---|
| Khách hàng | Khám phá bộ sưu tập, xem mẫu áo dài, kiểm tra màu/size/giá tham khảo và gửi yêu cầu tư vấn hoặc đặt lịch thử. |
| Quản trị viên | Quản lý nội dung bộ sưu tập, sản phẩm và yêu cầu tư vấn ở giai đoạn sau. Không thiết kế giao diện quản trị trong phạm vi hiện tại. |

## Chức năng
| # | Chức năng | Vai trò | Ưu tiên (P0/P1/P2) | Mô tả ngắn / quy tắc nghiệp vụ |
|---|---|---|---|---|
| 1 | Trang chủ thương hiệu | Khách hàng | P0 | Hero ảnh/video áo dài, thông điệp ngắn, CTA “Khám phá bộ sưu tập” và “Đặt lịch thử”; kể chuyện về phom dáng, chất liệu và chi tiết may. |
| 2 | Khám phá bộ sưu tập | Khách hàng | P0 | Xem bộ sưu tập và các sản phẩm thuộc bộ sưu tập; luôn có đường quay về trang chủ. |
| 3 | Danh sách sản phẩm | Khách hàng | P0 | Card có ảnh, tên, giá tham khảo và màu; lọc theo dịp mặc, khoảng giá, size; sắp xếp theo mới nhất hoặc giá. |
| 4 | Chi tiết sản phẩm | Khách hàng | P0 | Gallery ảnh toàn thân, sau lưng và cận chất liệu; chọn màu/size; xem phom dáng, thành phần vải mẫu, hướng dẫn bảo quản và bảng size. Giá ghi rõ là giá demo/tham khảo. |
| 5 | Tư vấn và đặt lịch thử | Khách hàng | P0 | Form gồm họ tên, điện thoại, nhu cầu; đặt lịch thêm ngày và khung giờ mong muốn. Sản phẩm/màu/size được điền từ lựa chọn trước đó. Gửi thành công chỉ xác nhận đã nhận yêu cầu, chưa xác nhận lịch hẹn. |
| 6 | Tìm kiếm sản phẩm | Khách hàng | P1 | Tìm theo tên sản phẩm hoặc bộ sưu tập; có gợi ý và trạng thái không tìm thấy. |
| 7 | Lookbook | Khách hàng | P1 | Bộ ảnh editorial theo dịp mặc; từ ảnh có thể mở sản phẩm liên quan. |
| 8 | Câu chuyện thương hiệu | Khách hàng | P1 | Giới thiệu quan điểm thiết kế và quy trình may bằng nội dung demo; không bịa chứng nhận, số năm hoạt động hoặc cam kết chưa xác nhận. |
| 9 | Danh sách yêu thích | Khách hàng | P2 | Đánh dấu và xem lại mẫu yêu thích; không đưa vào prototype P0. |
| 10 | Giỏ hàng và thanh toán | Khách hàng | P2 | Dành cho giai đoạn bán trực tuyến; chưa thiết kế checkout, thanh toán, tài khoản hay theo dõi đơn hàng. |

## Yêu cầu design states và flow
- UI states áp dụng cho P0:
  - Default: trang chủ, bộ sưu tập, danh sách, chi tiết và biểu mẫu.
  - Loading: skeleton danh sách/gallery; nút gửi có tiến trình và không cho gửi lặp.
  - Empty: không có sản phẩm phù hợp bộ lọc; CTA “Xóa bộ lọc”.
  - Error: tải nội dung thất bại có “Thử lại”; ảnh lỗi có placeholder; lỗi từng trường form; gửi thất bại giữ nguyên dữ liệu.
  - Success: đã nhận yêu cầu tư vấn/đặt lịch, có “Tiếp tục khám phá”.
  - Unavailable: biến thể hết hàng hoặc size không có; giải thích rõ và cho phép “Hỏi về mẫu này”.
- Các flow chính cần có bản thiết kế:
  1. Trang chủ → bộ sưu tập → chi tiết → chọn màu/size → gửi yêu cầu tư vấn → thành công.
  2. Danh sách → lọc/sắp xếp → chi tiết; nhánh không có kết quả → xóa bộ lọc.
  3. Trang chủ → đặt lịch thử → điền thông tin/ngày/khung giờ → gửi → đã nhận yêu cầu.
  4. Chi tiết → mở gallery/bảng size → đóng → tiếp tục tư vấn, giữ lựa chọn trước đó.
  5. Form không hợp lệ hoặc gửi lỗi → sửa/thử lại → thành công.
- Cần interactive prototype: có, nếu tool hỗ trợ. Liên kết các flow P0, thao tác quay lại/đóng overlay và nhánh lỗi. Nếu tool không hỗ trợ, bàn giao sơ đồ flow và chú thích tương tác.
- Form: điện thoại bắt buộc, họ tên bắt buộc; lỗi hiển thị cạnh trường. Ngày mong muốn không nằm trong quá khứ. Việc cho phép gửi khi chưa chọn size được hỗ trợ bằng lựa chọn “Cần tư vấn size”.

### Cấu trúc trang chủ bắt buộc
1. Header tối giản: logo chữ NÉT, Bộ sưu tập, Áo dài, Câu chuyện; CTA Đặt lịch thử. Mobile dùng menu thu gọn.
2. Hero: ảnh mẫu mặc áo dài toàn thân, không cắt mất tà áo; headline “Nét Việt. Dáng hôm nay.”; mô tả một câu và 2 CTA. Không dùng slider tự chạy.
3. Bộ sưu tập chủ đạo “Dáng Việt”: ảnh lớn và lời giới thiệu ngắn.
4. Ba điểm nổi bật: phom dáng, chất liệu, chi tiết — mỗi điểm có ảnh minh họa riêng và nội dung cụ thể.
5. Câu chuyện chất liệu: ảnh cận bề mặt vải, chuyển tiếp sang ảnh áo dài trên người; nội dung đọc được khi không có animation.
6. Lựa chọn màu sắc: swatch có tên màu, trạng thái được chọn và ảnh tương ứng; không chỉ dùng màu để biểu đạt lựa chọn.
7. Sản phẩm tuyển chọn: 4 card và CTA “Xem tất cả áo dài”.
8. Khối đặt lịch thử: lời mời ngắn, CTA rõ ràng.
9. Footer: điều hướng, liên hệ và chính sách. Thông tin liên hệ/chính sách chưa có dùng nhãn “Thông tin demo”, không tạo địa chỉ, hotline hoặc điều khoản giả như thông tin thật.

### Phạm vi màn hình và responsive
- Thiết kế P0: trang chủ, bộ sưu tập/danh sách, chi tiết, form tư vấn/đặt lịch và xác nhận thành công; overlay menu mobile, gallery và bảng size; các state nêu trên.
- Frame chuẩn: desktop 1440px, tablet 768px, mobile 390px; ghi quy tắc co giãn xuống 320px, không tràn ngang.
- Desktop: lưới 12 cột, vùng nội dung tối đa 1200px; sản phẩm 4 cột. Tablet 2 cột; mobile 2 cột, chuyển 1 cột khi nội dung không đủ chỗ.
- Trang chủ desktop có section ảnh tràn chiều rộng xen kẽ section giới hạn nội dung; mobile giảm khoảng cách và kích thước chữ, vẫn giữ trọn phom áo.
- Chi tiết mobile có CTA tư vấn cố định cuối màn hình, không che nội dung hoặc bàn phím.

## Dữ liệu mẫu
> Toàn bộ dữ liệu sau là demo phục vụ thiết kế. Giá tính bằng VND; thành phần chất liệu phải xác nhận trước khi dùng thật.

| Mã | Tên sản phẩm | Bộ sưu tập / dịp mặc | Chất liệu mẫu | Màu | Size | Giá tham khảo | Trạng thái mẫu |
|---|---|---|---|---|---|---|---|
| NET-001 | Áo dài An Nhiên | Dáng Việt / công sở, gặp gỡ | Lụa satin | Trắng ngà, xanh sage | S, M, L | 2.490.000₫ | Có sẵn |
| NET-002 | Áo dài Ngọc Sương | Dáng Việt / lễ Tết | Organza, lớp lót mềm | Hồng phấn, trắng ngọc | S, M, L | 3.290.000₫ | Size M hồng phấn hết hàng |
| NET-003 | Áo dài Hạ Miên | Sắc Mùa / dạo phố, chụp ảnh | Linen pha | Be cát, xanh nhạt | S, M, L, XL | 1.890.000₫ | Có sẵn |
| NET-004 | Áo dài Diễm Châu | Khoảnh Khắc / lễ cưới, sự kiện | Gấm jacquard | Đỏ rượu, vàng champagne | S, M, L | 4.590.000₫ | Tư vấn đặt may |
| NET-005 | Áo dài Mộc Lan | Sắc Mùa / sự kiện | Crepe | Đen, trắng ngà | S, M, L | 2.790.000₫ | Có sẵn |

- Mô tả mẫu NET-001: “Phom áo thanh thoát, cổ đứng gọn và tà dài mềm mại. Dễ phối cùng quần sáng màu cho những cuộc gặp quan trọng.”
- Bảng size demo theo vòng ngực/vòng eo/vòng mông (cm): S 82/64/88; M 86/68/92; L 90/72/96; XL 94/76/100. Ghi rõ là bảng mẫu, không bảo đảm vừa vặn và chưa phải thông số thương hiệu.
- Ảnh cần có cho mỗi sản phẩm: toàn thân mặt trước, mặt sau, chi tiết cổ/tay và chất liệu; đồng nhất ánh sáng và màu vải giữa các ảnh.

## Ràng buộc
- Màu thương hiệu đề xuất: nền trắng ngà #F7F5F0, chữ chính #202020, nền phụ #EAE4DA, CTA chính đỏ rượu #722F37 với chữ trắng. Vàng champagne #B99A61 chỉ dùng trang trí, không mặc định dùng cho chữ nhỏ.
- Font được phép: Inter cho giao diện/nội dung; Noto Serif cho một số tiêu đề editorial. Kiểm tra đầy đủ dấu tiếng Việt; tối đa 2 họ font. Không phụ thuộc font độc quyền của Apple.
- Dark mode: không ở giai đoạn này. Có thể dùng một section nền tối để tôn ảnh, không đồng nghĩa với dark mode.
- Accessibility: contrast chữ thường tối thiểu 4.5:1; touch target mobile tối thiểu 44×44px; body text tối thiểu 16px; focus rõ; nhãn cho icon/swatches; thao tác bằng bàn phím; không đặt chữ lên vùng ảnh khó đọc.
- Motion: fade/reveal nhẹ, chuyển ảnh màu và mở overlay; có biến thể reduced motion. Không ép cuộn, không dùng animation làm điều kiện để đọc nội dung hoặc tìm CTA. Video có ảnh thay thế, không tự phát âm thanh.
- Asset có sẵn trong assets/: chưa được cung cấp. Dùng ảnh placeholder có ghi chú hoặc ảnh được phép sử dụng; không coi ảnh mẫu là asset đã được duyệt. Không lấy ảnh sản phẩm Apple làm ảnh website.
- Phong cách ảnh: thời trang editorial, ánh sáng mềm, nền sạch, người mẫu và phom áo là trọng tâm; cận cảnh thể hiện được chất liệu thật. Tránh đồ họa công nghệ và trang trí truyền thống dày đặc.
- Nội dung: ngắn, tự nhiên, giàu cảm giác thời trang; không tự tạo đánh giá khách hàng, doanh số, ưu đãi hoặc chứng nhận.
- Figma: Auto Layout, component tái sử dụng và variants cho nút/input/card/swatches; styles hoặc variables cho màu, chữ, spacing; tên frame/component dễ hiểu. Bàn giao các page Brief, Foundations, Components, Desktop, Mobile, Tablet và Prototype; chú thích responsive và motion.
- Chỉ thiết kế trải nghiệm khách hàng; chưa có admin, tài khoản, thanh toán, hệ thống đơn hàng hoặc yêu cầu tích hợp kỹ thuật.

## Brainstorm
- Trước khi thiết kế Figma, xác nhận: tên thương hiệu chính thức, phân khúc giá, bán sẵn hay đặt may, CTA ưu tiên tư vấn hay mua ngay, asset thực tế và thông tin liên hệ.
- Nếu chưa có câu trả lời, dùng giả định trong spec để lập brief nháp; không tự coi brief là đã được duyệt.
- Trình bày 3 hướng thị giác:
  1. **Modern Ivory — đề xuất:** trắng ngà, chữ lớn tối giản, ảnh áo dài tràn khung, điểm nhấn đỏ rượu. Gần tinh thần trang sản phẩm Apple và phù hợp thương hiệu thời trang hiện đại.
  2. **Editorial Contrast:** nền trắng/đen xen kẽ, ảnh tương phản mạnh, bố cục tạp chí. Cá tính hơn nhưng cần bộ ảnh chất lượng và kiểm soát khả năng đọc.
  3. **Soft Vietnamese:** be cát, xanh sage, serif và ánh sáng tự nhiên. Gần gũi, mềm mại hơn; cần tiết chế trang trí để giữ nét hiện đại.
- Design brief cần người dùng duyệt: mục tiêu, đối tượng, phạm vi P0/P1/P2, sitemap, 3 flow chính, hướng thị giác, font/màu, kế hoạch asset và các giả định.
- Chỉ bắt đầu thiết kế Figma sau khi người dùng duyệt brief. Khi duyệt, triển khai P0 trước; P1 chỉ triển khai nếu được chọn thêm; P2 để ngoài phạm vi.
- Tiêu chí nghiệm thu thiết kế: đủ màn hình và state P0; prototype đi được từ trang chủ đến xác nhận; lựa chọn màu/size và đường quay lại nhất quán; mobile không tràn hoặc che CTA; kiểm tra contrast; các dữ liệu demo được ghi nhận rõ trong page Brief.
