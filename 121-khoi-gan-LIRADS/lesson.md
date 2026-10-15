---
unit_id: "121"
subspecialty: Abdominal
anatomical_location: "gan (liver)"
primary_pattern: "khối gan (liver mass)"
tags: [pattern:khoi-gan, vung:gan, score:LI-RADS, protocol:CT-MRI-gan]
certainty: tong-hop-y-van
---

# 121 — Khối gan & LI-RADS v2018 / Liver masses & LI-RADS

**Tags:** `pattern:khoi-gan` `vung:gan` `score:LI-RADS` `protocol:CT-MRI-gan`
**Mức chắc chắn (certainty):** tổng hợp y văn (literature synthesis) — nhóm tự biên từ y văn mở, chưa gắn ca nguyên văn đơn lẻ.

## 1. Tổng quan — huyết động gan quyết định mọi dấu hiệu (Cửa 2)

- Gan lành nhận **75% máu từ tĩnh mạch cửa** (ngấm cực đại 60–70 giây) + **25% từ động mạch gan**; còn ung thư biểu mô tế bào gan (HCC) nhận gần như **100% máu từ hệ động mạch tân sinh**.
- TẠI SAO HCC sáng thì ĐM rồi tối dần: thì động mạch muộn (**35–40 giây**) HCC ngấm mạnh (**Non-rim APHE**) trong khi nhu mô chưa kịp ngấm; thì cửa (**60–70s**) và muộn (**3–5 phút**) nhu mô sáng lên còn HCC không có nhánh cửa nên **tối đi (Non-peripheral washout)**.
- **Điều kiện áp dụng LI-RADS v2018 (bẫy chết người):** CHỈ cho **xơ gan, viêm gan B mạn, hoặc tiền sử HCC**. **TUYỆT ĐỐI KHÔNG** cho < 18 tuổi, xơ gan do bệnh mạch máu (Budd-Chiari, suy tim phải, HHT — nốt tăng sản lành bắt thuốc giống hệt HCC!).

## 2. Gamut khối gan theo nền + động học

- **Nền xơ + APHE + washout:** HCC (LR-5 khi đủ chuẩn dưới).
- **Ngấm viền (rim APHE) + thải ngoại vi + co kéo bao:** ung thư đường mật (CCC)/di căn = **LR-M** (không phải HCC).
- **Nền lành + ngấm nốt ngoại vi hướng tâm:** hemangioma; **sẹo T2 sáng ngấm muộn + giữ Primovist:** tăng sản nốt khu trú (FNH); u tuyến (adenoma): chảy máu + mỡ vi thể.
- **Giả u tưới máu (THAD/THID):** hình chêm ngoại vi + mạch xuyên bình thường + **biến mất hoàn toàn thì cửa/muộn**.

![HCC 4 thì: ĐM ngấm → cửa/muộn thải](images/121_HCC-3-thi_CT_Wikimedia-Pan-CCBY40.jpg)
*Không tiêm (A) + ĐM (B) + cửa (C) + muộn (D). Nguồn: Pan et al., BMC Cancer 2014, CC BY 4.0.*

## 3. Bảng chốt LR-5 vs LR-M

| Thực thể (entity) | Hình ảnh | Chốt vào (rule-in) | Chốt loại (rule-out) | Gợi ý xác nhận |
|---|---|---|---|---|
| HCC LR-5 | **Non-rim APHE** + washout/vỏ/tăng trưởng | **10–19 mm: APHE + (washout HOẶC tăng ≥ 50%/6 tháng)**; **≥ 20 mm: APHE + ≥ 1/3 dấu** | 10–19 mm chỉ vỏ đơn độc → **LR-4**; rim APHE → LR-M | Đủ chuẩn = HCC 100%, không sinh thiết |
| LR-M (CCC/di căn) | **Rim APHE + peripheral washout** + ngấm muộn trung tâm + co kéo bao | **Rim + co kéo bao gan** | Non-rim APHE → HCC | Sinh thiết (không áp LR-5) |
| Hemangioma | **Ngấm nốt ngoại vi hướng tâm**, T2 sáng rực | **Hướng tâm + T2 sáng** | Washout → không phải hemangioma | MRI Primovist |
| FNH | **Sẹo trung tâm T2 sáng + ngấm muộn**, giữ Primovist | **Giữ thuốc thì gan-mật** | Thải thuốc → HCC/adenoma | MRI Gadoxetate |
| Adenoma | Chảy máu + mỡ vi thể, nữ + thuốc tránh thai | **Chảy máu + mỡ + nữ trẻ** | Washout + vỏ ở gan xơ → HCC | Ngừng thuốc + theo dõi (vỡ!) |

## 4. Protocol CT/MRI gan + flowchart

- CT 4 thì (trước + ĐM muộn 35–40s + cửa 60–70s + muộn 3–5p); MRI + Primovist (thì gan-mật 20p) cho FNH/HCC nhỏ.
- Đo trục dài + % tăng trưởng/6 tháng (threshold growth ≥ 50%).

```mermaid
flowchart TD
  A[Nốt gan + nguy cơ HCC?] --> B{Đủ điều kiện LI-RADS?}
  B -->|Không: <18t/mạch máu| C[Dừng LI-RADS, chẩn đoán khác]
  B -->|Có| D{Non-rim APHE?}
  D -->|Không| E{Rim APHE? LR-M}
  D -->|Có| F{Kích thước?}
  F -->|"10-19mm"| G[Washout/growth = LR-5; chỉ vỏ = LR-4]
  F -->|"≥20mm"| H[1 dấu = LR-5]
```

## 5. Cạm bẫy

- **THAD/THID sau sinh thiết/viêm** giả HCC thì ĐM — biến mất thì cửa/muộn là chốt.
- **Nốt tăng sản Budd-Chiari/suy tim** bắt thuốc giống HCC — cấm áp LI-RADS.
- **LR-4 ≠ LR-5:** 10–19 mm chỉ vỏ đơn độc = LR-4 (theo dõi/sinh thiết), đừng mổ như LR-5.

## 6. Tự lượng giá — Blind Quiz

**Ca 1 — Gan xơ + nốt 25 mm. Đọc 4 thì trước.**

![Ca 1 — CT 4 thì](images/121_HCC-3-thi_CT_Wikimedia-Pan-CCBY40.jpg)

- Hỏi: thì nào ngấm? Có washout không? Đủ LR-5 không? Vì sao?

<details><summary><b>Bấm để hiện đáp án</b></summary>

- **Non-rim APHE (B) + washout (C–D)** + ≥ 20 mm → **LR-5 = HCC chắc chắn**, không cần sinh thiết (đủ điều kiện: gan xơ).
- Nguồn: Pan et al., CC BY 4.0.
</details>

**Ca 2 — Nốt 15 mm + APHE + chỉ vỏ đơn độc, không washout/growth:** LR mấy? Xử trí? *(Bảng mục 3.)*

<details><summary><b>Bấm để hiện đáp án</b></summary>

- **LR-4** (chưa LR-5) — theo dõi sát/sinh thiết, không mổ như HCC chắc chắn.
</details>

## Bài liên quan chéo
- [100 – Tổng quan hệ Bụng](../100-tong-quan-he-bung/lesson.md)
- [110 – Giải phẫu bụng](../110-giai-phau-bung/lesson.md) (Couinaud, 4 thì)
- [122 – U lành gan (đã có)](../122-u-lanh-gan/lesson.md) (FNH/hemangioma chi tiết)

> Không dùng để chẩn đoán độc lập khi chưa có người hướng dẫn.
