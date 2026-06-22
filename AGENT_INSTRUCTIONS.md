# Hướng dẫn cho SWE-1.6 — quy trình git

Bạn nhận việc qua repo này. Làm đúng các bước:

1. **Clone** repo: `gh repo clone hrmaster1982-dev/phapluat-8chude-data` (hoặc git clone HTTPS).
2. **Đọc** `TASK.md` — đó là yêu cầu bắt buộc + Definition of Done. KHÔNG làm ngoài phạm vi.
3. **Tạo branch**: `git checkout -b swe/01-legal-scraper`.
4. **Làm việc** → ghi kết quả đúng cấu trúc trong `README.md`:
   - mã scraper vào `scraper/`
   - dữ liệu vào `docs/<topic_key>/...`
   - danh mục `index.json` ở gốc.
5. **Commit + push branch**, rồi **mở Pull Request** vào `main`.
6. **Trong PR description, nộp bằng chứng** (mục 6 của TASK.md):
   - bảng `topic → số văn bản` (mỗi dòng >= 5),
   - 3 ví dụ trích đúng `so_hieu / co_quan / tinh_trang`,
   - xác nhận đã push (đoạn `git log`).

## Tuyệt đối tránh (bản trước đã trượt vì các lỗi này)
- Lấy văn bản KHÔNG đúng chủ đề cho đủ số (vd thuế nhập khẩu thay cho Thuế TNCN).
- Đưa văn bản "Hết hiệu lực" vào kho chính.
- Coi text dính menu/breadcrumb web là "nội dung".
- Dùng file template tự chế thay cho văn bản tải về.
- Tự gắn "PASSED" mà chưa đối chiếu đúng chủ đề + còn hiệu lực.

Không tự ý đổi yêu cầu sang phương án dễ hơn. Vướng chỗ nào → ghi rõ trong PR, đừng giấu.
