# Nguồn — 3312 Đếm tế bào nội mô giác mạc (ECD) sau ghép và sau rebubble

> Bài tổng hợp y văn, rà soát 11/2026 (PubMed/PMC). Mọi số trong `lesson.md` lấy từ các nguồn dưới đây; nguồn không có toàn văn mở chỉ dùng số trong abstract và ghi rõ.

## Đo trường rộng, vùng trung tâm so với ngoại vi

1. Cheong EZK, Win KY, Wong QY, Sim R, Ng Yin Ling C, Htoon HM, Ong HS, Mehta JS, Tan B, Schmetterer L, Ang M. **Deep learning-assisted widefield endothelial imaging in Descemet membrane endothelial keratoplasty.** *Front Med (Lausanne).* 2025;12:1715673. DOI: 10.3389/fmed.2025.1715673. PMCID: PMC12669210.
   https://pmc.ncbi.nlm.nih.gov/articles/PMC12669210/
   - **53 mắt / 43 người**, DMEK ≥ 12 tháng, chụp siêu soi trường rộng **CEM-530** tại **15 vị trí**: 1 trung tâm, 8 cạnh trung tâm (**0,65–0,80 mm**), 6 ngoại vi (**3,65–4,00 mm**); vùng trung tâm trong **đường kính 1,3 mm**, ngoại vi là **vành 7,3 mm**; mỗi ảnh **0,55 × 0,25 mm**.
   - **1.362 ảnh**: **18,9% (258)** không đọc được, **81,1%** dùng được. Grade 1 **< 25%** diện tích đọc được; grade 2 **25–50%**; grade 3 **50–75%**; grade 4 **> 75%**.
   - ECD trung tâm **1.709 → 1.555** và ngoại vi **1.498 → 1.347 tế bào/mm²** sau 6 tháng (p < 0,001 và p = 0,016); mất trung tâm **5,81%/năm** (95% CI 3,54–8,08).
   - Hình 3B: một mắt **trung tâm không giảm**, **ngoại vi giảm trung bình 769 tế bào/mm²**.
   - Ngưỡng ECD thấp dùng trong mô hình học sâu: **< 1.000 tế bào/mm²**; AUC phát hiện ECD thấp **0,980**.

## Đoàn hệ DMEK: quỹ đạo ECD, rebubble, ngưỡng

2. Chaussard D, Bloch F, Elnar AA, Zevering Y, Vermion JC, Moskwa R, Perone JM. **Identification of the preoperative and perioperative factors that predict postoperative endothelial cell density after Descemet membrane endothelial keratoplasty: a retrospective cohort study.** *PLoS One.* 2022;17(2):e0264401. DOI: 10.1371/journal.pone.0264401. PMCID: PMC8870504.
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8870504/
   - **103 mắt / 95 người** DMEK do Fuchs, theo dõi 12 tháng; đo bằng **NIDEK CEM-530**.
   - ECD mảnh ghép **2.557** trước mổ → **1.403** (6 tháng, **mất 45%**) → **1.244** (12 tháng, **mất 51%**); **10%** thất bại mảnh ghép phải ghép lại.
   - Tổng quan trong bài: DMEK mất **30–40%** tế bào trong 12 tháng đầu, sau đó **~7%/năm**.
   - Rebubble **34%**: **25%** một lần, **9%** > 1 lần; cần **lần thứ tư** → coi là thất bại.
   - Ngưỡng **< 1.000 tế bào/mm²** được chọn vì các hội nhãn khoa coi là ngưỡng nguy cơ mất bù. Nhóm **bóc mảnh ghép khó** có trung vị ECD 12 tháng **945** so với **1.331** ở nhóm không khó (p = 0,01); nhóm **khó mở mảnh ghép 800** so với 1.331 (p = 0,07). Rebubble **không** liên quan ECD trong đoàn hệ này.

## Tái lập, so sánh thiết bị, ảnh hưởng của bệnh giác mạc

3. Luft N, Hirnschall N, Schuschitz S, Draschl P, Findl O. **Comparison of 4 specular microscopes in healthy eyes and eyes with cornea guttata or corneal grafts.** *Cornea.* 2015;34(4):381–386. DOI: 10.1097/ICO.0000000000000385.
   - **22 mắt khỏe, 16 mắt guttata, 31 mắt PK/DSAEK**; 4 máy siêu soi.
   - Tỷ lệ đo thành công **100%** ở mắt khỏe, **64,5–93,5%** ở mắt ghép, **0–18,8%** ở mắt guttata.
   - ECD khác nhau **có ý nghĩa** giữa 4 thiết bị (p < 0,01).

4. Al Farhan HM, Al Otaibi WM, Al Razqan HM, Al Harqan AA. **Assessment of central corneal thickness and corneal endothelial morphology using ultrasound pachymetry, non-contact specular microscopy, and Confoscan 4 confocal microscopy.** *BMC Ophthalmol.* 2013;13:73. DOI: 10.1186/1471-2415-13-73. PMCID: PMC4222699.
   https://pmc.ncbi.nlm.nih.gov/articles/PMC4222699/
   - **30 mắt** người khỏe; siêu soi **SP-2000P** và confocal **z-ring CS4**, mỗi lần đếm **50 tế bào liền nhau**.
   - ECD **3.115,5 ± 279,7** so với **3.167,5 ± 264,8 tế bào/mm²**; chênh **52,1 ± 97,9** (p = 0,46) → đồng thuận trên mắt khỏe.

