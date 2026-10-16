# Nguồn — 456 Bệnh võng mạc trẻ sinh non (ROP)

> Tổng hợp y văn mở. Ảnh tải về ghi giấy phép từng file ở `images/CREDITS.md`; nguồn không tải được thì **chỉ dẫn link**.

## Bài tổng quan / phân loại (nguồn chính)
- **Phân loại ROP (ICROP, zone–stage–plus, AP-ROP):** Molinari A, Weaver D, Jalali S. Classifying retinopathy of prematurity. Community Eye Health. 2017;30(99):55–56. — PMCID: PMC5806220 (CC BY-NC 4.0). https://pmc.ncbi.nlm.nih.gov/articles/PMC5806220/ (Fig. 1–9: 5 giai đoạn, 3 vùng, plus, AP-ROP, di chứng; "điều trị trong 48 giờ" khi zone I/plus/AP-ROP.)
- **Dịch tễ + điều trị hiện tại (Type 1/Type 2, laser, anti-VEGF):** Hong EH, Shin YU, Cho H. Retinopathy of prematurity: a review of epidemiology and current treatment strategies. Clin Exp Pediatr. 2022;65(3):115–126. — PMCID: PMC8898617 (CC BY-NC 4.0). https://pmc.ncbi.nlm.nih.gov/articles/PMC8898617/ (tỷ lệ ROP 10–40%; Type 1 = zone I + plus / zone I stage 3 / zone II stage 2–3 + plus; í́t nhất điều trị 48–72 giờ; anti-VEGF theo dõi đến ≥ 65 tuần PMA, nguy cơ tái hoạt 45–55 tuần; BEAT-ROP tái phát 7,2%.)
- **Hướng dẫn đồng thuận quốc gia (sàng lọc theo lịch, bảng tuổi khám lần đầu):** Turkish Neonatal and Turkish Ophthalmology Societies consensus guideline on the retinopathy of prematurity. Turk Pediatri Ars. 2018;53(Suppl 1):S3–S16. — PMCID: PMC6568303 (CC BY-NC-SA 4.0). https://pmc.ncbi.nlm.nih.gov/articles/PMC6568303/ (BW ≤ 1500 g và/hoặc GA ≤ 30 tuần; bảng khám lần đầu theo tuổi thai: 22 tuần → 31 tuần PMA/9 tuần tuổi thực… 30 tuần → 34 tuần PMA/4 tuần tuổi thực; zone I mỗi tuần, zone II ≥ 2 tuần, zone III 2–3 tuần; threshold cũ 5/8 giờ đồng hồ.)

## Ca / hình ảnh minh họa (CC BY)
- **Phát triển mạch võng mạc non tháng + định nghĩa zone (RetCam):** Jang JH, Kim YC. Retinal vascular development in an immature retina at 33–34 weeks postmenstrual age predicts retinopathy of prematurity. Sci Rep. 2020;10:18111. — PMCID: PMC7582165 (CC BY 4.0). https://pmc.ncbi.nlm.nih.gov/articles/PMC7582165/ (Fig. 3: zone I = 2 DF; Fig. 4: chuỗi diễn tiến pre-plus → plus.)
- **Schema 5 giai đoạn + plus (nhãn):** Tong Y, Lu W, Deng QQ, Chen C, Shen Y. Automated identification of retinopathy of prematurity by image-based deep learning. Eye Vis (Lond). 2020;7:40. — PMCID: PMC7395360 (CC BY 4.0). https://pmc.ncbi.nlm.nih.gov/articles/PMC7395360/ (Fig. 2: panel a–f — demarcation line/ridge/tăng sinh xơ-mạch/stage 4/stage 5/plus.)
- **Thuật toán cân nặng sau sinh dự báo ROP nặng/Type 1 (tham khảo thêm):** Athikarisamy S et al. The Use of Postnatal Weight Gain Algorithms to Predict Severe or Type 1 Retinopathy of Prematurity: A Systematic Review and Meta-analysis. JAMA Netw Open. 2021;4(11):e2135879. — PMCID: PMC8611486 (CC BY 4.0). https://pmc.ncbi.nlm.nih.gov/articles/PMC8611486/

## Ngưỡng số / bảng tóm tắt trong bài
- Sàng lọc: **GA ≤ 30 tuần và/hoặc BW ≤ 1500 g**; mở rộng GA 30–32 tuần/BW 1500–2000 g có bệnh cảnh nặng.
- Khám lần đầu: **31–33 tuần PMA** hoặc **4 tuần tuổi thực** (lấy mốc muộn hơn); theo dõi zone I **1 tuần** / zone II **≥ 2 tuần** / zone III **2–3 tuần**.
- ICROP zone I = **2 DF** (DF = khoảng cách đĩa thị–hoàng điểm).
- ETROP **Type 1** (điều trị 48–72 giờ): zone I + plus; zone I stage 3; zone II stage 2–3 + plus; **AP-ROP**.
- "Threshold" lịch sử: stage 3 liền **5 giờ** hoặc cộng dồn **8 giờ** + plus (zone I/II) = nguy cơ bong **50%**.
- Anti-VEGF: theo dõi đến **≥ 65 tuần PMA**; cao điểm tái hoạt **45–55 tuần PMA**.

## Tham khảo chéo trong repo
- Bài 400 (tổng quan Mắt), 450 (mắt nhi/leukocoria), 443 (tân mạch võng mạc ĐTĐ), 445 (bong võng mạc), 411 (siêu âm nhãn cầu), 412 (u trong nhãn cầu), 610 (oxy liệu pháp sơ sinh).
- Radiopaedia — Retinopathy of prematurity: https://radiopaedia.org/articles/retinopathy-of-prematurity (dẫn link; ảnh theo CC BY-NC-SA khi trích riêng từng case).
- AuntMinnie Case of the Day: https://www.auntminnie.com — paywall, **chỉ dẫn link, không tải**.
