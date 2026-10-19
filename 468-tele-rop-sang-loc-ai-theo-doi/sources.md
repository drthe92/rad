# Nguồn — 468 (Sàng lọc ROP từ xa (tele-ROP) & trí tuệ nhân tạo (AI))

> Chủ đề: **tele-ROP & AI** — mạng lưới sàng lọc ROP ở nơi thiếu chuyên gia; ảnh võng mạc góc rộng (WFDRI) vs chụp bằng điện thoại (SBFI); học sâu (deep learning), thang độ nặng mạch máu (vascular severity score — VSS 1–9), bản đồ nhiệt giải thích; quy trình chụp/đọc ảnh.
> Nguồn ảnh: bài **mở** (open access), kiểm tra giấy phép từng bài; tác giả đối chiếu trực tiếp `authorString` qua Europe PMC.

## Nguồn chính (có ảnh / lấy số liệu)

| PMCID | Tài liệu | Giấy phép | Dùng cho |
|---|---|---|---|
| PMC9583350 | Tan Z et al., *Saudi J Ophthalmol* 2022 — Retinopathy of prematurity screening: narrative review of programs, teleophthalmology, and diagnostic support systems | CC BY-NC-SA 4.0 | 3 phương thức (BIO/WFDRI/tele-ROP); "đại dịch ROP thứ ba"; sơ đồ luồng tele-ROP có CBIA/AI; tiêu chí sàng lọc khác nhau giữa các nước |
| PMC5398746 | Thanos A et al., *Eye Brain* 2016 — Screening and treatments using telemedicine in ROP | CC BY-NC 3.0 | Bộ 5–6 ảnh chuẩn; giao diện đọc ảnh (mức mạch, giai đoạn, zone); công cụ xác định zone I tự động |
| PMC6928229 | Wintergerst MWM et al., *Sci Rep* 2019 — Non-contact smartphone-based fundus imaging vs conventional fundus imaging | CC BY 4.0 | SBFI: trường nhìn **1:2,5**, thời gian khám **109,0 ± 57,8 s** vs **75,9 ± 36,3 s** (p < 0,01); đồng thuận plus κ 0,88 / stage κ 0,81; Se/Sp plus **90%/100%**, ROP **88%/93%** |
| PMC8100867 | Wang J et al., *JAMA Netw Open* 2021 — Automated explainable multidimensional deep learning platform (14 108 mắt, 8 652 trẻ, 52 249 ảnh) | CC BY 4.0 | 4 bộ phân loại; **AUC 0,983–0,998**, hệ chuyển tuyến AUC **0,9901–0,9956**; bản đồ nhiệt CAM/DeepSHAP |
| PMC8363465 | Zhang J et al., *J Ophthalmol* 2021 — Accuracy of DL algorithms for ROP: systematic review & meta-analysis | CC BY 4.0 | Gộp 9 nghiên cứu/15 bộ phân loại: **Se 0,953**, **Sp 0,975**, **SROC AUC 0,984**; ROP vs normal AUC 0,990 |
| PMC9754980 | Cole E et al., *Ophthalmol Sci* 2022 — Evaluation of an AI system for ROP screening in Nepal and Mongolia | CC BY-NC-ND 4.0 | i-ROP DL; VSS 1–9; type 1 ROP **14,0% (Mongolia) vs 2,2% (Nepal)**; AUC VSS–plus 0,999/0,968 (giữ nguyên bản) |
| PMC8620568 | Attallah O, *Diagnostics (Basel)* 2021 — DIAROP: automated DL diagnostic tool for ROP | CC BY 4.0 | Độ chính xác **93,2%**, AUC **0,98**; 5 pha pipeline |
| PMC8192130 | Guo Z et al., *BMC Ophthalmol* 2021 — Telemedicine-assisted ROP screening during COVID-19 | CC BY 4.0 | Hẹn trực tuyến hoàn thành **58,1% vs 22,1%** trực tiếp (p = 0,018); 2020 (54 trẻ) ≥ 2019 (51 trẻ) |

## Nguồn số liệu bổ trợ (không lấy ảnh)

| PMCID | Tài liệu | Giấy phép | Dùng cho |
|---|---|---|---|
| PMC11890260 | *Med Hypothesis Discov Innov Ophthalmol* 2024 — A review on retinopathy of prematurity | CC BY-NC-ND 4.0 | Tổng quan bối cảnh, thuật ngữ |
| PMC7406614 | *Ophthalmol Ther* 2020 — The role of telemedicine... ROP | CC BY-NC 4.0 | Vai trò tele-ROP trong hệ thống y tế |
| PMC10414056 | *BMJ Open Ophthalmol* 2023 — Fairness and generalisability in DL ROP screening: literature review | CC BY-NC 4.0 | Cảnh báo **dịch chuyển miền (domain shift)/công bằng** giữa các dân số |
| PMC2720584 | *Graefes Arch Clin Exp Ophthalmol* 2009 — Wide-field digital imaging based telemedicine (6 năm) | (theo bài) | Tiền lệ tele-ROP quy mô lớn |

## Nguồn tham khảo mô tả (chỉ dẫn link — không tải ảnh)
- **Radiopaedia — Retinopathy of prematurity:** https://radiopaedia.org/articles/retinopathy-of-prematurity
- **AuntMinnie (Case of the Day):** https://www.auntminnie.com/ — **chỉ dẫn link**, không tải ảnh.
- **AAO — Retinopathy of Prematurity PPP (Preferred Practice Pattern):** https://www.aao.org/preferred-practice-pattern/retinopathy-of-prematurity-ppp

## Phân độ & protocol (tóm tắt)
- **Phân độ ICROP (bài [456](../456-benh-vong-mac-tre-sinh-non/lesson.md)):** zone I–III × stage 1–5 × plus/pre-plus; AP-ROP.
- **Type 1 (ETROP):** zone I bất kỳ stage **có plus**; zone I **stage 3**; zone II **stage 2–3 có plus** → điều trị **48–72 giờ**.
- **AI:** gán **VSS 1–9**; ngưỡng hành động lấy theo **điểm vận hành (operating point)** đã kiểm định trên đúng máy/đúng dân số.
- **Lịch theo dõi:** zone I mỗi **1 tuần**, zone II–III mỗi **1–2 tuần**; sau điều trị anti-VEGF theo dõi tới **≥ 65 tuần PMA** (bài [458](../458-di-chung-theo-doi-dai-han-sau-rop/lesson.md)).
