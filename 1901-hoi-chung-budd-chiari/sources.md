# Nguồn gốc — 1901-hoi-chung-budd-chiari (hội chứng Budd–Chiari)

> Quét ngày 2026-10-27. Chủ đề: BCS — cơ chế "flip-flop", chẩn đoán hình ảnh, phân độ tiên lượng và bậc thang can thiệp (nong bóng/stent → TIPS → ghép). Kiểm chứng giấy phép từng ảnh trước khi tải.

| # | Nguồn | Tiêu đề / Ca | Link gốc | Giấy phép ảnh | Tải về? |
|---|---|---|---|---|---|
| 1 | Europe PMC / PMC10341099 | Porrello G, Mamone G, Miraglia R. *Budd–Chiari Syndrome Imaging Diagnosis: State of the Art and Future Perspectives*, Diagnostics 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10341099/ | CC BY 4.0 | **Fig. 1** (tắc TM gan + mosaic), **Fig. 3** (shunt trong gan), **Fig. 4** (flip-flop CT+MRI), **Fig. 5** (hạch đuôi) + ảnh ghép |
| 2 | Europe PMC / PMC10137827 | Rössle M. *Interventional Treatment of Budd–Chiari Syndrome*, Diagnostics 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10137827/ | CC BY 4.0 | **Fig. 1** (sơ đồ + cavogram chèn IVC), **Fig. 4** (Doppler hẹp stent 200 cm/s) |
| 3 | Europe PMC / PMC9689902 | Mancuso A et al. *Budd–Chiari Syndrome Management: Controversies and Open Issues*, Diagnostics 2022 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9689902/ | CC BY 4.0 | không tải ảnh (dùng cho **Clichy criteria**, tỷ lệ sống với nội khoa đơn thuần, tranh luận thời điểm TIPS) |
| 4 | Europe PMC / PMC10143067 | *Hepatic Venous Occlusion Type of Budd–Chiari Syndrome versus Pyrrolizidine Alkaloid-Induced Hepatic Sinusoidal Obstruction Syndrome*, J Pers Med 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10143067/ | CC BY 4.0 | không tải ảnh (đối chiếu **SOS/VOD** — chỉ dùng tên chủ đề, chưa trích số) |
| 5 | Europe PMC / PMC10378170 | *Focal Liver Lesions in Budd–Chiari Syndrome: Spectrum of Imaging Findings*, Diagnostics 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10378170/ | CC BY 4.0 | không tải ảnh (đối chiếu **nốt tái tạo/FNH-like vs HCC** — dùng nguyên tắc thì gan đặc hiệu) |
| 6 | Radiopaedia | Budd–Chiari syndrome (chỉ dẫn link) | https://radiopaedia.org/articles/budd-chiari-syndrome | CC BY-NC-SA (từng ca) | **không tải** — chỉ dẫn link |
| 7 | The Radiology Assistant (RNL) | Portal hypertension / liver vascular (chỉ dẫn link) | https://radiologyassistant.nl/ | giáo dục — dẫn link | **không tải** — chỉ dẫn link |
| 8 | AuntMinnie | Case of the Day (chỉ dẫn link) | https://www.auntminnie.com | chỉ dẫn link (paywall) | **không tải** |

## Ghi chú giấy phép
- **CC BY 4.0** (PMC10341099, PMC10137827, PMC9689902): dùng được, tạo phái sinh, **kèm ghi công**; ảnh ghép letterbox từ **Fig. 4 + Fig. 5 của PMC10341099**, ghi rõ **đã thay đổi**.
- Ảnh gốc lấy từ gói `supplementaryFiles` của Europe PMC (`.jpg`), **không đổi pixel**.
- Không có ảnh nào của Radiopaedia/AuntMinnie trong repo.

## Ghi chú trung thực nội dung
- **Tên tác giả** lấy trực tiếp từ danh sách tác giả của bài gốc (PMC10341099; PMC10137827 là bài một tác giả), **không suy đoán**.
- Các con số giữ đúng nguồn: phì đại hạch đuôi **~50%**; TM hạch đuôi **> 3 mm**; US dấu trực tiếp + hạch đuôi to **Sp 100%**; MRA **Se 97,6%/Sp 70,7%**; cổ trướng **56%**, bàng hệ ngoài gan **44%**; nội khoa **80–90% không đáp ứng bền**, **~2/3 không sống dài hạn**; stent vs nong đơn thuần **2% vs 40%** tái hẹp, sống không tái hẹp 3 năm **96% vs 60,4%**; áp lực cửa **40,4 ± 10,1 → 10,8 ± 4,9 mmHg**; tốc độ TM cửa **12,7 ± 10,0 → 48,6 ± 16,9 cm/s**; Doppler stent **< 60 / > 180 cm/s**, **200 cm/s ≈ 16 mmHg**; sống sau TIPS **1 năm 80–100%, 5 năm 74–78%**, **88/78/70%** (124 ca), **95/90/80%** (59 ca); HE trước TIPS **10%**, sau TIPS **0–20%**; kháng thể heparin **~30%**.
- **Điểm chưa kiểm chứng trong lượt này:** thành phần **Rotterdam score** không được trích chi tiết (chỉ nêu vai trò tiên lượng đã xác nhận trong bài gốc) → bài **không liệt kê công thức**. Tỷ lệ HCC theo thời gian ở BCS **không đưa số** vì chưa đối chiếu được dữ liệu gốc.
- **Ngưỡng "IVC giãn"** không ghi số mm vì nguồn trong lượt không nêu ngưỡng cụ thể — bài dùng mô tả **giãn + không xẹp theo nhịp thở + reflux**.

- **Lượt này Europe PMC Search trả lỗi 503** khi chạy `check_credits_authors.py` → 4 PMCID mới **chưa được đối chiếu tự động**; tên tác giả vì vậy lấy **trực tiếp từ danh sách tác giả trong XML full-text của chính bài** (đã đối chiếu PMCID), không suy đoán. Khi mạng ổn định nên chạy lại cổng authors.
