# CREDITS — Ảnh bài 3272 (Bơm dầu silicon ở trẻ em)

Mỗi ảnh ghi **nguồn + giấy phép cụ thể**. Attribution theo quy ước: **tạp chí + năm + PMCID/DOI**, **không suy đoán tên tác giả** khi chưa đối chiếu authorString.

| Tệp | Nội dung | Nguồn | Giấy phép | Ghi chú |
|---|---|---|---|---|
| `3272_dau-silicone-tre-em_SoDo_CC0.png` | Sơ đồ "ba đồng hồ": nhược thị 0–8 tuổi, tăng trưởng trục nhãn cầu, biến chứng dầu; kèm vòng khám 3 tháng và ngưỡng | **Tự vẽ** (Pillow) cho bài này | **CC0 1.0** (public domain dedication) | Không chứa dữ liệu bệnh nhân; số liệu ghi trên hình kèm PMID/PMCID |
| `3272_dau-silicone-tre-em_KM_Hinh-PMC12366033-Fig2-CCBY.jpg` | Kaplan–Meier: xác suất **không phải mổ thể thủy tinh** theo loại tamponade (không khí/khí/dầu) ở 242 mắt < 18 tuổi | Int J Retina Vitreous 2025, **PMC12366033**, DOI 10.1186/s40942-025-00718-w, Fig. 2 | **CC BY 4.0** | Nguyên bản, không crop; dùng mục 1.4 và quiz ca 3 |
| `3272_dau-silicone-tre-em_Day-mat-ROP-PMC6552571-Fig3-CCBYNCSA.jpg` | 6 ô (a–f): ROP 4B, cắt dịch kính giữ thể thủy tinh, lỗ hoàng điểm + bong khu trú, bóc ILM, bơm dầu, kết quả lỗ đóng | Indian J Ophthalmol 2019, **PMC6552571**, DOI 10.4103/ijo.IJO_2039_18, Fig. 3 | **CC BY-NC-SA 4.0** | Nguyên bản, **không crop**; dùng quiz ca 2 |
| `3272_dau-silicone-tre-em_OCT-duoi-vong-mac-PMC12077865-Fig1-CCBYNC.jpg` | SD-OCT (a–d): dầu dưới võng mạc lan dưới hoàng điểm ở 14 tháng, giảm dần sau tháo dầu + dẫn lưu | Case Rep Ophthalmol 2025, **PMC12077865**, DOI 10.1159/000545661, Fig. 1 | **CC BY-NC 4.0** | Nguyên bản; thành phần trái của composite |
| `3272_dau-silicone-tre-em_Day-mat-PMC12077865-Fig2-CCBYNC.jpg` | Đáy mắt màu: coloboma đĩa thị, võng mạc áp sau tháo dầu + dẫn lưu dầu dưới võng mạc | Case Rep Ophthalmol 2025, **PMC12077865**, DOI 10.1159/000545661, Fig. 2 | **CC BY-NC 4.0** | Nguyên bản; thành phần phải của composite |
| `3272_dau-silicone-tre-em_OCT-PMC13479887-Fig1-CCBY.jpg` | SD-OCT 2 mắt macula-on: trước dầu (a/d), trong khi có dầu với đường viền hoàng điểm dẹt (b/e), sau tháo dầu (c/f) | BMC Ophthalmol 2026, **PMC13479887**, DOI 10.1186/s12886-026-05235-4, Fig. 1 | **CC BY 4.0** | Nguyên bản; dùng mục 5 (dữ liệu **người lớn**, ghi rõ trong chú thích) |
| `composite_ca-15-tuoi.jpg` | Ghép letterbox Fig. 1 + Fig. 2 của cùng ca 15 tuổi, giữ aspect, dải đen attribution | Case Rep Ophthalmol 2025, **PMC12077865** | **CC BY-NC 4.0** (giữ nguyên giấy phép nguồn) | Tạo bằng `tools/make_composite.py`; dùng mục 3 và quiz ca 1 |

## Quy tắc đã áp dụng

- Ảnh **CC BY / CC BY-NC / CC BY-NC-SA**: tải, dùng **nguyên bản**, không crop/kéo giãn; attribution đầy đủ ở `lesson.md` + bảng này.
- Ảnh ghép chỉ từ **hai ảnh cùng ca, cùng nguồn** (PMC12077865) — không trộn nguồn khác giấy phép.
- Các bài chỉ trích **số liệu** (PMID 10406629, 40122281, 10544979, 33165653, 40086265, 11239883, 15774111, 23882695, 20162296, 17583817) **không tải ảnh**, tránh rủi ro giấy phép.
- Sơ đồ tự vẽ đặt **CC0** và ghi rõ "không phải ảnh bệnh nhân".

## Kiểm tra tên tệp

- Tiền tố `NNN_slug_Modality_SourceID`; composite dùng tiền tố `composite_`.
- Không có ảnh nào ngoài danh sách trên trong `images/`.
