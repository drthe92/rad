# CREDITS — 429 Đo trục nhãn cầu bằng MRI/CT khi sinh trắc và A-scan thất bại

Mỗi ảnh dưới đây ghi rõ **nguồn, bài gốc, giấy phép, có phái sinh hay không**. Không ảnh nào lấy từ nguồn không rõ giấy phép.

| File | Nội dung | Nguồn | Giấy phép | Phái sinh |
|---|---|---|---|---|
| `429_do-truc-nhan-cau_Sodo_CC0.png` | Sơ đồ 2 phần: (A) cửa sổ đo đỉnh giác mạc → hoàng điểm so với trục qua gai thị; (B) bốn con số AL trên cùng một mắt 24 mm khi có 12 mm khí / 16 mm dầu | **Tự vẽ** trong repo (Pillow), không dùng ảnh bệnh nhân | **CC0 1.0** (public domain dedication) | Nguyên bản |
| `429_do-truc-nhan-cau_MRI_BMC2022-Fig1.jpg` | MRI T2 3T lát ngang: định vị tâm nhãn cầu trên 3 mặt phẳng trực giao, đặt thước đo AL trên lát ngang (ảnh gốc Fig. 1) | BMC Ophthalmol 2022;22:54 — “Measuring axial length of the eye from magnetic resonance brain imaging” — https://europepmc.org/article/PMC/PMC8817515 (PMC8817515, DOI 10.1186/s12886-022-02289-y) | **CC BY 4.0** | Nguyên bản (chỉ đổi tên file) |
| `429_do-truc-nhan-cau_MRI_BMC2022-Fig2.jpg` | Ba biểu đồ Bland–Altman: AL đo bằng Mango / ITK / Carestream so IOLMaster 500 (n = 93) (ảnh gốc Fig. 2) | Như trên — BMC Ophthalmol 2022 (PMC8817515) | **CC BY 4.0** | Nguyên bản (chỉ đổi tên file) |
| `composite_429_cua-so-do-va-dong-thuan.jpg` | Ghép cạnh nhau Fig. 1 + Fig. 2 của cùng bài, letterbox nền đen, dải attribution in trong ảnh | Như trên — BMC Ophthalmol 2022 (PMC8817515) | **CC BY 4.0** (cho phép phái sinh, có ghi công) | **Ảnh ghép** bằng `tools/make_composite.py`: letterbox, **không crop, không kéo giãn**; attribution ghi trong dải đen |
| `429_do-truc-nhan-cau_CT_BMC2025-Fig1.jpg` | CT sọ không cản quang (A–J): tăng đậm độ trong não thất trái và trong **nhãn cầu + dây thị giác phải** do dầu silicone (ảnh gốc Fig. 1) | BMC Ophthalmol 2025;25:… — “Intraventricular silicone oil migration post-retinal detachment surgery: diagnostic features and classification” — https://europepmc.org/article/PMC/PMC11883950 (PMC11883950, DOI 10.1186/s12886-025-03924-0) | **CC BY-NC-ND 4.0** | **Nguyên bản, KHÔNG crop/ghép/chỉnh sửa** (điều kiện ND); hiển thị nguyên hình |

## Ghi chú

- Ảnh **CC BY-NC-ND** (dầu silicone trong não thất) chỉ được hiển thị **nguyên bản**: không cắt, không ghép, không đổi màu — đúng điều kiện của giấy phép.
- Ảnh **CC BY 4.0** được phép phái sinh; ảnh ghép giữ **tỷ lệ gốc** (letterbox), không làm biến dạng giải phẫu.
- Bài **Br J Ophthalmol 2002 (PMC1770965)** chỉ dùng **số liệu** (12 mắt, 50% ±1 D, 75% ±2 D), **không dùng ảnh** vì không có khối giấy phép CC rõ ràng.
- Không ghi tên tác giả khi chưa đối chiếu trực tiếp với PMCID; các attribution ở đây dùng **tạp chí + năm + PMCID**.
