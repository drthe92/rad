# CREDITS — ảnh bài 1749 (Hội chứng nhân đôi đuôi)

Mỗi ảnh ghi rõ: file trong repo, hình gốc, bài gốc (PMCID), giấy phép, thay đổi phái sinh (nếu có).

| File | Hình gốc | Bài gốc | Giấy phép | Phái sinh |
|---|---|---|---|---|
| `composite_bang-quang-doi-axial-coronal.jpg` | Hình 1, panel **B** (CT niệu đồ thì bài xuất, lát trục — hai bàng quang) + panel **C** (MPR vành — vách giữa hai bàng quang) | Cureus 2026, PMCID **PMC12863223** — https://europepmc.org/article/PMC/PMC12863223 | **CC BY 4.0** | **Có**: cắt hai panel CT (bỏ panel lâm sàng A, D, E, F) + ghép letterbox bằng `tools/make_composite.py`, dải đen ghi tên hình + attribution |
| `1749_cds_CT-nieu-do-PMC12863223-F1B.jpg` | Hình 1, panel B (CT niệu đồ lát trục, hai bàng quang) | Cureus 2026, PMCID **PMC12863223** | **CC BY 4.0** | **Có**: cắt từ Hình 1, phóng 2× |
| `1749_cds_CT-nieu-do-PMC12863223-F1C.jpg` | Hình 1, panel C (MPR vành, vách giữa hai bàng quang) | Cureus 2026, PMCID **PMC12863223** | **CC BY 4.0** | **Có**: cắt từ Hình 1, phóng 2× |
| `1749_cds_MRI-tuy-cot-song-PMC13634463-F2.jpg` | Hình 2 — MRI T2 sagittal/axial cột sống – khung chậu (nhãn trong ảnh: right/left bladder, right/left colon, myelocystocele, uterus) | Urol Case Rep 2026, PMCID **PMC13634463** — https://europepmc.org/article/PMC/PMC13634463 | **CC BY-NC-ND 4.0** | **Không** — nguyên bản (chỉ đổi định dạng webp → jpg, không cắt/ghép/đổi chữ) |
| `1749_cds_Xquang-CT-xuong-nieu-do-PMC13634463-F3.jpg` | Hình 3 — A X-quang bụng; B dựng hình 3D xương; C niệu đồ ngược dòng; D CT axial; E CT vành | Urol Case Rep 2026, PMCID **PMC13634463** | **CC BY-NC-ND 4.0** | **Không** — nguyên bản (đổi định dạng webp → jpg) |
| `1749_cds_VR-hai-dai-trang-PMC13614799-F2.jpg` | Hình 2 — a MCUG; b CT niệu đồ; c dựng hình 3D hai đại tràng + hai bàng quang; d ảnh mổ | J Indian Assoc Pediatr Surg 2026, PMCID **PMC13614799** — https://europepmc.org/article/PMC/PMC13614799 | **CC BY-NC-ND 4.0** (khối license ghi NC-ND; URL kèm theo trỏ NC-SA → xử lý theo hướng thận trọng hơn) | **Không** — nguyên bản (đổi định dạng webp → jpg) |

## Ghi chú
- **CC BY 4.0** (Cureus): được cắt/ghép cho mục đích học tập, miễn ghi công + ghi rõ phái sinh. Hai panel **A và F** (ảnh lâm sàng bộ phận sinh dục trẻ) **không đưa vào repo** — chỉ dùng phần hình ảnh học.
- **CC BY-NC-ND 4.0** (Urol Case Rep; JIAPS): chỉ đăng **nguyên bản**, không tạo tác phẩm phái sinh → **không** cắt, **không** ghép composite, **không** phủ chữ; giữ nguyên cả nhãn tiếng Anh in trên hình.
- **Không tạo composite từ ảnh NC-ND**; composite duy nhất của bài dựng từ ảnh **CC BY 4.0**.
- **Tên tác giả KHÔNG ghi**: attribution dùng **tạp chí + năm + PMCID** (đối chiếu Europe PMC ngày 2026-11-06).
- Ảnh tải từ **cdn.ncbi.nlm.nih.gov/pmc/blobs/...** (đúng file figure trong bài gốc), không lấy từ trang trung gian.
- Ảnh không chứa tên bệnh nhân; một số ảnh có **overlay DICOM** (ngày chụp, thông số kV/mAs) — đây là overlay của bài gốc, **giữ nguyên** vì ảnh NC-ND không được sửa.
