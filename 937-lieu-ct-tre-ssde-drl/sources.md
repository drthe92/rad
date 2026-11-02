# Nguồn bài 937 — Liều CT ở trẻ: SSDE, DRL nhi và theo dõi liều tích lũy

> Nguyên tắc: chỉ đọc **toàn văn**, không viết từ abstract gián tiếp; ghi rõ PMCID + giấy phép.
> Không ghi tên tác giả khi chưa đối chiếu trực tiếp với PMCID.

## 1. Nguồn chính (toàn văn mở, đã đọc)

| # | Tài liệu | PMCID / DOI | Giấy phép | Dùng cho |
|---|---|---|---|---|
| 1 | *Size-specific dose estimation in pediatric computed tomography: from dose characterization to individualized optimization.* World J Radiol 2026 | PMC13527544 / 10.4329/wjr.124887 | CC BY-NC 4.0 | Định nghĩa SSDE, TG-204/TG-220/TG-293; SSDE cao hơn CTDIvol 88%; Deff vs Dw −10,08%; liều cơ quan/SSDE 0,7–1,4; DRL bụng–chậu theo cân nặng/Deff; DRL đầu 75th percentile; liều hiệu dụng đầu theo tuổi; chiều dài quét cho viêm ruột thừa; lọc lặp 58–60%; giới hạn cộng dồn liều |
| 2 | *Clinical indication-based pediatric diagnostic reference level values for abdominal computed tomography.* Health Sci Rep 2025;8:e70916 | PMC12277105 / 10.1002/hsr2.70916 | CC BY-NC 4.0 | 121 trẻ u nguyên bào thận; DRL theo 5 nhóm cân nặng; CTDIvol 2,4–2,7 mGy, DLP 78,4–108 mGy·cm, SSDE 4,9–5,6 mGy; phản biện "DRL đặt bằng trung vị" |
| 3 | *Relationship between water-equivalent diameter, CT dose indices, and image noise in pediatric head CT.* J Med Phys 2026;51(3):424–429 | PMC13345115 / 10.4103/jmp.jmp_289_25 | CC BY-NC-ND 4.0 | 50 trẻ 0–14 tuổi, 120 kVp; TCM bật vs tắt; CTDIvol −15,4%, SSDE −24,5%, nhiễu 10,2→8,6 HU; phương trình hồi quy Dw–SSDE; phản biện chênh lệch giữa số nhóm và biểu đồ |
| 4 | *Radiation dose optimisation in paediatric head CT using attenuation-based auto prescription.* Sci Rep 2025;15:33276 | PMC12474883 / 10.1038/s41598-025-18097-5 | CC BY-NC-ND 4.0 | 147 trẻ; giảm liều 48,2% (0–1 tuổi) và 40,4% (10–15 tuổi); ca 34,4 → 19,93 mGy, SSDE 33,02 → 19,27, ED 1,49 → 0,84 mSv; chất lượng ảnh không thua |
| 5 | *Radiation dose alert: CT overexposure as a result of patient off-centering.* J Belg Soc Radiol 2025;109(1):61 | PMC12680003 / 10.5334/jbsr.3971 | CC BY 4.0 | Ca lệch tâm: DLP 3.394 mGy·cm ≈ 51 mSv, > 10× trung vị; CTDIvol lần sau thấp hơn 40% nhưng ảnh chẩn đoán được; vai trò DACS/cảnh báo liều |
| 6 | *Clinical determinants of dose-length product in pediatric brain CT.* J Imaging 2026;12:383 | PMC13514631 | CC BY 4.0 | 69 ca CT sọ ≤ 5 tuổi; DLP khác theo nhóm tuổi (1–5 tuổi +158,71 mGy·cm so với < 1 tuổi); BMI/giới/hãng máy không độc lập — củng cố "tuổi ≠ kích thước" |

## 2. Hướng dẫn / chuẩn tham chiếu (đọc gián tiếp qua nguồn 1, ghi rõ)

- **AAPM TG-204** (2011) — SSDE dựa trên AP, LAT hoặc Deff (thân).
- **AAPM TG-220** (2014) — Dw (water-equivalent diameter), hiệu chỉnh theo suy giảm.
- **AAPM TG-293** (2022) — SSDE cho CT đầu; hệ số riêng, không dùng hệ số thân.
- **ICRP Publication 135** (2017) — định nghĩa typical value (trung vị) và DRL (bách phân vị 75 của trung vị từng cơ sở), cỡ mẫu tối thiểu 20.
- **Image Gently** — chiến dịch tối ưu liều CT nhi (10 bước thực hành của Strauss và cs., dẫn qua nguồn 1).

## 3. Nguồn đã loại (và vì sao)

- Hai hình của **PMC12277105** (báo cáo liều trên PACS; đo AP/LAT) ghi "used with permission / personal communication" → **không chắc thuộc phạm vi CC BY-NC**, nên **không dùng ảnh**; chỉ dùng Figure 3 (biểu đồ của tác giả).
- Các bài DRL của ICRP/AAPM **không mở toàn văn** → chỉ trích qua nguồn 1, không gán số cho bản gốc khi chưa đọc.
- Không dùng Radiopaedia/AuntMinnie cho bài này (chủ đề vật lý liều, không cần ca bệnh).

## 4. Kiểm chứng số liệu

- Mọi con số trong `lesson.md` lấy từ **toàn văn/bảng/hình** của 6 nguồn trên.
- Các số **không kiểm chứng được** đã ghi rõ là "chưa có ngưỡng thống nhất" (liều tích lũy) thay vì bịa ngưỡng.
- Chỗ nguồn **tự mâu thuẫn** (trung bình nhóm TCM giảm SSDE nhưng biểu đồ TCM nằm cao hơn) đã ghi **phản biện** ngay trong bài, không sửa nguồn.
