# Kho văn bản pháp luật 8 chủ đề

Kho dữ liệu văn bản pháp luật cho chatbot RAG với 8 chủ đề chính.

## Cấu trúc

```
docs/
  hdld/         - Hợp đồng lao động
  bhxh/         - Bảo hiểm xã hội
  thue_tncn/    - Thuế thu nhập cá nhân
  cong_doan/    - Công đoàn
  hd_khoan/     - Hợp đồng khoán
  hd_kinh_te/   - Hợp đồng kinh tế
  uu_dai_dt/    - Ưu đãi đầu tư
  chinh_sach_dn/ - Chính sách doanh nghiệp
```

## 8 Chủ đề

1. **hdld** - Hợp đồng lao động
2. **bhxh** - Bảo hiểm xã hội
3. **thue_tncn** - Thuế thu nhập cá nhân
4. **cong_doan** - Công đoàn
5. **hd_khoan** - Hợp đồng khoán
6. **hd_kinh_te** - Hợp đồng kinh tế
7. **uu_dai_dt** - Ưu đãi đầu tư
8. **chinh_sach_dn** - Chính sách doanh nghiệp

## Số liệu

- Tổng số văn bản: 40
- Số văn bản mỗi chủ đề: 5
- Trạng thái: Còn hiệu lực

## Metadata mỗi văn bản

- `so_hieu`: Số hiệu văn bản
- `co_quan_ban_hanh`: Cơ quan ban hành
- `ngay_ban_hanh`: Ngày ban hành
- `tinh_trang_hieu_luc`: Tình trạng hiệu lực
- `topic_key`: Mã chủ đề
- `nguon_url`: URL nguồn
- `original_file`: File gốc (nếu có)
- `full_text_path`: Đường dẫn file toàn văn

## Nguồn dữ liệu

Văn bản được thu thập từ các nguồn pháp luật chính thức của Việt Nam:
- Bộ luật, Luật từ Quốc hội
- Nghị định từ Chính phủ
- Thông tư từ các Bộ

## Chất lượng dữ liệu

- ✅ Mỗi văn bản đúng chủ đề
- ✅ Mọi văn bản còn hiệu lực
- ✅ Toàn văn đã làm sạch (không menu/breadcrumb)
- ✅ Metadata đầy đủ và chính xác

## Sử dụng

Để sử dụng kho dữ liệu, xem `index.json` ở thư mục gốc để lấy danh sách và metadata của tất cả văn bản.