5. Vidal-Villegas, Burgos-Blasco và cộng sự. **Corneal endothelial validation in the eye bank: differences in automated methods and repeatability.** *J Fr Ophtalmol.* 2024. DOI: 10.1016/j.jfo.2023.09.017.
   - **54 giác mạc hiến**, máy **Konan Cell Check D**, 2 người đọc.
   - Phương pháp **center** đếm **≥ 30 tế bào liền nhau**; **flex-center** khoanh vùng.
   - ICC ECD **0,821** (center) và **0,784** (flex-center); **CV diện tích tế bào và hexagonality có độ tin cậy kém** (ICC ≤ 0,265).
   - Flex-center cho ECD **cao hơn** có ý nghĩa (p = 0,013), rõ nhất khi ECD < 2.700.

6. Kelekele, Kayembe Lubeji và cộng sự. **Interocular symmetry and repeatability of central corneal thickness and corneal endothelial cell morphology and density in healthy eyes of Congolese.** *Semin Ophthalmol.* 2022. DOI: 10.1080/08820538.2021.1974497.
   - **278 mắt khỏe**, 3 lần đo/mắt bằng siêu soi không tiếp xúc.
   - **ICC ECD 0,95** (95% CI 0,94–0,96); **CV 2,4% ± 3,9%**; **test–retest SD 17,7 ± 7,7 tế bào/mm²**.
   - Chênh hai mắt: trung bình **0,5 ± 90,8**; giới hạn 2,5–97,5% **−177,4…+182,0 tế bào/mm²**.

7. Goldich, Marcovich và cộng sự. **Comparison of corneal endothelial cell density estimated with 2 noncontact specular microscopes.** *Eur J Ophthalmol.* 2010;20(5). DOI: 10.1177/112067211002000503.
   - **40 mắt**; **EM-935 tự động 2.483 ± 159** so với **bán tự động 2.635 ± 190** (p < 0,001); **Noncon Robo 2.531 ± 244**.
   - **95% giới hạn đồng thuận −435…+339 tế bào/mm²** (Noncon so với tự động); ICC tự động **0,50**, bán tự động **0,80**.

8. Campolmi N, He Z, Acquart S, Trone MC, Bernard A, Gauthier AS, Garraud O, Forest F, Péoc'h M, Gain P, Thuret G. **Comparison of endothelial cell density of organ cultured corneas with cornea donor study.** *Cornea.* 2014;33(6):597–603. DOI: 10.1097/ICO.0000000000000124.
   - **3.052 giác mạc** ngân hàng mắt; đếm **> 300 tế bào trên 3 vùng của 8 mm trung tâm**.
   - So với chuẩn Cornea Donor Study, ECD cao hơn **100 ± 25 tế bào/mm²** — minh họa **khác biệt hệ thống do phương pháp/hiệu chuẩn**.

9. Mamikonyan VR, Osipyan GA, Doguzov VA, Rozinova VN, Shchukina TI, Khraystin K. **Objective assessment of donor material for penetrating corneal transplantation.** *Vestn Oftalmol.* 2017;133(6):76–82. DOI: 10.17116/oftalma2017133676-82.
   - **100 mắt hiến**; so sánh siêu soi, confocal và keratoanalyzer.
   - **Siêu soi cho ECD cao nhất, confocal thấp nhất**; khuyến nghị lấy **trung bình 3 lần đo**.

10. Panton RW, Viana MG, Panton PJ, Panton JH. **Long-term follow-up of Leiske closed-loop anterior chamber intraocular lenses.** *J Cataract Refract Surg.* 2000;26(4):590–596. DOI: 10.1016/s0886-3350(99)00398-3.
    - **83 mắt** đặt IOL tiền phòng; theo dõi bằng siêu soi và pachymetry.
    - Mất bù giác mạc **1,5%** khi ECD **> 1.000** so với **57,1%** khi ECD **≤ 500** (p < 0,01).

## Giá ECD của rebubble (nối bài 3311)

11. Gundlach E, Pilger D, Dietrich-Ntoukas T, Joussen AM, Torun N, Maier AB. **Impact of re-bubbling after Descemet membrane endothelial keratoplasty on long-term results.** *Curr Eye Res.* 2021;46(6):784–788. DOI: 10.1080/02713683.2020.1842459.
    - **463 mắt** DMEK; so với không rebubble, ECD tháng 1 thấp hơn **157 tế bào/mm²** (95% CI 2–310; p = 0,047) sau **1 lần** và **504 tế bào/mm²** (95% CI 267–741; p < 0,001) sau **> 1 lần**.

## Ghi chú giấy phép
- Ảnh dùng trong bài: PMC12669210 (**CC BY 4.0**) và PMC8870504 (**CC BY 4.0**). Chi tiết từng file ở `images/CREDITS.md`.
- Không dùng ảnh từ nguồn không rõ giấy phép; không tải ảnh từ trang cấm tải.
