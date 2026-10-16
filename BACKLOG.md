# BACKLOG — Khoảng trống kiến thức chưa có trong thư viện (tự mở rộng)

> Vòng lặp tự lấp đầy: mỗi turn (người hoặc lịch tự động) lấy top 1 mục `chờ viết`,
> viết bài đúng chuẩn `AGENTS.md` + 4 cửa Argon, rồi flip thành `xong` và append
> khoảng trống mới phát hiện (tối đa 3/turn) xuống cuối file.
> Tiêu chí xếp hạng: tần suất gặp lâm sàng > nguy cơ bỏ sót chết người > giá trị thi cử.
> Mỗi turn tối đa **2 bài** (giới hạn context + verify giấy phép ảnh từng bài).
> Không tạo ID trùng bài đã có — kiểm tra `README.md` + curriculum overview trước khi viết.

| # | ID đề xuất | Chủ đề | Vì sao quan trọng nhất | Trạng thái |
|---|---|---|---|---|
| 1 | 612 | Cấp cứu đường thở trẻ em: Croup (steeple) vs viêm nắp thanh quản (thumb) vs dị vật | Cấp cứu nhi tối khẩn, thi cử kinh điển, chưa có bài nào | chờ viết |
| 2 | 525 | K nội mạc/cổ tử cung: FIGO MRI (<50% vs ≥50% cơ, parametrium) | Quyết định mổ/xạ, nối tiếp bài 520 | chờ viết |
| 3 | 512 | Vú: vi vôi hóa, biến dạng cấu trúc, túi ngực (linguine/snowstorm) | Hoàn thiện cụm BI-RADS sau bài 510 | chờ viết |
| 4 | 622 | Tắc ruột sơ sinh: double-bubble, microcolon, Hirschsprung (<1) | Cấp cứu sơ sinh, nối tiếp bài 620 | chờ viết |
| 5 | 159 | Bàng quang: VI-RADS + u đường niệu trên | Lỗ hổng GU duy nhất còn lại (đã có 150/152/155/158) | chờ viết |
| 6 | 635 | Tiết niệu nhi: SFU 1–4, VUR I–V, PUV keyhole | Hay gặp + quyết định mổ, nối tiếp bài 640 | chờ viết |
| 7 | 655 | HIE sơ sinh + Chiari/Dandy-Walker/bất sản thể chai | Não nhi bẩm sinh chưa phủ (đã có 650 u/mầm) | chờ viết |
| 8 | 528 | Dị dạng tử cung ESHRE/ESGE (vách ngăn vs hai sừng) | Hay nhầm, quyết định mổ nội soi | chờ viết |
| 9 | 535 | K buồng trứng, phúc mạc, Krukenberg | Hoàn thiện cụm O-RADS sau bài 530 | chờ viết |
| 10 | 565 | Hình thái thai + Doppler (rốn/MCA/ống TM) | Sản khoa còn thiếu sau bài 550/560 | chờ viết |
| 11 | 151 | U thận đặc: RCC vs oncocytoma vs AML (mỡ −10 HU) | Bosniak (150) chỉ phủ nang, thiếu u đặc | chờ viết |
| 12 | 545 | Sàn chậu MR defecography (PCL/HMO) | Ít gặp hơn, ưu tiên thấp | chờ viết |

## Nhật ký vòng lặp
- 2026-10-16: khởi tạo file + gắn lịch cron tự động (6 giờ/lần, tối đa 2 bài/lượt).
