# phapluat-8chude-data

Kho văn bản pháp luật THẬT theo **8 chủ đề**, làm dữ liệu cho chatbot RAG.

> **AGENT (SWE-1.6) đọc trước khi làm:** mở [`TASK.md`](TASK.md) — đặc tả đầy đủ + Definition of Done.
> Quy trình git ở [`AGENT_INSTRUCTIONS.md`](AGENT_INSTRUCTIONS.md). Làm sai phạm vi = trượt nghiệm thu.

## Cấu trúc repo (đích cần đạt)
```
docs/
  hdld/         <so_hieu>.pdf  +  <so_hieu>.txt   (file gốc + toàn văn sạch)
  bhxh/
  thue_tncn/
  cong_doan/
  hd_khoan/
  hd_kinh_te/
  uu_dai_dt/
  chinh_sach_dn/
  _het_hieu_luc/   (văn bản hết hiệu lực, để riêng - không vào kho chính)
index.json         danh mục toàn bộ + metadata mỗi văn bản
scraper/           mã nguồn thu thập (chạy lại được)
```

## Nghiệm thu
Người giám sát (Claude Code) sẽ **clone repo này về tự chạy lại scraper** và kiểm theo
Definition of Done trong TASK.md (đếm số văn bản đúng-chủ-đề/còn-hiệu-lực, mở thử toàn văn + file gốc).
