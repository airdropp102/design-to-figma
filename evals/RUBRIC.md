# RUBRIC

| Chỉ số | Cách đo | Mục tiêu |
|---|---|---|
| Độ phủ chức năng P0 | Số chức năng P0 xuất hiện ≥ 1 màn / tổng P0 (đối chiếu DESIGN_REPORT) | 100% |
| Token fidelity | Số node có màu/font khớp tokens.json / tổng node kiểm tra (lấy mẫu 5 màn bằng `get_node_info`) | ≥ 95% |
| Contrast | Số cặp text/bg đạt ≥ 4.5:1 / tổng cặp trong tokens | 100% |
| Checklist pass rate | Mục đạt / tổng mục "Pre-delivery checklist" của MASTER.md | ≥ 90% |
| Tool-call error rate | Lệnh MCP lỗi / tổng lệnh | ≤ 5% |
| Trùng lặp | Số frame trùng tên `S<ID>` sau khi chạy lại từ BUILD_LOG | 0 |
| Placeholder text | Số text node còn "Lorem"/"Text"/"Label" | 0 |
| Thời gian / chi phí | Phút và token trên mỗi màn | Ghi nhận, so sánh giữa Claude và Codex |

## Chấm so sánh Claude vs Codex
Chạy B01, B05, B07 trên cả hai nền tảng, cùng spec. Ghi lại: thành công cuối cùng (có/không),
số lần dừng do lỗi, thời gian, và chất lượng thị giác (1–5, hai người chấm độc lập).

## Phương án A — benchmark hiệu quả TalkToFigma

Chạy brief B01 trên file thử đã sao lưu; cùng spec, model, và thiết bị. Chạy baseline gói cũ và bản patch, tối thiểu 3 lần mỗi cấu hình. Đếm call MCP thực từ `state.py metrics`/log tool, không ước lượng.

| KPI | Cách đo | Tiêu chí chấp nhận |
|---|---|---|
| MCP calls / validated screen | Tổng calls Figma / màn qua QA | Giảm ≥25% so baseline (mục tiêu, chưa xác minh live) |
| Validated screen success | Màn qua structural + visual QA bắt buộc / màn thực hiện | ≥95% |
| Batch text usage | Text replacements dùng `set_multiple_text_contents` / tất cả text replacements có thể gom | ≥90% |
| Incremental skip precision | Màn skip thực sự không cần mutation / màn skip được kiểm tra | 100% |
| Wrong-node mutation | Mutation ngoài node thuộc state / toàn bộ mutation | 0 |
| Duplicate screen roots | Số root trùng `S<ID>` sau crash/recovery | 0 |
| Recovery | Case pass / total case trong CHAOS.md | 100% |

**Không sử dụng Official Figma MCP trong benchmark**. Test local của state/intent không thay cho benchmark tốc độ/chất lượng thực tế trên Figma.
