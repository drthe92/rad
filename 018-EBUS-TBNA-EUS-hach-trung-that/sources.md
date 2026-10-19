# Nguồn gốc — 018 Chọc hút hạch trung thất dưới hướng dẫn siêu âm (EBUS-TBNA & EUS-B)

> Quét 2026-10-19: Europe PMC (`FIG:"EBUS-TBNA"` / `FIG:"endobronchial ultrasound"` / `FIG:"EUS-B"` + `OPEN_ACCESS:Y`), lọc theo giấy phép từng bài (ưu tiên CC BY 4.0), đối chiếu PMCID + tác giả qua Europe PMC. Không scrape Radiopaedia; Radiopaedia/AuntMinnie chỉ dẫn link.

| # | Nguồn | Tiêu đề / Ca | Link gốc | Giấy phép ảnh | Tải về? (đường dẫn / lý do không tải) |
|---|---|---|---|---|---|
| 1 | Europe PMC / *Cancers* (MDPI) | **Alkathiri O, Liberman M.** — "State-of-the-Art Mediastinal Staging in Non-Small-Cell Lung Cancer: Integration of Combined Endosonographic Techniques" (2026): **bản đồ hạch IASLC ấn bản 9**, kỹ thuật EUS tới **trạm 6**, **Canada Lymph Node Score**; phối hợp EBUS+EUS-B nâng độ nhạy **82% → 92%** | https://pmc.ncbi.nlm.nih.gov/articles/PMC13204510/ | CC BY 4.0 | `images/018_ban-do-hach-IASLC9_CT_PMC13204510.jpg`, `images/018_EUS-tram-6_US_PMC13204510.jpg`, `images/018_Canada-LN-score_US_PMC13204510.jpg` |
| 2 | Europe PMC / *Cancers* (MDPI) | **Haimi I, Rajaram R.** — "Nodal Staging in Patients with Locally Advanced Non-Small Cell Lung Cancer: Indications, Approaches, and Impact on Downstaging" (2026): lưu đồ lấy mô, so sánh phương thức, tiên lượng theo N; **CT Se 55%/Sp 81%**; **PET ngưỡng hạch/máu > 1,7 hoặc SUV > 3,9 → Se 91%/Sp 79–90%**; **N2a/N2b ấn bản 9** | https://pmc.ncbi.nlm.nih.gov/articles/PMC13510314/ | CC BY 4.0 | `images/018_quy-trinh-staging_CT_PMC13510314.jpg`, `images/018_so-sanh-phuong-thuc_CT_PMC13510314.jpg` |
| 3 | Europe PMC / *Bioengineering* (MDPI) | **Ervik Ø et al.** — "Explainability of a Deep Learning Model for Mediastinal Lymph Node Station Classification in Endobronchial Ultrasound" (2026): ảnh **EBUS hạch trạm 4R** + bản đồ hoạt hóa mô hình | https://pmc.ncbi.nlm.nih.gov/articles/PMC12938215/ | CC BY 4.0 | `images/018_EBUS-tram-4R_US_PMC12938215.jpg` |
| 4 | Europe PMC / *CHEST Pulmonary* | **Gerbino AJ et al.** — "Impact of Rapid Cytologic Evaluation of Endobronchial Ultrasound-Guided Transbronchial Needle Aspiration..." (2026): sơ đồ **ROSE vs chẩn đoán tế bào cuối cùng** | https://pmc.ncbi.nlm.nih.gov/articles/PMC13419112/ | **CC BY-NC-ND 4.0** | `images/018_ROSE-so-do_CT_PMC13419112.jpg` (**giữ nguyên bản, không cắt/ghép**) |
| 5 | Europe PMC / *Cancers* (MDPI) — bổ sung số liệu | **Alkathiri & Liberman** (như #1): **Canada Lymph Node Score** — 4 tiêu chí, mỗi tiêu chí 1 điểm; nghiên cứu đa trung tâm Canada (140 BN, 300 hạch, 12 chuyên gia, mô bệnh là chuẩn vàng): cắt **≥ 3** → Se 31,5% / Sp 96,3% / PPV 86,5% / NPV 65,4% | https://pmc.ncbi.nlm.nih.gov/articles/PMC13204510/ | CC BY 4.0 | (số liệu, đã dùng ảnh ở #1) |
| 6 | Europe PMC / *Cancers* (MDPI) — bổ sung số liệu | **Haimi & Rajaram** (như #2): u trung tâm nguy cơ **N2/N3 20–25%**; **N2a** (1 trạm) tiếp cận mổ sau hóa–miễn dịch, **N2b** (nhiều trạm) đa số không mổ | https://pmc.ncbi.nlm.nih.gov/articles/PMC13510314/ | CC BY 4.0 | (số liệu) |
| 7 | Radiopaedia | Hạch trung thất / phân trạm — mô tả tham khảo | https://radiopaedia.org/articles/mediastinal-lymph-node-stations | dẫn link | không tải |
| 8 | AuntMinnie | Case of the Day (nếu có, tham khảo) | https://www.auntminnie.com/ | paywall — chỉ dẫn link | không tải |

## Ghi chú giấy phép
- Ảnh tải về: **CC BY 4.0** (cho phép tải/ghép khi ghi nguồn), **trừ `018_ROSE-so-do_CT_PMC13419112.jpg` là CC BY-NC-ND 4.0 — giữ NGUYÊN BẢN, không crop/ghép**.
- Ảnh ghép `composite_EUS-tram-6-vs-EBUS-tram-4R.jpg` dựng bằng `tools/make_composite.py` từ 2 ảnh **CC BY 4.0** (#1 + #3), letterbox giữ nguyên tỉ lệ.
- Tác giả ghi theo **tên tác giả đầu tiên đọc trực tiếp từ bản ghi Europe PMC (đối chiếu PMCID/DOI)**; không suy đoán. Số liệu giữ đúng nguồn, số chưa kiểm chứng ghi "chưa rõ".
