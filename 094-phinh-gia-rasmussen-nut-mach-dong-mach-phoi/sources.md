# Nguồn gốc — 094 Ho ra máu từ động mạch phổi: phình giả Rasmussen & nút mạch phổi

> Quét Europe PMC `FIG:"Rasmussen aneurysm" AND OPEN_ACCESS:Y` (22 bài) + `FIG:"pulmonary artery" AND FIG:"embolization" AND FIG:"hemoptysis"` (52 bài), lọc thủ công ngày 2026-10-27. Tên tác giả đối chiếu `authorString` Europe PMC cùng ngày.

| # | Nguồn | Tiêu đề / Ca | Link gốc | Giấy phép ảnh | Tải về? (đường dẫn / lý do không tải) |
|---|---|---|---|---|---|
| 1 | Eur Radiol (Akis S et al. 2025) | Therapeutic approaches for pulmonary artery pseudoaneurysms and analysis of outcomes (29 túi phình giả / 28 bệnh nhân) | https://europepmc.org/article/MED/PMC12634792 · PMCID PMC12634792 | CC BY 4.0 | `images/094_rasmussen_CT-DSA_PMC12634792-Fig3-CCBY.jpg`, `..._DSA_...-Fig4-...jpg` |
| 2 | BMC Pulm Med (Liu M et al. 2024) | Clinical and radiological features associated with rupture of pulmonary artery pseudoaneurysm: a retrospective study (50 bệnh nhân / 58 túi) | https://europepmc.org/article/MED/PMC11351075 · PMCID PMC11351075 | CC BY 4.0 | `images/094_rasmussen_CT_PMC11351075-Fig3-CCBY.jpg`, `..._CT-DSA_...-Fig4-...jpg`, `composite_rasmussen-chua-vo-vs-vo.jpg` |
| 3 | J Cardiothorac Surg (Li FQ et al. 2023) | Endovascular treatment for massive haemoptysis due to pulmonary pseudoaneurysm: report of 23 cases | https://europepmc.org/article/MED/PMC10426096 · PMCID PMC10426096 | CC BY 4.0 | `images/094_rasmussen_CT-DSA_PMC10426096-Fig2-CCBY.jpg` |
| 4 | J Thorac Dis (Chen Y et al. 2026) | Pulmonary artery involvement contributes to the recurrence of hemoptysis after bronchial artery embolization in patients with chronic pulmonary aspergillosis (58 ca, Cox đa biến) | https://europepmc.org/article/MED/PMC13266778 · PMCID PMC13266778 | CC BY 4.0 | không tải ảnh (chỉ dùng số liệu hồi quy HR 3,43) |
| 5 | Respirol Case Rep (2024) | Rasmussen aneurysm in a patient with pulmonary tuberculosis | https://europepmc.org/article/MED/PMC11625681 · PMCID PMC11625681 | CC BY 4.0 (theo bài) | không tải (đã đủ ảnh; nguồn dự phòng ca lâm sàng) |
| 6 | J Korean Soc Radiol (2024) | Angiographic Insights and Endovascular Intervention in Pulmonary Artery Pseudoaneurysms | https://europepmc.org/article/MED/PMC11625830 · PMCID PMC11625830 | dẫn link | không tải ảnh (chỉ đối chiếu kỹ thuật) |
| 7 | CMAJ (2026) | Concurrent Rasmussen aneurysm and pulmonary embolism in a patient with cavitary pulmonary tuberculosis | https://europepmc.org/article/MED/PMC13561452 · PMCID PMC13561452 | dẫn link | không tải (ca ngắn) |
| 8 | The Radiology Assistant (RadiologyAssistant.nl) | Pulmonary hemorrhage / hemoptysis | https://radiologyassistant.nl/ | dẫn link | không tải (ảnh theo điều khoản trang) |
| 9 | AuntMinnie | Case of the Day — pulmonary artery pseudoaneurysm | https://www.auntminnie.com/ | paywall — **chỉ dẫn link** | **không tải** |

## Ghi chú giấy phép
- Ảnh nguồn **CC BY 4.0** → được phép ghép; composite `composite_rasmussen-chua-vo-vs-vo.jpg` tạo bằng `tools/make_composite.py` (letterbox nền đen, giữ tỷ lệ, dải đen ghi tên + attribution; **không crop/kéo giãn**).
- Số liệu đọc từ **Results/Table** của bài gốc, không lấy từ abstract. Riêng mô hình nguy cơ vỡ (bảng 5 dòng ở mục 1) lấy từ Table 4 của PMC11351075.
- **Ngưỡng "ho ra máu ồ ạt" không thống nhất giữa các nguồn:** ≥ 200 mL/ngày (PMC11351075) vs > 500 mL/ngày (PMC10426096) vs > 100 mL/lần hoặc > 500 mL/24 giờ (bài 091). Đã ghi rõ trong bài, không tự chọn một ngưỡng.
- **Kiểm chứng tác giả:** Akis S (PMC12634792), Liu M (PMC11351075), Li FQ (PMC10426096), Chen Y (PMC13266778) — đối chiếu `authorString` Europe PMC ngày 2026-10-27.
- **Phản biện nguồn:** chú thích Fig. 4 của PMC11351075 ghi thuốc tràn vào "hang và khí quản"; trên ảnh chỉ thấy rõ thuốc trong túi/hang — bài ghi nhận sự không khớp, không sửa chú thích gốc.
