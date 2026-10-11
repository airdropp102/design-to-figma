@AGENTS.md

## Ghi chú riêng cho Claude Code
- Skill nằm ở `.claude/skills/ui-ux-pro-max/` (cài bằng `uipro init --ai claude`).
- MCP: dùng cấu hình project-scope `.mcp.json` được `./agent setup --runtime claude` tạo từ checkout TalkToFigma đã pin; KHÔNG dùng `@latest` (xem SETUP.md).
- Superpowers: cài bản có revision đã pin rồi smoke test trực tiếp trong Claude Code; chỉ dùng `brainstorming` khi thiết kế (xem workflow.yaml).
- `.claude/settings.json` có hook SessionStart tự in `state.py status --text` khi mở phiên, để bạn thấy ngay tiến trình dở dang.
  Hook không thay được Pha R: dù hook có chạy hay không, việc đầu tiên vẫn là `state.py status --text`.
- Dùng task list để theo dõi từng màn hình; nguồn sự thật vẫn là `design/STATE.json`, không phải task list (task list mất khi phiên kết thúc).
- Với spec nhiều màn (>10): có thể dùng sub-agent để phân tích flow, tạo screen recipe và review offline; **chỉ agent chính** được mutate Figma canvas, kể cả hai sub-agent dựng hai section khác nhau. Khóa state không khóa được toàn bộ Figma plugin/WebSocket nên không được parallel Figma writer.
- State v2: đọc Pha 4 mới trong AGENTS.md về `inspect`, `intend`, `bind`, `qa`, `begin-update`, `done-update`; không dùng Official Figma MCP.
- Nếu response vượt giới hạn output: chia nhỏ theo pha, ghi kết quả ra file từng phần.

- Workflow v3.1: đọc `design/WORKFLOW.json` và `./agent status --json` trước khi thao tác; không tiếp tục nếu thiếu approval/live Figma proof. Chỉ TalkToFigma, không sinh mã nguồn ứng dụng.
