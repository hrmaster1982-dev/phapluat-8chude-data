# TASK-01 — Thu thập văn bản pháp luật 8 chủ đề (cho chatbot) + đẩy GitHub

> Đây là LÀM LẠI cho ra việc. Bản trước (vietnamese-legal-docs-scraper, file
> all_documents_hybrid_20260618_171201.md) bị TRƯỢT nghiệm thu: 9/10 văn bản SAI chủ đề,
> 4/10 hết hiệu lực, không tải file thật, trích sai trường, chưa push GitHub. Xem REVIEW-01.
> Branch: `swe/01-legal-scraper` → mở PR.

## 1. Bối cảnh
Cần kho văn bản pháp luật THẬT, ĐÚNG 8 chủ đề, CÒN HIỆU LỰC để nuôi một chatbot RAG.
Chất lượng dữ liệu quan trọng hơn số lượng. KHÔNG được lấy bừa văn bản cho đủ số.

## 2. 8 chủ đề (mỗi văn bản phải gắn đúng 1 topic_key)
1. `hdld`        — Hợp đồng lao động
2. `bhxh`        — Bảo hiểm xã hội
3. `thue_tncn`   — Thuế thu nhập cá nhân  (KHÔNG nhầm thuế nhập khẩu/XNK)
4. `cong_doan`   — Công đoàn
5. `hd_khoan`    — Hợp đồng khoán
6. `hd_kinh_te`  — Hợp đồng kinh tế
7. `uu_dai_dt`   — Ưu đãi đầu tư
8. `chinh_sach_dn` — Chính sách doanh nghiệp

## 3. Yêu cầu cụ thể
- [ ] Mỗi chủ đề: **>= 5 văn bản ĐÚNG chủ đề và CÒN HIỆU LỰC** (tổng >= 40).
- [ ] Mỗi văn bản lưu **CẢ HAI**:
      (a) file gốc tải về (PDF/DOC) NẾU trang có nút "Tải về"; nếu không có thì ghi rõ `original_file: null`.
      (b) **toàn văn đã làm sạch** (bỏ menu/breadcrumb/"Thuộc tính Lược đồ Tải về 100%"...).
- [ ] Mỗi văn bản có metadata đúng: `so_hieu`, `co_quan_ban_hanh`, `ngay_ban_hanh`,
      `tinh_trang_hieu_luc`, `topic_key`, `nguon_url`, `original_file`, `full_text_path`.
- [ ] Tự động push lên GitHub repo: `hrmaster1982-dev/phapluat-8chude-data` (tạo nếu chưa có, qua `gh`).
      Cấu trúc repo: `docs/<topic_key>/<so_hieu>.{pdf|txt}` + `index.json` liệt kê toàn bộ.

## 4. ⛔ Cấm (chống làm hình thức — bản trước dính hết)
- Cấm lấy văn bản KHÔNG thuộc chủ đề chỉ để đủ số (đối chiếu nội dung, không chỉ tiêu đề).
- Cấm đưa văn bản "Hết hiệu lực" vào kho chính (nếu giữ để tham khảo phải gắn cờ rõ + để thư mục riêng).
- Cấm coi text dính menu/breadcrumb là "nội dung" — phải làm sạch.
- Cấm dùng file .docx template tự chế thay cho văn bản tải về.
- Cấm tự gắn "PASSED" bằng phép kiểm chỉ xét "chuỗi không rỗng".
- Cấm báo "đã push GitHub" khi `git log` của repo remote chưa có commit.

## 5. ✅ Definition of Done (Claude sẽ tự chạy lại để kiểm)
- [ ] Chạy `python <scraper> --run` → sinh ra `index.json` với >= 40 mục.
- [ ] Mỗi `topic_key` trong index có >= 5 mục; đếm bằng script, in ra bảng topic→count.
- [ ] Mọi mục có `tinh_trang_hieu_luc` = còn hiệu lực (hoặc nằm trong thư mục `_het_hieu_luc/` riêng).
- [ ] Mở ngẫu nhiên 5 mục bất kỳ: `full_text` là điều/khoản luật thật, KHÔNG mở đầu bằng menu web.
- [ ] Với mục có `original_file`: file mở được, đúng định dạng (không phải template rỗng).
- [ ] `grep -rIn "TODO\|FIXME\|placeholder\|mock\|test_document\|lorem"` trong code → không còn rác.
- [ ] `gh repo view hrmaster1982-dev/phapluat-8chude-data` tồn tại + `git log` có commit dữ liệu thật.

## 6. Bằng chứng SWE phải nộp trong PR description
- Output bảng `topic → số văn bản` (phải >= 5 mỗi dòng).
- 3 ví dụ `so_hieu + co_quan + tinh_trang` trích đúng.
- URL repo GitHub + ảnh/đoạn `git log` chứng minh đã push.
- Nêu rõ chủ đề nào khó kiếm đủ 5 (nếu có) thay vì lấy bừa cho đủ.

## 7. FIXME (Claude điền sau mỗi vòng chưa đạt)
<trống — vòng đầu của bản làm lại>
