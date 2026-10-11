# Asset cho agent: icon, ảnh, file Illustrator

Agent không mở được `.ai`. Bạn xuất ra PNG (đưa vào Figma) và SVG (cho dev), agent chỉ dùng các file đã xuất.

```
assets/
├── icons/                  PNG để đưa vào Figma
│   ├── home--text@4x.png        <tên>--<biến-thể>@<N>x.png
│   └── home--primary@4x.png
├── images/                 ảnh minh họa/ảnh nền
│   └── hero-spa@2x.png          <tên>@<N>x.png|jpg
├── source/
│   ├── icons/home.svg           vector gốc, cho dev (agent chỉ ghi lại đường dẫn)
│   └── *.ai                     file Illustrator gốc, chỉ lưu trữ
├── ASSET_MANIFEST.json     do `scripts/assets.py scan` sinh; bạn điền thêm license/origin
└── NEEDED.md               agent ghi những asset còn thiếu
```

## Quy ước tên
- Chỉ chữ thường, số, dấu gạch ngang: `calendar-check`, không `Calendar_Check`.
- `--` ngăn tên và biến thể màu: `home--text`, `home--primary`, `home--white`.
- `@4x` = PNG lớn gấp 4 lần kích thước hiển thị (icon 24px → PNG 96px). Ảnh minh họa dùng `@2x`.

## Xuất từ Illustrator
1. Mỗi icon là một artboard, đặt tên artboard đúng quy ước.
2. **PNG:** `File > Export > Export for Screens` → tab Artboards → Format PNG → Scale 4x → chọn thư mục `assets/icons/`.
   Cần màu nào thì xuất đúng bấy nhiêu biến thể (đổi màu nét rồi xuất lại).
3. **SVG:** cùng hộp thoại, thêm định dạng SVG → `assets/source/icons/`.
4. Lưu file `.ai` gốc vào `assets/source/`.
5. Ảnh minh họa: PNG/JPG, rộng gấp 2 lần kích thước hiển thị, dưới 1 MB mỗi ảnh.

## Vì sao icon là PNG, không phải vector?
Công cụ Figma MCP hiện có `set_image_fill` (điền ảnh vào hình) nhưng không có công cụ nhập SVG thành vector.
Hệ quả: icon trong Figma là ảnh, không đổi màu bằng fill được, nên cần xuất sẵn từng biến thể màu.
Muốn icon là vector sửa được, hãy thêm một lệnh `createNodeFromSvg` vào plugin (xem SETUP.md, mục 9).

## Sau khi thả file
```bash
python3 scripts/assets.py scan     # cập nhật manifest
python3 scripts/assets.py check    # lỗi: file giả đuôi, sai tên; cảnh báo: quá nặng, thiếu license
```
Mở `ASSET_MANIFEST.json`, điền `license` (vd "Phosphor, MIT", "tự thiết kế") cho từng mục.
