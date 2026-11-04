# Nguồn gốc — 1733-not-tai-tao-fnh-like-sau-hoa-tri

> Nốt tăng sản tái tạo FNH-like mới xuất hiện sau hóa trị (oxaliplatin, cyclophosphamide) — "di căn giả" trên MRI gan mật. Quét nguồn 2026-11-04; kiểm tra giấy phép từng ảnh trước khi tải.

| # | Nguồn | Tiêu đề / Ca | Link gốc | Giấy phép ảnh | Tải về? (đường dẫn / lý do không tải) |
|---|---|---|---|---|---|
| 1 | Insights into Imaging (Springer, OA) | Yang F, Peng W, Chen S và cs. *Hepatic focal nodular hyperplasia during follow-up of patients after cyclophosphamide- or oxaliplatin-based chemotherapy: differentiation from liver metastasis.* 2024;15:215. PMC11347512, PMID 39186145, DOI 10.1186/s13244-024-01793-7 | https://pmc.ncbi.nlm.nih.gov/articles/PMC11347512/ | CC BY 4.0 | `images/1733_fnh-like_MRI_PMC11347512-Fig2.jpg`, `...-Fig3.jpg`, `...-Fig4.jpg` (Fig. 1 = MRI + mô bệnh, không dùng vì ảnh ghép 9 panel khó đọc trên mobile) |
| 2 | Insights into Imaging (Springer, OA) | Vernuccio F, Gagliano DS, Cannella R, Ba-Ssalamah A, Tang A, Brancatelli G. *Spectrum of liver lesions hyperintense on hepatobiliary phase: an approach by clinical setting.* 2021;12:8. PMC7801550, DOI 10.1186/s13244-020-00928-w | https://pmc.ncbi.nlm.nih.gov/articles/PMC7801550/ | CC BY 4.0 | `images/1733_fnh-like_CT-MRI_PMC7801550-Fig8.jpg`, `...-Fig9.jpg`, `...-Fig10.jpg`, `images/composite_hbp-fnh-vs-hcc-vs-di-can.jpg` |
| 3 | Diagnostics (MDPI, OA) | Donati F, Cioni D, Guarino S, Mazzeo ML, Neri E, Boraschi P. *Chemotherapy-Induced Liver Injury in Patients with Colorectal Liver Metastases: Findings from MR Imaging.* 2022;12(4):867. PMC9029929, DOI 10.3390/diagnostics12040867 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9029929/ | CC BY 4.0 | không tải — server MDPI chặn tải ảnh (HTTP 403); dùng cho số liệu và cách đọc SOS/FNH-like |
| 4 | Radiology Case Reports (Elsevier, OA) | Vassallo L, Fasciano M, Fortunato M, Orcioni GF, Vavala' T, Regge D. *Focal nodular hyperplasia after oxaliplatin-based chemotherapy: A diagnostic challenge.* 2022. PMC8990178, PMID 35401910 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8990178/ | CC BY-NC-ND | không tải — CC BY-NC-ND (không tạo tác phẩm phái sinh); dùng cho bối cảnh lâm sàng |
| 5 | Journal of Liver Cancer (OA) | Joo I. *Preventing false positive imaging diagnosis of HCC: differentiating HCC from mimickers and practical strategies.* 2025. PMC12518988, PMID 40739839 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12518988/ | CC BY-NC | không tải — CC BY-NC; dùng cho hàng HCC trong ma trận |
| 6 | Bài nội bộ repo | 1910 — Hội chứng tắc xoang gan (SOS) do oxaliplatin | ../1910-hoi-chung-tac-xoang-gan-sos/lesson.md | — | không tải (bài nội bộ) |

## Ghi chú giấy phép
- Ảnh Fig. 2–4 (PMC11347512) và Fig. 8–10 (PMC7801550) đều **CC BY 4.0** → được tải, được ghép letterbox (giữ nguyên tỷ lệ, không crop/kéo giãn).
- Ảnh composite tạo bằng `tools/make_composite.py`, có dải đen ghi tên bệnh + chuỗi xung + attribution.
- Tên tác giả đối chiếu trực tiếp `authorString` qua Europe PMC: PMC11347512 = Yang F, Peng W, Chen S, Wan L, Zhao R, Liu X, Ye F, Zhang H; PMC7801550 = Vernuccio F, Gagliano DS, Cannella R, Ba-Ssalamah A, Tang A, Brancatelli G.
