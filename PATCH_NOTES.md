# TalkToFigma-only Harness — Option A patch

Ngày: 2026-10-10. Nguồn: `figma-design-agent.zip`.

## Đã thay đổi
- **Giữ TalkToFigma MCP duy nhất.** Không tích hợp Official Figma MCP, không thêm Figma API token.
- **AGENTS.md / CLAUDE.md:** one-writer, reuse/clone trước primitive, batch text/read/delete theo schema thực, không dựng lại màn không đổi, QA P0 bắt buộc.
- **scripts/state.py:** state v2, migrate v1 an toàn, `inspect`, `intend`, `begin-update`, `done-update`, `bind`, `adopt`, `qa`, `metrics`, `accept-spec`.
- **scripts/intent.py:** chuẩn hoá per-screen recipe; phân loại `skip/text_patch/style_patch/mixed_patch/rebuild`, fingerprint chỉ token/asset được screen dùng, hash bytes của file asset.
- **specs/SCREEN_RECIPE.template.json:** mẫu recipe nhẹ (không phải full Design IR).
- **evals:** rubric/chaos cases cho incremental + QA.
- **tests:** 14 test local đã chạy thành công, bao gồm WAL crash gate, migration, adopt, token/asset delta, text-only, P0 QA và duplicate ID.

## Chưa được chứng minh trong môi trường này
- Không có kết nối tới Figma plugin/channel nên **chưa test canvas live**, chưa đo lường giảm MCP calls thực tế; mục tiêu ≥25% mới là KPI, không phải kết quả.
- Script local không thể tự xác minh root/node ngoài Figma. `--verified-live` là lời xác nhận thủ tục của agent **sau** khi dùng `get_nodes_info`; không thay thế live verification.
- TalkToFigma upstream không có universal bulk create API. Primitive layout/style vẫn có thể cần nhiều MCP calls.
- One-writer mới được quy định bằng instruction, **chưa có distributed lock ở lớp WebSocket Figma**. Không chạy 2 agent writer cùng file.

## Quickstart
```bash
# Trong thư mục figma-design-agent
python3 -m unittest discover -s tests -v
python3 scripts/state.py status --text
# Chỉ nếu STATE.json cũ là version 1:
python3 scripts/state.py migrate
```

Đọc `SETUP.md` và AGENTS.md Pha 4 trước khi dùng thực tế. Với STATE có tiến trình đang chạy, **sao lưu `design/STATE.json`** trước migration.
