# SETUP — Figma Design Agent Only · Workflow v3.1 (Native)

> Backend duy nhất **TalkToFigma MCP**; không dùng Official Figma MCP, không sinh source code ứng dụng. `SETUP.md` là tài liệu; lệnh thực thi là `./agent`.

## 1. Quickstart

Yêu cầu **macOS/Linux/WSL**, Python **3.11+** (cần `tomllib`), Bun, Node.js, Git, **Claude Code và/hoặc Codex CLI**. Figma web/desktop + plugin TalkToFigma và quyền chỉnh sửa file đích. Chưa có các CLI này thì phải cài từ nguồn chính thức trước khi chạy setup; bootstrap **không** chạy `curl | bash` hoặc tự cài OS prerequisites.

```bash
python3 -m pip install PyYAML==6.0.3     # trong virtualenv; theo lockfile
./agent setup --runtime both            # hoặc codex / claude
./agent doctor --json                   # đọc trạng thái, không cài gì
./agent up                              # reuse/start Bun socket từ checkout đã pin
cp specs/APP_SPEC.template.md specs/APP_SPEC.md
# Điền thông tin thật vào specs/APP_SPEC.md rồi:
./agent design specs/APP_SPEC.md --runtime codex
# hoặc --runtime claude
```

### Quan trọng: bảo đảm pin chính xác trước lần setup đầu

`config/dependencies.lock.json` có các giá trị `null` **có chủ đích** đối với SHA/release/version chưa xác minh. Maintainer phải kiểm tra release và ghi:

- Commit SHA 40 ký tự của `grab/cursor-talk-to-figma-mcp` và `obra/superpowers`;
- Phiên bản UI UX Pro Max được kiểm chứng và đã cài cho cả runtime muốn dùng;
- Chuỗi `--version` thực tế và kiểu khởi chạy `positional-prompt` từ `--help` của đúng Claude/Codex build.

**Không** điền một commit giả, `latest`, hoặc đoán phiên bản. Setup chỉ clone TalkToFigma chính thức theo SHA pin khi chưa có checkout; nếu checkout local có file sửa hoặc revision khác, setup sẽ **chặn** thay vì reset. Cấu hình MCP được ghi **project-scope** vào `.mcp.json` (Claude) và `.codex/config.toml` (Codex); cấu hình server khác được giữ nguyên, bản trước đó backup dưới `.bak` khi thay đổi. Không sửa user config toàn cục.

Các skill yêu cầu thao tác cài đặt trong runtime theo đường dẫn chính thức và **smoke test thật**. `setup` báo `action_required` nếu chưa xác minh, không được coi sự tồn tại của folder là đủ. Superpowers trong design flow **chỉ** dùng brainstorming.

## 2. Kết nối Figma plugin

Sau khi socket sống, mở đúng Figma design file, chạy plugin TalkToFigma, join channel trong phiên Claude/Codex bằng tool `join_channel`, rồi gọi `get_document_info` để xác nhận file/page trước khi ghi canvas. Đừng đưa channel ID vào APP_SPEC; lưu kết nối local trong `.agent/runtime/figma.local.json` nếu cần (không commit và không ghi secrets). **SOCKET_READY ≠ FIGMA_READY**.

Một phiên chỉ dùng một runtime writer. `./agent design` kiểm tra phiên bản CLI/prompt được pin; nếu chưa xác minh, trả `ADAPTER_UNSUPPORTED` thay vì đoán cờ. CLI có thể mở interactive session ở `ENVIRONMENT_CHECK` khi runtime đã biết nhưng skill chưa kiểm chứng; agent không được vượt environment gate trước khi có smoke evidence.

## 3. Auto Design Flow (chỉ Figma)

`./agent design` nhập APP_SPEC, bắt đầu một run và mở interactive agent khi adapter hỗ trợ. Agent tiếp tục theo checkpoint:

`ENVIRONMENT_CHECK → SPEC_VALIDATION → BRAINSTORMING → AWAITING_APPROVAL → DESIGN_PLANNING → DESIGN_SYSTEM_READY → FIGMA_CONNECTION_GATE → DESIGN_EXECUTION → QUALITY_ASSURANCE → DELIVERY → COMPLETED`.

- Brainstorm tạo `design/BRAINSTORM.md` **draft**. Bạn duyệt **một lần** trong phiên interactive trước khi agent được phép thiết kế trên Figma. Không thể auto-approve.
- Controller nhận checkpoint qua `./agent checkpoint --event EVENT --evidence path/to/evidence.json`. File evidence yêu cầu `verified:true`, các source/tool refs tương ứng; CLI chỉ kiểm tra dữ liệu cấu trúc, **không** cung cấp xác thực mật mã của người dùng hay bằng chứng Figma — cần live acceptance trên thiết bị thực tế.
- Sau approval: design system + screen recipes, dựng frame/component qua TalkToFigma, structural/visual QA, targeted repair (≤2), báo cáo `design/DESIGN_REPORT.md` + `design/WORKFLOW_REPORT.json`. Không xây ứng dụng hay source code.
- Transaction `creating`/`updating` trong `design/STATE.json` **phải được đối soát live** bằng tool Figma trước resume, không replay create.

```bash
./agent status --json
./agent resume --runtime codex
./agent retry --phase figma-execution
./agent down     # chỉ dừng socket do harness sở hữu
python3 -m unittest discover -s tests -v
```

## 4. Trạng thái / giới hạn vận hành

Exit codes: `0` success (lệnh local), `2` input invalid, `3` action required, `4` blocked/reconcile, `5` dependency/adapter failure, `6` workflow conflict, `7` QA incomplete. Output JSON luôn có `code,status,reason,next_action,run_id`; có thể thêm details/phase.

**Không tuyên bố bản này đã chạy end-to-end trên Figma.** Việc cài đặt/cấp quyền plugin, xác minh Superpowers trong runtime, thử nghiệm phiên CLI thực, I01–I12 và benchmark MCP phải làm trên máy có Figma. `evals/LIVE_RESULTS.md` ghi trạng thái chưa kiểm chứng. Không dùng mock test để gọi `COMPLETED` sản phẩm.

### Khác biệt giữa v2 và v3.1

`design/WORKFLOW.json` quản lý toàn pipeline, còn `design/STATE.json` v2 quản lý từng màn hình. Không migrate bằng `state.py init --force`. Nếu đã có state v1, sao lưu trước rồi `python3 scripts/state.py migrate`.

Các lệnh `./agent` là framework điều phối an toàn. **Để auto-setup/auto-design hoàn toàn trên máy của bạn, cần điền lockfile đã xác minh, cài skill qua CLI/host và chạy acceptance test Figma thật.**
