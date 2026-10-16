# BACKLOG — Khoảng trống kiến thức chưa có trong thư viện (tự mở rộng)

> Vòng lặp tự lấp đầy: mỗi turn (người hoặc lịch tự động) lấy top 1 mục `chờ viết`,
> viết bài đúng chuẩn `AGENTS.md` + 4 cửa Argon, rồi flip thành `xong` và append
> khoảng trống mới phát hiện (tối đa 3/turn) xuống cuối file.
> Tiêu chí xếp hạng: tần suất gặp lâm sàng > nguy cơ bỏ sót chết người > giá trị thi cử.
> Mỗi turn tối đa **2 bài** (giới hạn context + verify giấy phép ảnh từng bài).
> Không tạo ID trùng bài đã có — kiểm tra `README.md` + curriculum overview trước khi viết.

| # | ID đề xuất | Chủ đề | Vì sao quan trọng nhất | Trạng thái |
|---|---|---|---|---|
| 1 | 443 | Võng mạc đái tháo đường: phân độ ETDRS/DRSS + phù hoàng điểm DME + OCTA | Hay gặp nhất võng mạc, quyết định laser/anti-VEGF, nối 441 | chờ viết |
| 2 | 444 | Tắc mạch võng mạc: CRVO/BRVO vs CRAO (cherry-red, giờ vàng) | Cấp cứu (CRAO tính bằng giờ), thi cử kinh điển | chờ viết |
| 3 | 445 | Bong võng mạc: rhegmatogenous vs co kéo vs tiết dịch + PVR | Quyết định mổ (khí/nút/scleral buckle), nối 411 siêu âm | chờ viết |
| 4 | 433 | Phù đĩa thị vs drusen đĩa: Frisén + IIH | Tránh chọc dịch oan + bỏ sót u, nối 430 | chờ viết |
| 0 | (27 bài text-only, liệt kê dưới) | Backfill ảnh: ưu tiên Radiopaedia từng case (CC BY-NC-SA) + vẽ CC0, mỗi lượt worker dành ≥1 slot | `chờ viết` (xuyên suốt) |
| 5 | 612 | Cấp cứu đường thở trẻ em: Croup (steeple) vs viêm nắp thanh quản (thumb) vs dị vật | Cấp cứu nhi tối khẩn, thi cử kinh điển, chưa có bài nào | xong (2026-10-16, 4 ảnh CC BY/BY-NC + composite) |
| 6 | 525 | K nội mạc/cổ tử cung: FIGO MRI (<50% vs ≥50% cơ, parametrium) | Quyết định mổ/xạ, nối tiếp bài 520 | chờ viết |
| 7 | 512 | Vú: vi vôi hóa, biến dạng cấu trúc, túi ngực (linguine/snowstorm) | Hoàn thiện cụm BI-RADS sau bài 510 | chờ viết |
| 8 | 622 | Tắc ruột sơ sinh: double-bubble, microcolon, Hirschsprung (<1) | Cấp cứu sơ sinh, nối tiếp bài 620 | chờ viết |
| 9 | 159 | Bàng quang: VI-RADS + u đường niệu trên | Lỗ hổng GU duy nhất còn lại (đã có 150/152/155/158) | chờ viết |
| 10 | 635 | Tiết niệu nhi: SFU 1–4, VUR I–V, PUV keyhole | Hay gặp + quyết định mổ, nối tiếp bài 640 | chờ viết |
| 11 | 655 | HIE sơ sinh + Chiari/Dandy-Walker/bất sản thể chai | Não nhi bẩm sinh chưa phủ (đã có 650 u/mầm) | chờ viết |
| 12 | 528 | Dị dạng tử cung ESHRE/ESGE (vách ngăn vs hai sừng) | Hay nhầm, quyết định mổ nội soi | chờ viết |
| 13 | 535 | K buồng trứng, phúc mạc, Krukenberg | Hoàn thiện cụm O-RADS sau bài 530 | chờ viết |
| 14 | 565 | Hình thái thai + Doppler (rốn/MCA/ống TM) | Sản khoa còn thiếu sau bài 550/560 | chờ viết |
| 15 | 151 | U thận đặc: RCC vs oncocytoma vs AML (mỡ −10 HU) | Bosniak (150) chỉ phủ nang, thiếu u đặc | chờ viết |
| 16 | 545 | Sàn chậu MR defecography (PCL/HMO) | Ít gặp hơn, ưu tiên thấp | chờ viết |
| 17 | 615 | Viêm phổi nhi: round pneumonia, virus vs vi khuẩn, hít sặc dầu hỏa | Hay gặp + dễ kháng sinh mù; nối tiếp 610/612 (phổi nhi còn thiếu mảng nhiễm trùng) | chờ viết |

## Nhật ký vòng lặp
- 2026-10-16: khởi tạo file + gắn lịch cron tự động (6 giờ/lần, tối đa 2 bài/lượt).
- 2026-10-16: lịch chuyển 1 giờ/lần + luật ảnh Radiopaedia-từng-case/CC0 + mục #0 backfill 27 bài text-only.
- 2026-10-16: viết 612 (cấp cứu đường thở nhi, 4 ảnh CC BY/BY-NC + composite dịch-vs-áp-xe, link chéo 730); append 615 (viêm phổi nhi — khoảng trống mới). Slot backfill #0 dồn lượt sau.
