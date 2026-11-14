# Nguồn gốc — 1473 Viêm xoang nấm xâm lấn cấp lan hốc mắt (AIFS)

> Quét Europe PMC (open access) ngày 2026-11-14; ưu tiên bài có **thang điểm định lượng**, **đường lan giải phẫu** và **hình minh họa có giấy phép rõ ràng**.

| # | Nguồn | Tiêu đề | Link gốc | Giấy phép ảnh | Tải về? |
|---|---|---|---|---|---|
| 1 | *World J Radiol* 2024 | Proposed computed tomography severity index for the evaluation of invasive fungal sinusitis: Preliminary results (66 ca COVID-19, CTSI 1–25) | https://europepmc.org/article/PMC/PMC11718521 · doi:10.4329/wjr.v16.i12.771 | CC BY-NC 4.0 | `images/1473_aifs-nhe_CT_PMC11718521.jpg` (Fig. 2), `images/1473_aifs-nang_CT_PMC11718521.jpg` (Fig. 3), `images/1473_aifs-roc_PMC11718521.jpg` (Fig. 5) |
| 2 | *J Family Med Prim Care* 2023 | Imaging spectrum, associations and outcomes in acute invasive fungal rhino-ocular-cerebral sinusitis in patients with COVID-19 pneumonia | https://europepmc.org/article/PMC/PMC10451586 · doi:10.4103/jfmpc.jfmpc_1189_22 | CC BY-NC-SA 4.0 | `images/1473_aifs-mri-xoanang_MRI_PMC10451586.jpg` (Fig. 2), `images/1473_aifs-lan-PPF_MRI_PMC10451586.jpg` (Fig. 4) |
| 3 | *AJNR* 2019 | The Black Turbinate Sign, A Potential Diagnostic Pitfall: Evaluation of the Normal Enhancement Patterns of the Nasal Turbinates (75 MRI người không bệnh) | https://pubmed.ncbi.nlm.nih.gov/31000527/ · doi:10.3174/ajnr.A6037 | không dùng ảnh — **chỉ trích số liệu** | không tải |
| 4 | *Curr Opin Otolaryngol Head Neck Surg* 2025 | Imaging approach for fungal sinusitis (tổng quan: CT ưu thế cho hủy xương/nốt tăng đậm, MRI cho mô mềm/niêm mạc) | https://pubmed.ncbi.nlm.nih.gov/39382179/ · doi:10.1097/MOO.0000000000001018 | không dùng ảnh — **chỉ trích nội dung** | không tải |

## Số liệu đã dùng (truy nguyên được)

- **Tử vong 50–80%** khi đã có biến chứng hốc mắt/nội sọ (nguồn #1, phần Introduction).
- Đoàn hệ **66 ca**: tuổi trung vị **48,5**; nam **84,85%**; đái tháo đường **77,27%**; HbA1c **≥ 6,5** ở **84,85%**; một bên **90,91%**, **hai bên 9,09%** (liên quan tử vong **p=0,004**); tử vong **15,15%**; đáp ứng điều trị **65,15%** (nguồn #1, Table 2–4).
- **CTSI**: nhẹ **1–8** (51,52%), vừa **9–16** (42,42%), nặng **≥ 17** (6,06%); điểm trung bình đáp ứng **6,3** vs không đáp ứng **12,9** (p<0,001); **ngưỡng 11**: nhạy **78,26%**, đặc hiệu **95,35%** (nguồn #1, abstract + Table 1, 5).
- Bảng điểm chi tiết từng vùng: chép từ **Table 1** của nguồn #1 (mục 4.2 trong `lesson.md`).
- **Turbinate đen xuất hiện ở 30%** MRI người **không** có bệnh nấm, đa số ở **phần sau cuốn mũi dưới** (nguồn #3).
- CT ưu thế cho **hủy xương và nốt tăng đậm (yếu tố nấm)**; MRI ưu thế cho **mô mềm và niêm mạc**; dấu sớm có thể **rất kín đáo** (nguồn #4).
- Điều trị: **cắt lọc rộng sớm** + amphotericin B liposomal **5–10 mg/kg/ngày** (khuyến cáo ECMM/ISHAM 2019) + kiểm soát đường huyết/nhiễm toan ceton — **nội dung guideline, không trích hình**.

## Ghi chú giấy phép
- 5 ảnh gốc: **CC BY-NC 4.0** (PMC11718521) và **CC BY-NC-SA 4.0** (PMC10451586) — cả hai cho phép tái bản phi thương mại; ảnh SA khi chỉnh sửa phải giữ **cùng giấy phép** (đã ghi trong CREDITS).
- **1 ảnh ghép** (`composite_1473_aifs-nhe-vs-nang.jpg`) ghép từ 2 ảnh **cùng bài, cùng chuỗi** (PMC11718521) bằng `tools/make_composite.py` — letterbox, **không crop, không kéo giãn**.
- **Không ghi tên tác giả** trong CREDITS/lesson vì chưa đối chiếu từng tác giả với từng PMCID; định danh bằng **tạp chí, năm, PMCID**.
- Không dùng nguồn trả phí/AuntMinnie; không dùng ảnh có giấy phép mơ hồ.
