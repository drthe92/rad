# Nguồn gốc — 417-hoi-chung-morning-glory

> Hội chứng Morning Glory (MGDA): hõm đĩa thị hình phễu, bong võng mạc, bất thường nền sọ – mạch máu não. Quét Europe PMC/PMC ngày 2026-11-05. Mọi bài dùng đều **open access**, giấy phép đọc trực tiếp từ thẻ `<license>` trong `fullTextXML`.

| # | Nguồn | Tiêu đề / Ca | Link gốc | Giấy phép ảnh | Tải về? (đường dẫn / lý do không tải) |
|---|---|---|---|---|---|
| 1 | Frontiers in Medicine (PMC) | Zou Y và cs 2021 — *Clinical and Echographic Features of Morning Glory Disc Anomaly in Children: A Retrospective Study of 249 Chinese Patients* (PMC8818885; DOI 10.3389/fmed.2021.800623) | https://europepmc.org/article/PMC/PMC8818885 | CC BY 4.0 | `images/417_do-hoc_B-scan_PMC8818885-Fig2.jpg`, `images/417_bat-thuong-nao_MRI-MRA_PMC8818885-Fig4.jpg` |
| 2 | Cureus (PMC) | Radder N, Radder S 2025 — *Morning Glory Disc Anomaly With Ipsilateral Carotid Vasculopathy: MRI Characteristics and Clinical Implications* (PMC12588109; DOI 10.7759/cureus.93932) | https://europepmc.org/article/PMC/PMC12588109 | CC BY 4.0 | `images/417_morning-glory_Anh-day-mat_PMC12588109-Fig1.jpg`, `images/417_morning-glory_MRI-BFFE_PMC12588109-Fig2.jpg` |
| 3 | Journal of Clinical Medicine (MDPI) | Cennamo G và cs 2024 — *Congenital Optic Disc Anomalies: Insights from Multimodal Imaging* (PMC10932420; DOI 10.3390/jcm13051509) | https://europepmc.org/article/PMC/PMC10932420 | CC BY 4.0 | `images/417_hom-dia-thi_Anh-day-mat_PMC10932420-Fig1.jpg` |

## Ghi chú giấy phép
- Cả 3 nguồn đều **CC BY 4.0** → được phép tải, trích và tạo ảnh dẫn xuất khi ghi nguồn.
- Ảnh composite `composite_morning-glory_fundus-MRI.jpg` ghép từ Fig. 1 + Fig. 2 của **PMC12588109** (cùng một bệnh nhi), tạo bằng `tools/make_composite.py` — **letterbox, không crop, không kéo giãn**.
- Tên tác giả lấy từ `authorString` Europe PMC, đối chiếu PMCID — **không bịa tên**.

## Điểm chưa kiểm chứng / cần tra thêm
- Tần suất MGDA: **3,6/100.000 trẻ** (Zou 2021; Cennamo 2024) so với **~1/10.000 trẻ sinh** (Cureus 2025) — hai con số lệch nhau ~3 lần; bài ghi cả hai và không chọn một con số tuyệt đối.
- Tỷ lệ bất thường mạch máu não **20–45%** trong y văn thuộc nhóm được chọn chụp mạch; đoàn hệ 271 mắt chỉ có **8/75 (10,7%)** trẻ được chụp sọ có bất thường.
