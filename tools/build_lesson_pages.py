#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_lesson_pages.py — sinh trang HTML tĩnh cho từng bài + sitemap + llms.txt.

Mục tiêu: mỗi bài có URL riêng `/{slug}/`, HTML thật (không JS), canonical/meta/
JSON-LD đầy đủ để Google/Bing và các công cụ AI đọc được (SEO + GEO).

Nguồn: `lesson.md` (frontmatter + markdown) → render bằng marked (vendored, MIT)
qua `tools/render_markdown.js`, rồi bọc trong template SEO.

Dùng:
    python3 tools/build_lesson_pages.py --all
    python3 tools/build_lesson_pages.py --only 020
    python3 tools/build_lesson_pages.py --all --sitemap
    python3 tools/build_lesson_pages.py --all --check   # chỉ kiểm, không ghi

Ghi:
    {slug}/index.html
    sitemap.xml          (khi --sitemap hoặc --all)
    llms.txt             (khi --sitemap hoặc --all)
"""
import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://rad.matcauvong.com"
SITE_NAME = "Thư viện Chẩn đoán hình ảnh"
SITE_DESC = ("Học liệu chẩn đoán hình ảnh tiếng Việt: bản chất bệnh học, cơ chế tạo hình ảnh, "
             "chẩn đoán phân biệt, protocol và tự lượng giá; có trích dẫn nguồn mở.")
LESSON_RE = re.compile(r"^(\d{3,4})-(.+)$")

sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    import build_index as bi  # dùng spec_for + TABS để phân chuyên mục
except Exception:
    bi = None
try:
    import cdn  # đổi ảnh sang Cloudflare R2 khi manifest có
except Exception:
    cdn = None


# ── tiện ích ────────────────────────────────────────────────────────────────
def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_if_changed(path, content):
    try:
        if read(path) == content:
            return False
    except FileNotFoundError:
        pass
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return True


def split_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
        else:
            fm[k] = v
    return fm, text[m.end():]


def plain(text, limit=160):
    t = text or ""
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[*_`>#|]+", " ", t)
    t = re.sub(r"&[a-z]+;", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= limit:
        return t
    cut = t[:limit]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 40 else cut).rstrip(" ,;:.") + "…"


def _plain_cmp(t):
    """Dạng phẳng (không markdown) để so ngưỡng/câu chữ."""
    t = re.sub(r"[*_`]+", " ", t or "")
    return re.sub(r"\s+", " ", t).strip()


# dòng rác KHÔNG bao giờ dùng làm mô tả (disclaimer, khung quiz, ghi chú biên soạn)
BOILERPLATE = (
    "không dùng để chẩn đoán độc lập",
    "ảnh trơn ở ngoài",
    "bấm để hiện đáp án",
    "đã viết có link",
    "id ổn định, không đánh lại số",
    "chưa viết là text dự kiến",
)
# nhãn mở đầu được ưu tiên: câu chốt/định nghĩa là mô tả tốt nhất cho bài
DESC_LEAD = ("Câu chốt", "Điểm chốt", "Điểm tựa", "Định nghĩa", "Cơ chế")

# Bài có `primary_pattern` là CỤM mẫu hình (không phải câu) từng lấy nguyên cụm đó làm
# meta/llms. Bảng dưới đây thay bằng MỘT CÂU TIẾNG VIỆT rút từ chính nội dung bài
# (không thêm dữ kiện ngoài bài), ≤ 158 ký tự như giới hạn meta; llms.txt dùng nguyên câu
# (không cắt 120) để không bị "…".
# Chỉ áp cho đúng các slug này — mọi bài khác giữ nguyên hành vi cũ.
PATTERN_DESC = {
    "058-nhiem-nam-khi-phe-quan-ghep-phoi":
        "ITBA sau ghép phổi là bệnh của niêm mạc đường thở: dày thành, giả mạc/nút nhầy, hẹp lòng lan tỏa, chốt bằng nội soi.",
    "1430-icans-doc-tinh-than-kinh-sau-car-t":
        "ICANS là bệnh não lan tỏa sau CAR-T: MRI thường bình thường, khi bất thường thấy FLAIR chất trắng lan tỏa ± hạn chế khuếch tán vỏ não.",
    "1438-viem-mang-bo-dao-giao-cam":
        "Viêm màng bồ đào giao cảm là viêm toàn màng bồ đào u hạt hai bên, khởi phát sau chấn thương xuyên thấu hoặc mổ nội nhãn một mắt.",
    "1635-ro-oi-non-thang-sau-can-thiep-bao-thai":
        "Rò ối non tháng sau can thiệp bào thai do lỗ trocar không được màng ối bịt kín, tạo ống rò thành tử cung gây thiểu ối tiến triển.",
    "1636-theo-doi-than-kinh-sau-mot-thai-chet":
        "Khi một thai trong song thai một bánh nhau chết, thai còn lại bị giảm tưới máu não cấp rồi thêm tổn thương chất trắng non tháng.",
    "1644-dai-thao-nhat-trung-uong-o-tre":
        "Đái tháo nhạt trung ương ở trẻ chẩn đoán bằng lâm sàng – sinh hóa trước, hình ảnh sau; MRI tìm mất điểm sáng sau yên hoặc cuống yên dày.",
    "1709-acth-lac-cho-an":
        "Cushing phụ thuộc ACTH do nguồn lạc chỗ ẩn: u vài milimét, hình ảnh hay âm tính, phải tìm theo bậc và chứng minh nguồn trung ương bằng BIPSS.",
    "1748-cushing-tai-phat-sau-mo-xuyen-buom":
        "Cushing tái phát sau mổ xuyên bướm chẩn đoán bằng đường cong cortisol ngày 1–3; MRI sau mổ chỉ đáng tin từ 3 tháng.",
    "1822-dcmrl-bach-huyet":
        "DCMRL là chụp mạch bạch huyết theo thời gian sau tiêm gadolinium pha loãng vào hạch bẹn, trả lời ống ngực có hiện hình và rò ở đâu.",
    "1899-buou-giap-lac-cho-lingual-thyroid":
        "Bướu giáp lạc chỗ có thể là toàn bộ tuyến giáp của người bệnh (hơn 70% không có mô giáp ở cổ); cắt khi chưa xạ hình gây suy giáp vĩnh viễn.",
    "1965-huyet-khoi-xoang-tm-nao-so-sinh":
        "Huyết khối xoang ở sơ sinh biểu hiện bằng co giật, bú kém, li bì; dấu hình ảnh mạnh nhất là tổn thương đồi thị hai bên.",
    "1967-acnes-dau-thanh-bung-sau-mo":
        "ACNES là đau thành bụng do nhánh trước T10–T12 bị chèn ở bờ ngoài cơ thẳng, chẩn đoán bằng lâm sàng với hình ảnh bình thường.",
    "3023-u-tai-mach-dap":
        "Ù tai mạch đập là cảm nhận âm thanh đồng bộ nhịp tim không có nguồn âm ngoài, phải phân biệt hướng động mạch hay tĩnh mạch.",
    "3051-mau-tu-to-chuc-hoa-xoang-buom":
        "Máu tụ tổ chức hóa xoang bướm là tổn thương lành tính giả u: khối mô mềm mòn xương, chảy máu cam tái phát; loại túi phình mạch cảnh trong trước.",
    "3070-tiem-chat-lam-day-day-thanh-va-thyroplasty-o-tre":
        "Hở thanh môn do liệt dây thanh một bên gây hít sặc và khàn; tiêm dây thanh là can thiệp tạm thời, hiệu quả chắc nhất trên nuốt.",
    "3073-hoi-chung-lumbar-u-mau-duong-giua-di-tat-tuy":
        "U máu đoạn tính đường giữa vùng thắt lưng–cùng cụt là dấu hiệu da của dị tật tủy; chỉ tổn thương vượt đường giữa mới mang nguy cơ.",
    "3087-hep-dong-mach-than-ghep":
        "Hẹp động mạch thận ghép chẩn đoán bằng PSV tại chỗ hẹp và phổ tardus-parvus hạ nguồn, không dựa vào chỉ số sức cản RI.",
    "3141-krukenberg-thai-ky":
        "Krukenberg trong thai kỳ là di căn buồng trứng hiếm nhưng gần như luôn muộn: 65,7% hai bên, khối đặc, cổ trướng, sống trung vị 6 tháng.",
    "3142-ung-thu-da-day-ct-linitis-plastica":
        "Dày thành dạ dày chỉ đáng giá khi dạ dày đã căng đủ; linitis plastica thường không có khối, chỉ thành dày cứng, mất nếp niêm, hẹp lòng.",
    "6110-nhiem-trung-quanh-khop-nhan-tao-sau-tha":
        "Nhiễm trùng quanh khớp nhân tạo không loại trừ bằng X-quang bình thường và không chẩn đoán bằng một xét nghiệm; quyết định là giữ hay thay implant.",
    "6111-huyet-khoi-tinh-mach-than-so-sinh":
        "Huyết khối tĩnh mạch thận sơ sinh có chữ ký siêu âm: thận to, mất dòng tĩnh mạch, chỉ số sức cản tăng; thận thường không hồi phục.",
    "6131-kinh-scleral-benh-be-mat-nhan-cau":
        "Kính scleral tạo bể dịch che chở bề mặt nhãn cầu mà không đè vùng rìa; độ vừa đo bằng vault 200–350 µm trên AS-OCT.",
    "6134-benh-xuong-cung-di-truyen-osteopetrosis":
        "Osteopetrosis là xương đặc nhưng giòn, không có tủy và bít các lỗ thần kinh; phim chốt mất phân biệt vỏ–tủy, bone-in-bone.",
    "753-loan-san-xo-xuong-ham":
        "Loạn sản xơ xương hàm không phân biệt được với u xơ xương hóa và loạn sản xê-măng bằng mô bệnh học, nên chẩn đoán là một quyết định hình ảnh.",
    "944-nhiem-stent-graft-dong-mach-chu-chau":
        "Nhiễm mảnh ghép động mạch chủ tử vong 10–45%, chẩn đoán bằng bộ tiêu chuẩn MAGIC 2016 kết hợp lâm sàng – hình ảnh – vi sinh.",
    "947-viem-phoi-rsv-va-cum-o-nguoi-ghep-tang":
        "Ở người ghép tạng, RSV và cúm cho tổn thương hướng đường thở (tree-in-bud, dày thành phế quản, nút nhầy), không phải kính mờ đối xứng.",
}


# ── Đợt 1/3 (task rad-desc-std-002): 180 bài `primary_pattern` đầu tiên,
# cùng quy tắc — 1 câu tiếng Việt ≤ 158 ký tự rút từ chính nội dung bài.
# Đợt 2–3 (360 bài còn lại): xem handoff/primary-pattern-remaining.txt.
PATTERN_DESC.update({
    "043-cham-soc-ho-hap-quanh-mo-tis-eos":
        "Trẻ TIS/EOS sau mở rộng lồng ngực dễ hạn chế thông khí và biến chứng hô hấp sau mổ, nên cai máy phải lên kế hoạch trước.",
    "044-cryobiopsy-trung-that-EBUS":
        "Cryobiopsy trung thất qua EBUS lấy được mảnh mô lớn nên độ nhạy với u lympho 95%, so với 15% của TBNA đơn thuần.",
    "054-abpa-viem-phe-quan-di-ung-aspergillus":
        "ABPA gây giãn phế quản trung tâm kèm nút nhầy 'ngón tay trong găng'; nút nhầy > 70 HU (HAM) là dấu chốt trên CT.",
    "056-benh-phoi-ntm-mac":
        "Bệnh phổi do NTM điển hình là giãn phế quản kèm nốt trung tâm tiểu thùy/tree-in-bud ở thể Lady Windermere, nặng hơn ở thể hang xơ.",
    "087-viem-phoi-hit-dau-hoa-hydrocarbon":
        "Viêm phổi do hít dầu hỏa ở trẻ nhỏ cho đông đặc hai đáy, phải nhiều hơn trái, xuất hiện vài giờ sau hít dù lượng hít rất nhỏ.",
    "088-apxe-phoi-mu-mang-phoi-sau-vap":
        "Áp-xe phổi sau VAP là hang có mức khí–dịch; mủ màng phổi là tụ dịch khu trú — cả hai đều phải quyết định dẫn lưu đúng ngưỡng.",
    "090-bong-hit-duong-tho-o-tre":
        "Bỏng hít đường thở ở trẻ gây phù nề, bồ hóng và dày thành phế quản, nhưng X-quang sớm thường bình thường nên dễ bỏ sót.",
    "103-ap-xe-gan-klebsiella":
        "Áp-xe gan do Klebsiella pneumoniae là ổ giảm đậm độ có vách hoặc khí, ngấm viền, hay gặp ở người đái tháo đường.",
    "113-hep-mien-noi-mat-ruot":
        "Hẹp miệng nối mật–ruột sau cắt nang ống mật chủ biểu hiện bằng sốt kèm hẹp miệng nối và giãn đường mật trong gan.",
    "117-tuong-tac-thuoc-va-theo-doi-tacrolimus":
        "Nồng độ đáy tacrolimus lệch mục tiêu vì tương tác CYP3A4/P-gp hoặc vì hematocrit, thời điểm lấy máu; phải đọc bằng C0/D.",
    "118-doac-ghep-tang-uc-che-calcineurin":
        "Ở người ghép tạng dùng ức chế calcineurin, DOAC tương tác qua CYP3A4/P-gp nên chọn thuốc và theo dõi khác hẳn kháng vitamin K.",
    "143-u-trung-bieu-mo-phuc-mac-vs-carcinomatosis":
        "U trung biểu mô phúc mạc ác và carcinomatosis đều gây dày phúc mạc dạng mảng/nốt kèm dịch khu trú, nhưng khác hẳn về điều trị.",
    "161-viem-ruot-thua-cap":
        "Viêm ruột thừa cấp là quai ruột giãn, thành dày kèm thâm nhiễm mỡ khu trú; đường kính ≥ 6 mm là ngưỡng hay dùng trên siêu âm/CT.",
    "166-tang-ap-luc-cua-xo-gan-bam-sinh-caroli":
        "Xơ hóa gan bẩm sinh và bệnh Caroli gây tăng áp cửa với xơ hóa quanh ống mật và giãn đường mật, thường khởi đầu bằng xuất huyết tiêu hóa.",
    "180-viem-tui-mat-thieu-mau-sau-tace":
        "Viêm túi mật thiếu máu sau TACE có thành dày ≥ 4 mm, thâm nhiễm mỡ quanh túi mật và lipiodol trong thành trên CBCT.",
    "186-hoi-chung-gan-phoi-hps-va-poph":
        "Hội chứng gan–phổi gây giảm oxy do giãn mạch trong phổi, còn tăng áp phổi do tăng áp cửa (PoPH) là mặt đối lập của cùng một bệnh gan.",
    "187-can-thiep-gian-tinh-mach-lac-cho":
        "Giãn tĩnh mạch lạc chỗ nằm ngoài vùng dạ dày–thực quản, nên chọn TIPS, BATO/ATO hay PTO là quyết định chính của can thiệp.",
    "188-benh-tuy-do-gan-sau-shunt-cua-chu":
        "Bệnh tủy do gan sau shunt cửa–chủ gây liệt cứng hai chi dưới tiến triển do hủy myelin đối xứng bó tháp bên ở tủy ngực–thắt lưng.",
    "192-splenosis-va-lach-phu-sau-cat-lach":
        "Splenosis và lách phụ phì đại sau cắt lách tạo nốt tăng tưới máu giống nhu mô lách, là 'giả di căn' nguy hiểm nhất của ổ bụng.",
    "196-hps-ton-tai-sau-ghep-gan":
        "HPS tồn tại sau ghép gan gây giảm oxy máu dai dẳng vì shunt phải–trái nội phổi còn lại, cần hàng tháng mới hết khó thở.",
    "203-neuro-behcet-va-mach-mau-lon":
        "Neuro-Behçet cho tổn thương nhu mô não không theo lãnh thổ mạch ở đồi thị–thân não, kèm phình/giả phình mạch và dễ bị mổ nhầm thành u.",
    "204-hoai-tu-phong-xa-sau-xa-tri-u-nao":
        "Hoại tử phóng xạ sau xạ trị não là ngấm thuốc dạng vòng tiến triển trong 6–24 tháng, phải phân biệt với tái phát u trên chuỗi ảnh.",
    "209-benh-chat-trang-do-doc-chat":
        "Bệnh chất trắng do độc chất cho tổn thương đối xứng, không ngấm thuốc, hạn chế khuếch tán và chừa vỏ não — khác nhồi máu.",
    "216-di-dang-mach-CVST":
        "Dị dạng mạch não và huyết khối xoang tĩnh mạch cùng gây đau đầu, co giật; CT không cản quang rồi CTV là cặp chụp đầu tay.",
    "227-dau-dau-set-danh-thunderclap":
        "Đau đầu sét đánh đạt đỉnh dưới 1 phút; CT không cản quang nhạy 95% trong 24 giờ đầu và giảm dần, nên âm tính chưa loại trừ SAH.",
    "231-ton-thuong-mach-mau-nao-chan-thuong-va-vo-so-tien-trien":
        "Ở trẻ chấn thương nặng, tổn thương mạch máu não do chấn thương và vỡ sọ tiến triển dễ bỏ sót vì triệu chứng xuất hiện muộn.",
    "232-chan-thuong-dau-nhe-concussion-o-tre":
        "Chấn thương đầu nhẹ ở trẻ (GCS 13–15) không có tổn thương cấu trúc trên ảnh; chấn động não là hội chứng rối loạn chức năng thoáng qua.",
    "236-viem-tai-xuong-chum-bien-chung-noi-so":
        "Viêm tai xương chũm cho mờ xương chũm và mòn vách xương; áp-xe não đi kèm chốt bằng DWI sáng, ADC tối.",
    "237-bien-chung-than-kinh-so-viem-tai-gradenigo":
        "Biến chứng thần kinh sọ của viêm tai gồm viêm đỉnh xương đá gây đau sau mắt, liệt dây VII và viêm mê nhĩ, chỉ gặp dưới 1% ca.",
    "238-lemierre-huyet-khoi-tm-canh-trong":
        "Hội chứng Lemierre là huyết khối tĩnh mạch cảnh trong nhiễm khuẩn sau viêm họng ở người trẻ, thường kèm thuyên tắc phổi nhiễm khuẩn.",
    "243-san-mang-than-kinh":
        "Sán máng thần kinh gây tổn thương nội tủy tăng T2 với ngấm thuốc dạng cuống lá do u hạt quanh trứng, hay gặp ở tủy ngực dưới–nón tủy.",
    "246-hoi-chung-sheehan-hoai-tu-tuyen-yen-sau-sinh":
        "Hội chứng Sheehan là hoại tử tuyến yên sau băng huyết sau sinh, dẫn tới hố yên trống và suy nhiều hormone tuyến yên.",
    "250-lao-noi-tuy-va-lao-mang-tuy":
        "Lao nội tủy là khối ngấm thuốc dạng vòng hoặc dấu bia, trung tâm bã đậu có khi tối trên T2 chứ không sáng như viêm thông thường.",
    "251-chan-thuong-dau-tre-shunt-va-roi-loan-dong-mau":
        "Trẻ có shunt não thất hoặc rối loạn đông máu bị chấn thương đầu nằm ngoài vùng bằng chứng của quy tắc chụp CT, nên ngưỡng chụp phải thấp.",
    "252-bien-chung-muon-cua-shunt-nao-that":
        "Biến chứng muộn của shunt não thất là gãy–ly giãn catheter, nhiễm trùng, pseudocyst ổ bụng và di trú; não thất to hơn phim nền mới là chốt.",
    "255-mang-nhen-lung-dorsal-scalpel-sign":
        "Màng nhện lưng tạo dấu scalpel: tủy ngực bị đẩy ra trước, lõm mặt lưng, khoang dịch não tủy phía sau giãn, thấy rõ trên 3D-CISS.",
    "256-nhoi-mau-tuy-sau-phau-thuat-dong-mach-chu":
        "Nhồi máu tủy sau mổ động mạch chủ cho T2 tăng hình bút chì ở 2/3 trước tủy, hạn chế khuếch tán và dấu 'mắt cú' trên lát trục.",
    "257-theo-doi-tai-phat-sau-can-thiep-tui-phinh":
        "Theo dõi sau can thiệp túi phình phải so với mốc ngay sau can thiệp: coil compaction, tái phát, hẹp trong stent và artifact MRA giả tái phát.",
    "258-apxe-ngoai-mang-cung-loet-ti-de-cung-cut":
        "Áp-xe ngoài màng cứng vùng cùng cụt từ loét tì đè gây đau rễ, yếu chi, bí tiểu mà chưa có mức tổn thương tủy rõ ở giai đoạn đầu.",
    "259-hoi-chung-smart-benh-nao-do-xa-muon":
        "Hội chứng SMART gây cơn giống đột quỵ với ngấm vỏ–màng mềm dạng cuộn một bên trong trường chiếu cũ, hồi phục trên phim chụp lại.",
    "260-hep-dong-mach-canh-do-xa":
        "Bệnh mạch cảnh do xạ là hẹp–tắc dài, nhẵn, nhiều ổ, ít vôi hóa, nằm đúng trường chiếu cũ và xuất hiện nhiều năm sau xạ.",
    "261-benh-nao-chat-trang-do-xa-tri":
        "Bệnh não chất trắng do xạ cho FLAIR sáng đối xứng quanh não thất, không ngấm, không choán chỗ, kèm teo não và chừa sợi U dưới vỏ.",
    "262-benh-mach-mau-lon-do-xa-tri-moyamoya":
        "Bệnh mạch máu lớn do xạ gây hẹp–tắc dài, nhẵn, không vôi hóa ở ICA tận–M1–A1, có thể kèm mạng bàng hệ kiểu moyamoya.",
    "263-hep-dong-mach-canh-ngoai-so-do-xa":
        "Hội chứng vỡ mạch cảnh sau xạ cổ gây chảy máu mũi–miệng tái phát (sentinel bleed), giả phình và hoại tử mô quanh mạch.",
    "264-u-mang-nao-do-xa":
        "U màng não do xạ là khối ngoài trục dựa màng não, ngấm thuốc đồng nhất, nằm trong trường chiếu cũ và xuất hiện sau nhiều năm.",
    "265-ngo-doc-khi-cuoi-tuy":
        "Ngộ độc khí cười gây thiếu B12 chức năng: T2 tăng đối xứng hai bên cột sau tủy cổ, hình chữ V ngược, không ngấm, không hạn chế khuếch tán.",
    "266-theo-doi-sau-web-tui-phinh":
        "Theo dõi sau đặt WEB dựa vào thang BOSS, co rút lưới và ngấm thuốc còn lại trong hoặc quanh lưới nitinol của túi phình.",
    "267-presyrinx-va-tuy-mem-hoi-phuc":
        "Presyrinx là phù tủy lan dọc còn hồi phục được, không có khoang, không ngấm thuốc, xuất hiện khi dòng dịch não tủy bị tắc.",
    "268-benh-tuy-do-xa-tri":
        "Bệnh tủy do xạ cho T2 sáng ở trung tâm tủy lan dọc ≥ 1 đốt, không choán chỗ, khu trú đúng trường chiếu, teo tủy về muộn.",
    "269-xa-lai-tuy-song":
        "Quyết định xạ lại tủy sống nằm ở tổng liều EQD2 cộng dồn trên DVH với α/β = 2 Gy, không ở một lần chụp đơn lẻ.",
    "270-carotid-web":
        "Carotid web là dải xơ nội mạc ở mặt sau hành cảnh trong, gây ổ ứ cản quang và đột quỵ ở người trẻ không có yếu tố xơ vữa.",
    "271-hoi-chung-tang-tuoi-mau-nao":
        "Hội chứng tăng tưới máu não sau can thiệp cảnh gây phù vận mạch hoặc xuất huyết cùng bên do mạch mất khả năng co lại.",
    "272-sarcoma-xuong-so-do-xa":
        "Sarcoma xương nền sọ do xạ là khối phá xương kèm mô mềm trong trường chiếu cũ, thường xuất hiện sau hơn 5 năm.",
    "274-thieu-mau-mat-ois":
        "Thiếu máu mắt và glôcôm tân mạch sau hẹp cảnh cho xuất huyết điểm giữa ngoại vi và tân mạch mống mắt ở phía sau chỗ hẹp.",
    "275-dong-kinh-sau-tai-thong-canh":
        "Động kinh sau bóc nội mạc hoặc đặt stent cảnh là cơn cục bộ do tăng tưới máu làm vỡ hàng rào máu–não, có thể tiến tới xuất huyết ổ.",
    "276-tac-dong-mach-trung-tam-vong-mac":
        "Tắc động mạch trung tâm võng mạc cấp cho võng mạc trắng đục lan tỏa với điểm đỏ anh đào; cửa sổ điều trị chỉ vài giờ.",
    "278-tac-dong-mach-mat":
        "Tắc động mạch mắt làm mất cả võng mạc lẫn hắc mạc nên trắng đục lan tỏa mà KHÔNG có điểm đỏ anh đào, kèm tam giác Amalric.",
    "279-pamm-nhoi-mau-lop-giua":
        "PAMM là nhồi máu lớp nhân trong hoàng điểm: OCT có dải tăng phản xạ, đáy mắt không trắng đục, bệnh nhân có ám điểm cạnh trung tâm.",
    "280-benh-tuy-thieu-dong":
        "Bệnh tủy do thiếu đồng bắt chước thiếu B12 và N2O: T2/STIR tăng đối xứng cột sau tủy, hình chữ V ngược.",
    "281-thoai-hoa-tuy-ket-hop-b12":
        "Thoái hóa tủy kết hợp bán cấp do thiếu vitamin B12 cho tăng tín hiệu T2 đối xứng, dọc dài ở cột sau tủy.",
    "304-dau-dai-dang-sau-cat-xuong-cut":
        "Đau dai dẳng sau cắt xương cụt có bốn nguồn: cụt còn sót, sẹo thần kinh, nhiễm trùng và đau thần kinh thẹn — đọc phim hậu phẫu theo từng nguồn.",
    "382-ischiofemoral-impingement":
        "Ischiofemoral impingement là hẹp khoảng giữa mấu chuyển nhỏ và ụ ngồi gây phù cơ quadratus femoris, chẩn đoán bằng MRI lát trục.",
    "383-benh-gan-goc-co-gan-kheo-gan":
        "Bệnh gân gốc cơ gân kheo gần là thoái hóa gân do tải lặp lại, biểu hiện dày gân và phù quanh gân tại ụ ngồi, không phải viêm.",
    "384-sarcoma-do-xa-sau-xa-tri-nguc":
        "Sarcoma do xạ sau xạ trị ngực là khối phá xương hoặc mô mềm mới trong trường chiếu, xuất hiện khoảng 10 năm sau xạ.",
    "405-pachychoroid-quanh-dia-thi-pps":
        "PPS gây 'phù đĩa thị giả' với hắc mạc quanh đĩa dày và túi dịch trong võng mạc xuất phát từ bờ đĩa, ngưỡng hắc mạc 300 µm.",
    "413-PFV-PHPV-day-xo-the-thuy-tinh":
        "Tồn tại tuần hoàn bào thai (PFV) cho dây xơ dịch kính từ đĩa thị kèm nhãn cầu nhỏ, tăng hồi âm trên B-scan nhưng không có bóng lưng.",
    "414-glaucoma-va-nhan-cau-nho-o-pfv":
        "PFV thể trước gây nhãn cầu nhỏ kèm tăng nhãn áp và màng xơ đồng tử: mắt bé vẫn có thể glôcôm vì củng mạc còn đàn hồi.",
    "415-phe-nhan-cau-nho-coloboma":
        "Phổ nhãn cầu nhỏ–coloboma đọc trên MRI hốc mắt: mất viền hắc mạc ở đáy coloboma là dấu chốt, vì đáy là mô xơ.",
    "416-di-tat-tien-phong-o-tre":
        "Dị tật tiền phòng ở trẻ gây đục giác mạc bẩm sinh trung tâm ± dính mống mắt–giác mạc, gồm Peters, Axenfeld–Rieger và sclerocornea.",
    "417-hoi-chung-morning-glory":
        "Hội chứng Morning Glory là hõm đĩa thị hình phễu có búi glia trung tâm; mất liên tục củng mạc là dấu chốt, kèm bất thường nền sọ đường giữa.",
    "418-nanophthalmos-tran-dich-hac-mac":
        "Nanophthalmos là nhãn cầu ngắn, củng mạc dày, tiền phòng nông nên dễ tràn dịch hắc mạc vì dịch thoát không được.",
    "419-thoat-vi-nao-nen-so":
        "Thoát vị não nền sọ là khuyết xương nền sọ kèm khối mô não/dịch não tủy thoát vị; dải dịch não tủy liên tục qua khuyết xương là dấu chốt.",
    "425-dusn-au-trung-di-dong-duoi-vong-mac":
        "DUSN gây viêm một bên với đốm xám trắng di chuyển và ấu trùng thấy được; OCT cho thấy mất dải ellipsoid và đường hầm dưới võng mạc.",
    "426-toxocariasis-theo-doi-bien-chung-muon":
        "Theo dõi toxocariasis nội nhãn phải tìm biến chứng muộn: dải co kéo, tân mạch hắc mạc và bong võng mạc co kéo.",
    "437-teo-thi-kem-diec":
        "Teo thị kèm điếc di truyền (DOA+/OPA1, WFS1 trội) chẩn đoán sớm bằng OCT: RNFL và GCL mỏng trước khi thị lực giảm rõ.",
    "438-theo-doi-dai-han-gca-bien-chung-mach-lon":
        "Theo dõi dài hạn GCA phải tầm soát biến chứng mạch lớn: aortitis, phình và tách thành động mạch chủ, thường không có triệu chứng.",
    "457-benh-gia-rop-tre-du-thang":
        "Bệnh 'giả ROP' ở trẻ đủ tháng (FEVR, Norrie, incontinentia pigmenti, Coats) gây tân mạch và bong võng mạc dù không sinh non.",
    "459-theo-doi-dai-han-cmv-retinitis":
        "Theo dõi dài hạn CMV retinitis sau ghép cần lịch sàng lọc UWF, theo dõi CD4 và viremia, và mốc ngừng kháng virus.",
    "462-u-lympho-noi-nhan-PVRL":
        "U lympho nội nhãn giả viêm màng bồ đào ở người lớn tuổi: thâm nhiễm dưới biểu mô sắc tố và viêm dịch kính, chốt bằng IL-10/IL-6 và MYD88.",
    "463-viem-noi-nhan-noi-sinh-nam":
        "Viêm nội nhãn nội sinh do nấm cho nốt trắng nổi vào dịch kính ('fluff ball', 'chuỗi ngọc trai') kèm ổ viêm hắc–võng mạc.",
    "465-coats-plus-syndrome-ctc1":
        "Coats plus (CTC1) gây bệnh võng mạc xuất tiết giống Coats hai bên kèm vôi hóa–nang não và chảy máu tiêu hóa.",
    "466-toxocariasis-noi-nhan":
        "Toxocariasis nội nhãn tạo u hạt võng mạc ngoại vi kèm dây co kéo dịch kính–võng mạc do phản ứng viêm quanh ấu trùng.",
    "467-norrie-di-truyen-tu-van-va-theo-doi":
        "Norrie gây bong võng mạc hai bên ở trẻ trai đủ tháng (liên kết X, gen NDP), kèm điếc và chậm phát triển nên cần tư vấn di truyền.",
    "469-lac-nhuoc-thi-tre-sinh-non-rop":
        "Trẻ sinh non/ROP bị lác và nhược thị do khúc xạ lệch, hoàng điểm lệch và tổn thương não; cần chỉnh kính và bịt mắt sớm.",
    "473-u-lympho-T-NK-va-u-lympho-thu-phat-o-mat":
        "U lympho T/NK hoặc u lympho thứ phát ở mắt gây masquerade với đục dịch kính ít viêm và dày hắc mạc/thể mi; IL-10 không đủ để loại.",
    "474-khang-nam-noi-nhan-chon-thuoc-theo-loai":
        "Viêm nội nhãn do nấm phải chọn kháng nấm theo loài và MIC, không dùng một phác đồ chung cho Candida và Aspergillus.",
    "475-viem-noi-nhan-noi-sinh-vi-khuan":
        "Viêm nội nhãn nội sinh do vi khuẩn gây ổ mủ dưới võng mạc tiến triển trong giờ–ngày, trong khi tiền phòng còn 'im lặng'.",
    "476-tam-soat-mat-candidemia-nhi":
        "Tầm soát đáy mắt ở trẻ candidemia tìm ổ chorioretinitis vàng–kem đơn độc không kèm viêm dịch kính, phần lớn không triệu chứng.",
    "477-benh-ty-the-thi-giac-tai":
        "Bệnh ty thể biểu hiện ở mắt và tai (MELAS, MIDD, POLG, PHARC) cho tổn thương vỏ não không theo lãnh thổ mạch và bệnh hoàng điểm dạng pattern.",
    "479-tu-van-di-truyen-vus-opa1-wfs1":
        "Biến thể VUS trong teo thị/điếc di truyền (OPA1/WFS1) là một trạng thái bằng chứng theo ACMG, không phải một chẩn đoán.",
    "480-naion-dieu-tri-va-theo-doi":
        "NAION là nhồi máu đầu thị trên đĩa thị chật; phù đĩa chỉ là hậu quả nên corticoid không giúp, và phải dự phòng mắt đối diện.",
    "482-tan-mach-hac-mac-sau-cscr-man":
        "Tân mạch hắc mạc sau CSCR mạn (pachychoroid neovasculopathy) nằm dưới biểu mô sắc tố, chốt bằng OCTA và phân biệt với drusen.",
    "484-nhiem-doc-vong-mac-hydroxychloroquine":
        "Nhiễm độc võng mạc do hydroxychloroquine mất lớp ellipsoid zone cạnh hoàng điểm nhưng còn nguyên hố trung tâm — dấu hiệu sàng lọc sớm.",
    "488-hcq-trong-thai-ky-va-cho-con-bu":
        "Hydroxychloroquine trong thai kỳ ít gây độc võng mạc vì tổn thương cần tích lũy nhiều năm, nhưng vẫn phải theo lịch sàng lọc mắt.",
    "489-loan-duong-hoa-van-vs-doc-tinh-thuoc":
        "Loạn dưỡng hoa văn ngoài di truyền (PRPH2) cho FAF đốm/vòng và dày hoặc mất ellipsoid zone, phải phân biệt với độc tính thuốc.",
    "490-vong-mac-dai-thao-duong-trong-thai-ky":
        "Bệnh võng mạc đái tháo đường tiến triển trong thai kỳ rồi thoái lui sau sinh, nên soi đáy mắt theo tam cá nguyệt và chọn laser/anti-VEGF trước sinh.",
    "491-pvrl-theo-doi-tai-phat":
        "Theo dõi PVRL phải tìm tái phát nội nhãn và tiến triển thần kinh trung ương, vì mắt và não chung hàng rào và chung đột biến MYD88 L265P.",
    "492-sinh-thiet-hac-vong-mac-dich-kinh":
        "Sinh thiết hắc–võng mạc và lấy mẫu dịch kính quyết định độ nhạy: ly tâm 500 × g trong 5 phút mới đủ tế bào để chẩn đoán.",
    "493-u-lympho-nguyen-phat-hac-mac":
        "U lympho nguyên phát hắc mạc gây dày hắc mạc lan tỏa kín đáo, hồi âm thấp trên B-scan, trễ chẩn đoán tới 2 năm, khác melanoma.",
    "494-doc-than-kinh-methotrexate":
        "Độc thần kinh methotrexate cho tổn thương chất trắng hạn chế khuếch tán (ADC thấp), đối xứng, không ngấm — khác tái phát u.",
    "495-viem-noi-nhan-nam-ngoai-sinh-vs-TASS":
        "Viêm nội nhãn do nấm ngoại sinh khởi phát muộn với ổ nấm trên IOL/bao thể thủy tinh; TASS thì giới hạn ở tiền phòng sau ca mổ trơn tru.",
    "496-u-lympho-T-NK-noi-nhan-dieu-tri-va-ghep":
        "ENKTL nội nhãn thiếu asparagine synthetase nên L-asparaginase là chốt điều trị; CHOP không cứu được, theo dõi bằng EBV DNA.",
    "497-theo-doi-sau-cay-oc-tai-tre":
        "Theo dõi sau cấy ốc tai: điện cực ngoài ốc tai hoặc di trú, xơ–vôi hóa ốc tai và thất bại thiết bị chiếm 69,2% ca phải cấy lại.",
    "499-hattersley-urano-wfs1-troi":
        "Hội chứng Hattersley–Urano (WFS1 trội) gây teo thị kèm điếc và đái tháo đường; phân lớp lớp rối ngoài trên OCT gặp ở 75% ca.",
    "511-aimss-dau-co-khop-do-uc-che-aromatase":
        "Đau cơ–khớp do ức chế aromatase gây đau khớp đối xứng và cứng buổi sáng ở 20–50% người dùng, kèm mất xương nhanh.",
    "534-roi-loan-phat-trien-gioi-gonadoblastoma":
        "Rối loạn phát triển giới 46,XY (Swyer) có tuyến sinh dục dạng dải nên dễ sinh u tế bào mầm/gonadoblastoma, hình ảnh là khối phần phụ đặc–hỗn hợp.",
    "535-ung-thu-buong-trung-phuc-mac-krukenberg":
        "Ung thư buồng trứng gieo rắc phúc mạc tạo khối phần phụ đặc hai bên kèm nốt phúc mạc, cổ trướng và u Krukenberg.",
    "536-u-mam-u-mo-dem-buong-trung":
        "Ở người trẻ, khối phần phụ đặc–hỗn hợp thường là u mầm hoặc u mô đệm–dây sinh dục, khác hẳn ung thư biểu mô ở tuổi quanh mãn kinh.",
    "544-dao-nguoc-tu-cung-khong-do-sinh":
        "Đảo ngược tử cung không do sinh hiếm, thường do u xơ có cuống kéo đáy tử cung lộn ra ngoài; 32% là ác tính nên phải lấy mô bệnh.",
    "554-polyp-noi-mac-va-u-xo-sa-qua-co-tu-cung":
        "Polyp nội mạc và u xơ có cuống sa qua cổ tử cung là khối 'sa' giả: tử cung vẫn đúng vị trí, chỉ khối u sa xuống.",
    "558-hoi-chung-co-hinh-le":
        "Hội chứng cơ hình lê gây chèn ép thần kinh tọa ngoài cột sống do cơ hình lê dày một bên, phải loại trừ nguyên nhân tại cột sống.",
    "585-nang-lac-noi-mac-va-du-tru-buong-trung":
        "Nang lạc nội mạc buồng trứng có T1 tăng tín hiệu kèm T2 shading; bóc nang hay đốt đều làm giảm dự trữ buồng trứng đo bằng AMH.",
    "596-ung-thu-vu-nam-va-nguoi-chuyen-gioi":
        "Ung thư vú ở nam và người chuyển giới thường là khối dưới quầng vú, phát hiện muộn vì không có chương trình tầm soát.",
    "604-dan-luu-mang-ngoai-tim-nhu-nhi":
        "Khoang màng ngoài tim ở nhũ nhi chứa dưới 5 mL dịch, nên một lượng dịch hoặc khí nhỏ tích tụ nhanh đã đủ gây chèn ép tim.",
    "607-tang-ap-phoi-so-sinh-pphn":
        "PPHN là thất bại giảm sức cản mạch phổi sau sinh, gây shunt phải–trái qua PDA/PFO và hạ oxy không tương xứng với bệnh nhu mô phổi.",
    "618-ro-phe-quan-mang-phoi-va-ro-khi-dai-dang-o-tre":
        "Rò phế quản–màng phổi sau cắt phổi cho rò khí dai dẳng; CT thấy đường thông trực tiếp giữa phế quản và khoang màng phổi.",
    "628-viem-tuy-tang-triglyceride-o-tre":
        "Viêm tụy cấp do tăng triglyceride ở trẻ thường gặp ở trẻ ≥ 10 tuổi mới chẩn đoán đái tháo đường hoặc tự ngừng insulin.",
    "652-dot-quy-mach-mau-nao-nhi-moyamoya-viem-mach":
        "Đột quỵ động mạch ở trẻ chủ yếu do bệnh mạch máu (moyamoya, viêm mạch, bóc tách), nên phải chụp MRA/MRV và đo tưới máu bằng ASL.",
    "655-hie-so-sinh-va-di-dang-bam-sinh-than-kinh":
        "HIE sơ sinh cho hạn chế khuếch tán sớm (ADC đạt đáy ngày 2–4); dị tật bẩm sinh như Chiari II, Dandy-Walker đọc theo mốc giải phẫu.",
    "662-boc-tach-dong-mach-co-o-tre":
        "Bóc tách động mạch cổ ở trẻ hay ở các đoạn 'neo' chịu lực cắt khi cổ duỗi–xoay; CTA/MRA cổ là chốt và phải theo dõi giả phình.",
    "668-theo-doi-sau-thao-cang-tuy-bang-quang-than-kinh":
        "Sau tháo căng tủy, bàng quang thần kinh phải theo dõi bằng urodynamics vì áp lực bàng quang cao làm giảm GFR và giãn đường niệu trên.",
    "669-theo-doi-dai-han-BO-Swyer-James":
        "BO hậu nhiễm trùng và Swyer–James để lại tắc nghẽn tiểu phế quản cố định, theo dõi bằng HRCT thì thở ra (mosaic) và hô hấp ký.",
    "677-cham-soc-ong-dan-luu-tren-xuong-mu-o-tre":
        "Ống dẫn lưu trên xương mu ở trẻ có thể tắc, đóng vảy, sỏi bàng quang, nhiễm đường hầm hoặc di trú; guideline 2025 ưu tiên SPC hơn catheter niệu đạo.",
    "678-cuong-sinh-san-sau-chan-thuong-khung-chau-o-tre":
        "Sau chấn thương khung chậu ở bé trai, rối loạn cương gặp 34% nếu chỉ đặt catheter và 16% nếu nắn chỉnh nội soi thì đầu.",
    "681-chong-ket-tap-tieu-cau-sau-tai-thong-mach-nao-o-tre":
        "Sau tái thông mạch não ở trẻ phải dùng kháng kết tập tiểu cầu vì miệng nối chỉ 1–2 mm, nhưng phải cân nhắc nguy cơ chảy máu.",
    "690-cmmrd-tam-soat-wb-mri-o-tre":
        "CMMRD gây u não ác thời thơ ấu, đa polyp và café-au-lait do đột biến lưỡng alen MMR; cần lịch tầm soát toàn thân bằng MRI.",
    "693-theo-doi-sau-cat-u-gan-o-tre":
        "Sau cắt u gan ở trẻ phải đọc mọi ổ dịch theo bản chất mật–máu–mủ, vì 14% có biến chứng đường mật và còn nguy cơ di căn phổi.",
    "695-hoi-chung-treacher-collins-nager":
        "Treacher Collins và Nager gây thiểu sản xương gò má – hàm dưới đối xứng hai bên; phải mô tả bằng CT xương dựng 3D, không bằng phim sọ nghiêng.",
    "702-oc-tai-nhiem-trung-bao-thai":
        "Cấy ốc tai ở trẻ điếc do nhiễm trùng bào thai (rubella/CMV) cần chọn tai và thời điểm dựa trên hình ảnh tai trong tiền phẫu.",
    "745-hht-o-tre-tam-soat-avm-phoi-nao":
        "HHT ở trẻ gây chảy máu cam tái diễn và AVM tạng: nốt/kính mờ có mạch nuôi và tĩnh mạch dẫn lưu, nhiều ổ, kèm shunt phải–trái.",
    "746-cm-avm-rasa1-ephb4":
        "CM-AVM (RASA1/EPHB4) có nhiều mảng đỏ kèm quầng nhạt và shunt động–tĩnh mạch tốc độ cao ở não–tủy.",
    "747-chan-thuong-rang-o-tre":
        "Chấn thương răng ở trẻ là tổn thương dây chằng nha chu: dày khe PDL và mất lá cứng là dấu sớm, luxation/avulsion cần nẹp đúng ngưỡng.",
    "748-chan-thuong-rang-sua":
        "Răng sữa lún vào xương ổ đẩy chân răng vào mầm răng vĩnh viễn, gây bất thường mầm răng nhiều năm sau nên phải theo dõi dài.",
    "749-nhiem-khuan-rang-lan-trung-that":
        "Nhiễm khuẩn răng lan xuống trung thất theo khoang cổ sâu: khoang dưới hàm chiếm 50,7% vì chân răng hàm dưới nằm dưới đường mylohyoid.",
    "751-viem-xuong-ham-do-rang":
        "Viêm xương hàm do răng gây tiêu xương kèm xương chết và phản ứng màng xương; hàm dưới nghèo mạch nên ổ nhiễm bị 'nhốt' lâu.",
    "752-thieu-san-men-turner-rang-vinh-vien":
        "Thiểu sản men Turner là khiếm khuyết men khu trú một răng vĩnh viễn sau chấn thương răng sữa, kiểu khuyết tùy thời điểm tổn thương.",
    "850-loan-san-co-xo-fibromuscular-dysplasia-toan-than-o-tre":
        "Loạn sản cơ xơ ở trẻ gây hẹp kiểu chuỗi hạt, phình và bóc tách mạch; không dày thành mạch đối xứng nên phân biệt được với viêm mạch.",
    "851-loet-xuyen-thanh-dmc-pau":
        "Loét xuyên thành động mạch chủ là thể thứ ba của hội chứng ĐMC cấp: mảng xơ vữa loét ăn vào trung mạc, kèm huyết khối thành mạch.",
    "935-toi-uu-lieu-can-thiep-nhi-drl":
        "Can thiệp nhi cần DRL theo kích thước cơ thể: cùng một DAP dồn vào khối mô nhỏ hơn nên liều hiệu dụng ở sơ sinh cao hơn nhiều.",
    "936-phan-ung-da-muon-nang-sau-can-quang":
        "Phản ứng da muộn nặng sau cản quang (AGEP, DRESS, SJS/TEN) do cả phân tử thuốc quyết định, không do nguyên tử i-ốt.",
    "937-lieu-ct-tre-ssde-drl":
        "Liều CT ở trẻ phải đọc bằng SSDE thay CTDIvol và so với DRL nhi, vì mô đang phân bào nhạy với bức xạ hơn.",
    "938-ro-dong-mach-chu-ruot":
        "Rò động mạch chủ–ruột cho khí ngoài lòng trong túi phình hoặc quanh miếng ghép, mất mặt phẳng mỡ với ruột và thoát cản quang vào lòng ruột.",
    "939-ro-dong-mach-chu-tinh-mach-chu":
        "Rò động mạch chủ–tĩnh mạch chủ làm tĩnh mạch chủ ngấm cản quang đồng thời với động mạch chủ ở thì động mạch, gặp ở 2–6,7% phình vỡ.",
    "942-ro-dong-mach-chu-nieu-quan":
        "Rò động mạch chủ–niệu quản gây tiểu máu ồ ạt ngắt quãng và cản quang trong lòng niệu quản ở thì động mạch tại chỗ bắt chéo mạch.",
    "943-viem-co-tim-do-dress":
        "Viêm cơ tim do DRESS gây phù cơ tim và ngấm thuốc muộn dưới nội tâm mạc do bạch cầu ái toan thoái hạt, không do tắc mạch vành.",
    "945-nhiem-va-bien-chung-port-a-cath":
        "Biến chứng port-a-cath gồm nhiễm khu trú túi port, huyết khối và tràn dịch; vị trí đầu catheter ở ngã ba tĩnh mạch chủ trên–nhĩ phải quyết định.",
    "946-nhiem-trung-manh-ghep-mach-mau":
        "Nhiễm trùng mảnh ghép mạch máu khó chẩn đoán: CT và cả PET/CT đều không đủ, vì biofilm trên PTFE/Dacron có thể âm thầm nhiều năm.",
    "968-cuong-giap-do-amiodarone-ait-type-1-2":
        "Cường giáp do amiodarone phân type bằng Doppler màu: PSV động mạch giáp trên > 100 cm/s là type 1, < 45–50 cm/s là type 2.",
    "972-buou-giap-thong-trung-that":
        "Bướu giáp thòng trung thất là khối trung thất trên chèn ép khí quản; CT đánh giá chèn ép và quyết định có phải mở xương ức.",
    "1402-bong-vong-mac-sau-viem-noi-nhan":
        "Bong võng mạc sau viêm nội nhãn có hai cơ chế: lỗ hoại tử toàn bộ bề dày gây bong rách, hoặc màng viêm co kéo gây bong/PVR.",
    "1407-cnv-loan-duong-hoa-van-prph2":
        "Tân mạch hắc mạc trên nền loạn dưỡng hoa văn PRPH2: FAF tăng huỳnh quang do ứ lipofuscin, phải phân biệt với u mạch.",
    "1408-anti-vegf-thai-ky-cho-con-bu":
        "Chọn anti-VEGF nội dịch kính trong thai kỳ và cho con bú dựa vào phân tử có Fc hay không, vì Fc quyết định mức thoát vào tuần hoàn.",
    "1409-benh-vong-mac-do-xa-sau-xa-tri":
        "Bệnh võng mạc do xạ là bệnh vi mạch tắc nghẽn tiến triển kèm phù hoàng điểm; bệnh sử xạ trị là chốt, không phải hình thái tổn thương.",
    "1410-lay-dau-silicone-va-dau-ton-luu":
        "Dầu silicone nhũ tương hóa cho giọt tăng phản xạ trên OCT, hồi âm mạnh trên B-scan và giọt ở góc tiền phòng; phải cân nhắc bong tái phát khi lấy.",
    "1411-tang-nhan-ap-do-corticoid-noi-nhan":
        "Tăng nhãn áp do corticoid nội nhãn là xơ hóa bè chứ không phải phù, nên phải theo dõi nhãn áp sau tiêm và sau implant dexamethasone/fluocinolone.",
    "1413-tut-mat-co-truc-trong-sau-mo-lac":
        "Tụt hoặc mất cơ trực trong sau mổ lác cho lác ngoài lớn kèm hạn chế khép; MRI/AS-OCT định vị cơ và quyết định mổ lại.",
    "1416-glaucom-do-dau-silicone":
        "Glôcôm do dầu silicone xảy ra theo ba cơ chế: pupillary block, bít bè bởi giọt nhũ tương, hoặc góc đóng; mỗi cơ chế một cách xử trí.",
    "1417-giu-dau-silicone-vinh-vien":
        "Giữ dầu silicone vĩnh viễn khi bong tái phát nếu lấy; phải theo dõi nhũ tương hóa, dầu đục và tổn thương thị thần kinh dài hạn.",
    "1418-phu-hoang-diem-xa-khang-anti-vegf":
        "Phù hoàng điểm do xạ dai dẳng, kháng anti-VEGF nên chuyển sang implant dexamethasone 0,7 mg hoặc fluocinolone acetonide 0,19 mg.",
    "1419-vong-mac-xa-tre-sau-xa-tri":
        "Bệnh võng mạc do xạ ở trẻ sau xạ trị u não/retinoblastoma cần lịch OCT/OCTA và phải phân biệt biến chứng xạ với tái phát u.",
    "1420-ap-xe-gan-klebsiella-va-viem-noi-nhan":
        "Áp-xe gan do Klebsiella kèm viêm nội nhãn nội sinh cần dẫn lưu ổ gan và tiêm nội nhãn đúng thứ tự trong cửa sổ can thiệp.",
    "1421-nhan-thuc-sau-doc-than-kinh-mtx":
        "Sau độc tính thần kinh do methotrexate, tổn thương chất trắng tồn tại trên ảnh nhưng triệu chứng nhận thức không tương xứng.",
    "1422-hvkp-khong-o-gan-va-di-can-an":
        "Nhiễm khuẩn huyết do hvKP không có ổ gan vẫn di căn ẩn, nên phải tầm soát bộ ba mắt–não–phổi.",
    "1423-doc-tinh-methotrexate-noi-tuy":
        "Methotrexate nội tủy gây tổn thương chất trắng hạn chế khuếch tán và chừa vỏ não, hoặc viêm màng não vô khuẩn sau tiêm.",
    "1425-viem-noi-nhan-sau-tiem-noi-nhan":
        "Viêm nội nhãn sau tiêm nội nhãn cấp trong 1–3 ngày với mủ tiền phòng và viêm dịch kính; B-scan là chốt khi không soi được đáy mắt.",
    "1426-viem-noi-nhan-tai-phat-khong-dap-ung":
        "Viêm nội nhãn sau tiêm tái phát vì ổ nhiễm kín trong fibrin dịch kính, nên cắt dịch kính vừa lấy mẫu vừa mở khoang mủ.",
    "1427-tiem-anti-vegf-hai-mat-cung-ngay":
        "Tiêm anti-VEGF hai mắt cùng ngày giảm số buổi từ 26 xuống 13 mỗi năm, nhưng phải cân nhắc biến cố xảy ra ở cả hai bên.",
    "1428-phu-giac-mac-sau-implant-tien-phong":
        "Implant corticoid lạc vào tiền phòng gây phù giác mạc một bên; vật thể hình que 0,46 × 6 mm là dấu nhận diện.",
    "1429-lo-hoang-diem-thu-phat-manh-oi":
        "Lỗ hoàng điểm thứ phát sau mổ ROP/bong võng mạc phức tạp không tự đóng vì bờ teo, thiếu màng giới hạn trong và co kéo sau cực.",
    "1431-quang-dong-the-mi-mat-bom-dau":
        "Quang đông thể mi ở mắt bơm dầu phải chọn CW 'pop', slow-coag hay micropulse theo vị trí thể mi đã dịch ra sau, không theo dầu.",
    "1432-thay-dau-silicone":
        "Thay dầu silicone khi bơm thiếu thể tích, nhũ tương nặng hoặc dầu đục: tamponade do sức căng mặt phân cách, không do độ nhớt.",
    "1433-viem-noi-nhan-mat-bom-dau":
        "Viêm nội nhãn ở mắt bơm dầu bị dầu đục che lấp; phải cấy dịch kính–dầu rồi quyết định lấy hay giữ dầu.",
    "1434-ha-nhan-ap-rach-the-mi-sau-quang-dong":
        "Hạ nhãn áp sau quang đông thể mi cần phân biệt suy thể mi với rách thể mi; UBM 35–50 MHz là chốt để thấy khe thông.",
    "1435-hoi-chung-masquerade-u-lympho-noi-nhan":
        "Hội chứng masquerade nội nhãn: viêm màng bồ đào tái phát không đáp ứng corticoid kèm thâm nhiễm dưới biểu mô sắc tố là u lympho nội nhãn.",
    "1436-benh-vogt-koyanagi-harada":
        "VKH gây viêm hắc mạc hai bên và bong võng mạc thanh dịch, diễn tiến thành sunset glow fundus; chốt bằng hình ảnh hắc mạc dày.",
    "1437-viem-mang-bo-dao-do-uc-che-diem-kiem-mien-dich":
        "Viêm màng bồ đào do thuốc ức chế điểm kiểm miễn dịch gây viêm hai bên kiểu giống VKH do tế bào T nhận diện kháng nguyên tế bào hắc tố.",
    "1440-mnt-parkinsonism-sau-car-t-bcma":
        "Parkinsonism muộn sau CAR-T nhắm BCMA có MRI thường bình thường; khi bất thường thấy T2/FLAIR tăng ở nhân đuôi–thể vân.",
    "1442-manh-the-thuy-tinh-con-sot":
        "Mảnh thể thủy tinh còn sót gây phù giác mạc một bên và viêm tiền phòng tái diễn nhiều năm sau phaco, thấy là mảnh trắng bờ nham nhở ở góc.",
    "1444-viem-mang-bo-dao-sau-chan-thuong":
        "Viêm màng bồ đào sau chấn thương kín là viêm tiền phòng vô khuẩn một bên, nhưng phải theo dõi vì có thể là khởi đầu viêm giao cảm.",
    "1446-phu-hoang-diem-sau-quang-dong-the-mi":
        "Phù hoàng điểm dạng nang sau quang đông thể mi do viêm chứ không do bắt giữ dịch; OCT thấy dày trung tâm và khoang nang, không có màng co kéo.",
})

def _desc_ok(t):
    """Ứng viên mô tả hợp lệ: đủ dài, không boilerplate/link list/nhãn mục."""
    low = t.lower()
    if any(b in low for b in BOILERPLATE):
        return False
    if "](" in t or "http" in low or "nguồn:" in low:
        return False
    if re.match(r"^\d+\s*[–—-]\s*\d+\s*[–—-]", t):  # nhãn dải ID "300–319 — ..."
        return False
    p = _plain_cmp(t)
    if len(p) < 55 or p.endswith(":"):
        return False
    return p[:1].isupper() or p[:1].isdigit()


def desc_candidates(body):
    """Mọi câu/đoạn/gạch đầu dòng có thể làm mô tả, theo thứ tự trong bài."""
    out, in_fence = [], False
    for raw in body.splitlines():
        s = raw.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not s:
            continue
        if s.startswith(("#", "**Tags", "**Mức chắc chắn", "*Không dùng", "|", "!", "<")):
            continue
        # bỏ caption ảnh: "*Trái: ... Nguồn: ...", "*Hình ...", "Panel ..."
        if re.match(r"^\*?\s*(Trái|Phải|Hình|Ảnh|Panel|A\)|B\))\b", s):
            continue
        if ("Nguồn:" in s or "Fig." in s) and s.startswith("*"):
            continue
        t = s
        if t.startswith(">"):  # blockquote: "> **Ca 1.** bệnh nhân ..."
            t = re.sub(r"^[>\s]+", "", t).strip()
        elif re.match(r"^([-*+]|\d+\.)\s", t):  # gạch đầu dòng: "- **X:** ..."
            t = re.sub(r"^([-*+]|\d+\.)\s+", "", t).strip()
        if _desc_ok(t):
            out.append(t.lstrip("*").strip())
    return out


# nhãn "dẫn chuyện" — bỏ đi để câu còn lại đọc như mô tả, không như ghi chú soạn bài
DISCARD_LABEL = re.compile(
    r"^(?:Câu chốt|Điểm chốt(?: của bài)?|Điểm tựa(?: duy nhất của bài)?|Định nghĩa|"
    r"Cơ chế(?: 1 câu)?|Bệnh học|Câu hỏi thực hành|Kịch bản thực hành|"
    r"Vì sao bài này quan trọng|Bài toán CĐHA của vùng này khác hẳn[^:]*)\s*(?:\([^)]*\))?\s*:\s*[\*_]*\s*",
    re.I,
)


def _tidy_desc(t):
    t = re.sub(r"^[\s*_>]+", "", t or "")
    t = DISCARD_LABEL.sub("", t).strip()
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    return t


def _strict_paragraph(body):
    """Đoạn văn "thuần" đầu tiên đủ dài (≥ 70 ký tự) — đường chính, giữ nguyên hành vi cũ."""
    in_fence = False
    for raw in body.splitlines():
        s = raw.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not s:
            continue
        if s.startswith(("#", "**Tags", "**Mức chắc chắn", "*Không dùng", ">", "|", "!", "<")):
            continue
        if re.match(r"^([-*+]|\d+\.)\s", s):
            continue
        # bỏ caption ảnh: "*Trái: ... Nguồn: ...", "*Hình ...", "Panel ..."
        if re.match(r"^\*?\s*(Trái|Phải|Hình|Ảnh|Panel|A\)|B\))\b", s):
            continue
        if ("Nguồn:" in s or "Fig." in s) and s.startswith("*"):
            continue
        if len(s) < 70:
            continue
        return s.lstrip("*").strip()
    return None


def describe(body):
    """(mô tả, dùng_đường_dự_phòng) cho một lesson.md.

    Bài mở đầu bằng bảng/gạch đầu dòng/blockquote (không có đoạn văn thuần ≥ 70 ký tự)
    sẽ lấy câu chốt/định nghĩa đầu tiên, rồi tới câu hợp lệ đầu tiên — thay vì rơi về
    SITE_DESC dùng chung cho mọi bài.
    """
    strict = _strict_paragraph(body)
    if strict:
        return strict, False
    cands = desc_candidates(body)
    if not cands:
        return SITE_DESC, False
    for lead in DESC_LEAD:
        for c in cands:
            if c.lstrip("*_ ").startswith(lead):
                return _tidy_desc(c), True
    return _tidy_desc(cands[0]), True


def first_paragraph(body):
    """Mô tả một dòng cho bài (dùng cho meta/JSON-LD/llms.txt)."""
    return describe(body)[0]


def git_lastmod_map():
    """1 lần git log → {folder/lesson.md: 'YYYY-MM-DD'} (lần xuất hiện đầu là mới nhất)."""
    try:
        out = subprocess.run(
            ["git", "log", "--format=__D__%cs", "--name-only", "--", "*/lesson.md"],
            cwd=ROOT, capture_output=True, text=True, timeout=180,
        ).stdout
    except Exception:
        return {}
    dmap, cur = {}, None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("__D__"):
            cur = line[5:]
        elif line.endswith("/lesson.md") and cur and line not in dmap:
            dmap[line] = cur
    return dmap


def spec_label(uid, tags, title):
    if bi is None:
        return "Chẩn đoán hình ảnh"
    tagstr = " ".join(tags) if isinstance(tags, (list, tuple)) else (tags or "")
    spec = bi.spec_for(uid, tagstr, title)
    return dict(bi.TABS).get(spec, "Chẩn đoán hình ảnh").split(" ", 1)[-1]


# ── template ────────────────────────────────────────────────────────────────
def jsonld(slug, title, desc, lastmod, primary, spec, image):
    url = f"{BASE}/{slug}/"
    about = [{"@type": "Thing", "name": primary}] if primary else []
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "MedicalWebPage",
                "@id": url + "#webpage",
                "url": url,
                "name": title,
                "description": desc,
                "inLanguage": "vi",
                "isPartOf": {"@id": BASE + "/#website"},
                "dateModified": lastmod,
                "about": about,
                "audience": {"@type": "MedicalAudience", "audienceType": "Physician, MedicalStudent"},
                "isAccessibleForFree": True,
                "specialty": "Radiology",
            },
            {
                "@type": "LearningResource",
                "name": title,
                "description": desc,
                "url": url,
                "inLanguage": "vi",
                "learningResourceType": "Bài học chẩn đoán hình ảnh",
                "educationalLevel": "Chuyên khoa",
                "isAccessibleForFree": True,
                "dateModified": lastmod,
                "provider": {"@type": "Organization", "name": SITE_NAME, "url": BASE + "/"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Hub tra cứu", "item": BASE + "/"},
                    {"@type": "ListItem", "position": 2, "name": spec, "item": BASE + "/"},
                    {"@type": "ListItem", "position": 3, "name": title, "item": url},
                ],
            },
            {
                "@type": "WebSite",
                "@id": BASE + "/#website",
                "url": BASE + "/",
                "name": SITE_NAME,
                "description": SITE_DESC,
                "inLanguage": "vi",
            },
        ],
    }, ensure_ascii=False)


PAGE = """<!doctype html>
<!-- lesson-sha256: __HASH__ -->
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6VCXZNSLK1"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-6VCXZNSLK1');</script>
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="__URL__">
<link rel="alternate" hreflang="vi" href="__URL__">
<link rel="alternate" type="text/markdown" href="__URL__lesson.md" title="Markdown gốc">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/lesson.css">
<style>
#noi-dung img{cursor:zoom-in}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;align-items:center;justify-content:center;flex-direction:column;z-index:9999;overflow:hidden}
#lb.open{display:flex}
#lb img{max-width:96vw;max-height:86vh;object-fit:contain;background:#000;border-radius:0;cursor:grab;user-select:none;-webkit-user-select:none;touch-action:none;transition:transform .12s}
#lb img.drag{transition:none;cursor:grabbing}
#lb .cap{color:#ddd;font-size:13px;margin-top:8px;max-width:92vw;text-align:center}
#lb .x{position:absolute;top:10px;right:16px;z-index:2;color:#fff;font-size:28px;line-height:1;cursor:pointer;background:none;border:0}
#lb .orig{position:absolute;top:14px;left:16px;z-index:2;color:#cfe3ff;font-size:13px;text-decoration:none;border:1px solid rgba(255,255,255,.4);border-radius:999px;padding:5px 12px;background:rgba(0,0,0,.35)}
#lb .orig:hover{background:rgba(255,255,255,.15);color:#fff}
</style>
<meta name="author" content="__SITE__">
<meta property="og:type" content="article">
<meta property="og:site_name" content="__SITE__">
<meta property="og:locale" content="vi_VN">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__URL__">
<meta property="og:image" content="__IMAGE__">
<meta property="og:image:alt" content="__TITLE__">
<meta property="article:modified_time" content="__LASTMOD__">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="__DESC__">
<meta name="twitter:image" content="__IMAGE__">
<script type="application/ld+json">__JSONLD__</script>
</head>
<body>
<a class="skip" href="#noi-dung">Bỏ qua điều hướng</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/"><img src="/assets/favicon.svg" alt="" width="22" height="22"> __SITE__</a>
    <span class="grow"></span>
    <label class="learnbox" title="Đánh dấu bài này đã học (lưu trong trình duyệt của bạn)">
      <input type="checkbox" class="learn-chk" data-id="__UID__"> <span class="learn-txt">Đã học</span>
    </label>
  </div>
</header>
<main class="wrap" id="noi-dung">
  <nav class="crumbs" aria-label="Breadcrumb">
    <a href="/">Hub tra cứu</a><span class="sep">›</span><span>__SPEC__</span><span class="sep">›</span><span>__UID__</span>
  </nav>
  <div class="page-meta">
    <span class="badge">__SPEC__</span>
    <span class="badge">Mức chắc chắn: __CERT__</span>
    <time datetime="__LASTMOD__">Cập nhật: __LASTMOD__</time>
  </div>
  <article>
__BODY__
  </article>
  <aside class="note">
    <strong>Lưu ý:</strong> bài học tổng hợp từ y văn mở, dùng để học và tra cứu — không thay thế
    chẩn đoán của bác sĩ có trách nhiệm. Nguồn chi tiết: <a href="sources.md">sources.md</a> ·
    <a href="images/CREDITS.md">giấy phép ảnh</a>.
  </aside>
  <nav class="pager" aria-label="Điều hướng bài học">
    <span>__PREV__</span><span>__NEXT__</span>
  </nav>
</main>
<footer class="site-foot">
  <div class="wrap">
    <p>__SITE__ · <a href="/">Hub tra cứu</a> · <a href="/about.html">Giới thiệu &amp; quy trình biên soạn</a> ·
    <a href="/sitemap.xml">Sitemap</a></p>
    <p>Không dùng để chẩn đoán độc lập khi chưa có người hướng dẫn.</p>
  </div>
</footer>
<script>
(function(){
  var LKEY='rad-learned', uid='__UID__';
  var box=document.querySelector('.learnbox'), chk=document.querySelector('.learn-chk');
  if(!box||!chk) return;
  function get(){try{return JSON.parse(localStorage.getItem(LKEY)||'{}')||{}}catch(e){return {}}}
  function set(o){try{localStorage.setItem(LKEY,JSON.stringify(o))}catch(e){}}
  function paint(on){box.classList.toggle('on',on);chk.checked=on;
    box.querySelector('.learn-txt').textContent=on?'Đã học ✓':'Đã học';}
  paint(!!get()[uid]);
  chk.addEventListener('change',function(){var o=get();if(chk.checked)o[uid]=1;else delete o[uid];set(o);paint(chk.checked);});
})();
</script>
<div id="lb" role="dialog" aria-modal="true" aria-label="Xem ảnh phóng to"><button class="x" type="button" aria-label="Đóng">×</button><a class="orig" href="#" target="_blank" rel="noopener" aria-label="Mở ảnh gốc ở tab mới">Mở ảnh gốc ↗</a><img alt="" draggable="false"><div class="cap"></div></div>
<script>
(function(){
  var box=document.getElementById('noi-dung'), lb=document.getElementById('lb');
  if(!box||!lb) return;
  var im=lb.querySelector('img'), cap=lb.querySelector('.cap'), xb=lb.querySelector('.x');
  var orig=lb.querySelector('.orig');
  var sc=1, tx=0, ty=0, drag=null;
  var imgs=[], idx=-1;
  function tf(){ im.style.transform='translate('+(tx?tx+'px':'0')+','+(ty?ty+'px':'0')+') scale('+sc+')'; }
  function reset(){ sc=1; tx=0; ty=0; tf(); }
  function r2(v){ return Math.round(v*100)/100; }
  // tâm ảnh khi CHƯA transform (đo theo layout: không phụ thuộc scale/transition)
  function ctr(){
    var w=im.offsetWidth, h=im.offsetHeight;
    if(w&&h){ var b=lb.getBoundingClientRect();
      return {x:b.left+lb.clientLeft+im.offsetLeft+w/2, y:b.top+lb.clientTop+im.offsetTop+h/2};
    }
    var q=im.getBoundingClientRect();
    return {x:q.left+q.width/2-tx, y:q.top+q.height/2-ty};
  }
  // zoom neo ĐIỂM DƯỚI CON TRỎ: chi tiết đang trỏ đứng yên tại chỗ, không trôi về giữa ảnh
  function zoomAt(s2,mx,my){
    if(s2===sc) return;
    var c=ctr(), k=s2/sc;
    tx=r2((mx-c.x)*(1-k)+k*tx);
    ty=r2((my-c.y)*(1-k)+k*ty);
    sc=s2;
    if(sc===1){ tx=0; ty=0; }
    tf();
  }
  function close(){ lb.classList.remove('open'); reset(); idx=-1; }
  // hiển thị ảnh thứ i trong danh sách ảnh của #noi-dung (thứ tự DOM);
  // src + caption + nút "Mở ảnh gốc" đổi cùng lúc, zoom/pan về 1×
  function show(i){
    if(i<0||i>=imgs.length) return;
    var el=imgs[i], src=el.currentSrc||el.src;
    idx=i;
    im.src=src; im.alt=el.alt||'';
    cap.textContent=el.alt||'';
    if(orig) orig.href=src;
    reset();
  }
  function open(img){
    imgs=Array.prototype.slice.call(box.querySelectorAll('img'));
    var i=imgs.indexOf(img);
    if(i<0) return;
    show(i);
    lb.classList.add('open');
  }
  box.addEventListener('click',function(e){
    var el=e.target, img=el&&el.closest?el.closest('img'):null;
    if(!img||!box.contains(img)) return;
    e.preventDefault();
    open(img);
  });
  lb.addEventListener('click',function(e){ if(e.target!==im) close(); });
  xb.addEventListener('click',function(e){ e.stopPropagation(); close(); });
  // nút "Mở ảnh gốc": mở tab mới, KHÔNG đóng overlay (như nút ×)
  if(orig) orig.addEventListener('click',function(e){ e.stopPropagation(); });
  document.addEventListener('keydown',function(e){
    if(!lb.classList.contains('open')) return;   // đang đọc bài thì phím ←/→ không bị chiếm
    var k=e.key;
    if(k==='Escape'||k==='Esc'){ close(); return; }
    // ←/→ chuyển ảnh theo thứ tự DOM; ở ảnh đầu/cuối thì DỪNG (không vòng lại)
    if(k==='ArrowRight'||k==='Right'){ e.preventDefault(); show(idx+1); return; }
    if(k==='ArrowLeft'||k==='Left'){ e.preventDefault(); show(idx-1); return; }
  });
  im.addEventListener('wheel',function(e){
    e.preventDefault(); e.stopPropagation();
    zoomAt(Math.min(4,Math.max(1,sc+(e.deltaY<0?0.25:-0.25))),e.clientX,e.clientY);
  },{passive:false});
  function down(x,y){ if(sc<=1) return; drag={x:x,y:y,tx:tx,ty:ty}; im.classList.add('drag'); }
  function moveT(x,y){ if(!drag) return; tx=drag.tx+(x-drag.x); ty=drag.ty+(y-drag.y); tf(); }
  function up(){ drag=null; im.classList.remove('drag'); }
  im.addEventListener('mousedown',function(e){ if(sc>1){ e.preventDefault(); down(e.clientX,e.clientY); } });
  document.addEventListener('mousemove',function(e){ if(drag) moveT(e.clientX,e.clientY); });
  document.addEventListener('mouseup',up);
  im.addEventListener('touchstart',function(e){
    if(e.touches.length===1) down(e.touches[0].clientX,e.touches[0].clientY);
  },{passive:true});
  im.addEventListener('touchmove',function(e){
    if(drag&&e.touches.length===1){ moveT(e.touches[0].clientX,e.touches[0].clientY); if(e.cancelable) e.preventDefault(); }
  },{passive:false});
  im.addEventListener('touchend',up);
  im.addEventListener('touchcancel',up);
})();
</script>
__MERMAID__
</body>
</html>
"""

MERMAID = """<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
mermaid.initialize({startOnLoad:false,securityLevel:"loose",
  theme: matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "default"});
try { await mermaid.run({querySelector:".mermaid"}); } catch (e) { console.warn("mermaid:", e); }
</script>"""


# ── build ───────────────────────────────────────────────────────────────────
def collect(only=None):
    ids = None
    if only:
        ids = {s.strip() for s in str(only).replace(" ", ",").split(",") if s.strip()}
    items = []
    for d in sorted(os.listdir(ROOT)):
        m = LESSON_RE.match(d)
        if not m or not os.path.isdir(os.path.join(ROOT, d)):
            continue
        lp = os.path.join(ROOT, d, "lesson.md")
        if not os.path.exists(lp):
            continue
        if ids and m.group(1) not in ids:
            continue
        items.append((m.group(1), d, lp))
    return items


def render(items):
    payload = []
    bodies = {}
    for uid, slug, lp in collect():
        text = read(lp)
        fm, body = split_frontmatter(text)
        bodies[slug] = (uid, fm, body, text)
        payload.append({"id": slug, "md": body})
    p = subprocess.run(
        ["node", os.path.join(ROOT, "tools", "render_markdown.js")],
        input=json.dumps({"items": payload}, ensure_ascii=False),
        capture_output=True, text=True, cwd=ROOT, timeout=600,
    )
    if p.returncode != 0:
        raise SystemExit("render_markdown.js FAIL:\n" + (p.stderr or "")[-2000:])
    return {it["id"]: it for it in json.loads(p.stdout)["items"]}, bodies


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sinh trang bài học tĩnh + sitemap + llms.txt")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", help="chỉ (các) ID, cách nhau dấu phẩy (vd 020 hoặc 020,025)")
    ap.add_argument("--sitemap", action="store_true")
    ap.add_argument("--check", action="store_true", help="chỉ kiểm, không ghi")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if not a.all and not a.only:
        ap.error("cần --all hoặc --only <ID>")

    items = collect(a.only)
    if not items:
        raise SystemExit("Không tìm thấy bài nào.")
    rendered, bodies = render(items)
    lastmods = git_lastmod_map()
    today = date.today().isoformat()

    order = [d for _, d, _ in collect()]
    idx = {d: i for i, d in enumerate(order)}

    changed = 0
    for uid, slug, lp in items:
        it = rendered[slug]
        fm, body, raw = bodies[slug][1], bodies[slug][2], bodies[slug][3]
        h1m = re.search(r"^#\s+(.+)$", body, re.M)
        title = h1m.group(1).strip() if h1m else slug
        if len(title) > 95:
            title = title[:95].rsplit(" ", 1)[0] + "…"
        # bỏ markdown nhấn mạnh trong <title>/meta (H1 hiển thị vẫn do marked render)
        title = re.sub(r"[*_`]+", "", title).strip()
        tags = fm.get("tags") or []
        spec = spec_label(uid, tags, title)
        cert = fm.get("certainty", "")
        cert_label = {"ca-nguyen-van": "ca nguyên văn", "tong-hop-y-van": "tổng hợp y văn",
                      "suy-luan": "suy luận"}.get(cert, cert or "tổng hợp y văn")
        para, relaxed = describe(body)
        desc = plain(para, 158) or SITE_DESC
        pattern = plain(str(fm.get("primary_pattern", "")), 155)
        tvi = re.sub(r"^\d+\s*[—–-]\s*", "", title).split(" / ")[0].strip()
        if slug in PATTERN_DESC:
            desc = plain(PATTERN_DESC[slug], 158)  # cụm mẫu hình → một câu tiếng Việt
        elif len(pattern) >= 80:
            desc = pattern
        elif relaxed and (158 - len(tvi) - 3) < 70:
            desc = plain(desc, 158)  # tên bài quá dài: giữ nội dung, đừng ghép tên
        elif relaxed and re.match(r"^[^:]{3,45}:", desc):
            desc = plain(f"{tvi} — {desc}", 158)  # câu đã có nhãn "X:" → dùng gạch dài
        else:
            desc = plain(f"{tvi}: {desc}", 158)
        lastmod = lastmods.get(f"{slug}/lesson.md", today)
        url = f"{BASE}/{slug}/"
        img = it.get("firstImage") or "/assets/og-default.png"
        if img.startswith("images/"):
            img = (cdn.public_url(f"{slug}/{img}") if cdn else None) or f"{BASE}/{slug}/{img}"
        elif img.startswith("/"):
            img = BASE + img
        sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        prev_html = next_html = ""
        i = idx.get(slug)
        if i is not None and i > 0:
            pd = order[i - 1]
            pt = re.search(r"^#\s+(.+)$", read(os.path.join(ROOT, pd, "lesson.md")), re.M)
            prev_html = f'<a href="/{pd}/">← {html.escape((pt.group(1) if pt else pd)[:70])}</a>'
        if i is not None and i + 1 < len(order):
            nd = order[i + 1]
            nt = re.search(r"^#\s+(.+)$", read(os.path.join(ROOT, nd, "lesson.md")), re.M)
            next_html = f'<a href="/{nd}/">{html.escape((nt.group(1) if nt else nd)[:70])} →</a>'

        body_html = it["html"].strip()
        # vài bài cũ ghi ảnh dạng "<slug>/images/..." → trên trang /<slug>/ sẽ thành /<slug>/<slug>/images
        body_html = body_html.replace(f'src="{slug}/images/', 'src="images/')
        if cdn is not None:
            body_html = cdn.rewrite_images(body_html, slug)
        page = (PAGE
                .replace("__HASH__", sha)
                .replace("__TITLE__", html.escape(title))
                .replace("__DESC__", html.escape(desc, quote=True))
                .replace("__URL__", url)
                .replace("__IMAGE__", html.escape(img, quote=True))
                .replace("__LASTMOD__", lastmod)
                .replace("__JSONLD__", jsonld(slug, title, desc, lastmod, fm.get("primary_pattern", ""), spec, img))
                .replace("__SITE__", SITE_NAME)
                .replace("__SPEC__", html.escape(spec))
                .replace("__UID__", uid)
                .replace("__CERT__", html.escape(cert_label))
                .replace("__BODY__", body_html)
                .replace("__PREV__", prev_html)
                .replace("__NEXT__", next_html)
                .replace("__MERMAID__", MERMAID if it.get("mermaid") else ""))

        out = os.path.join(ROOT, slug, "index.html")
        if a.check:
            if not os.path.exists(out):
                print(f"THIẾU: {slug}/index.html")
                return 1
        elif write_if_changed(out, page):
            changed += 1

    if a.sitemap or a.all:
        if not a.check:
            build_sitemap(lastmods, today)
            build_llms(items)
    if not a.quiet:
        print(f"build_lesson_pages: {len(items)} bài, ghi {changed} trang"
              + (", sitemap+llms" if (a.sitemap or a.all) else ""))
    return 0


def build_sitemap(lastmods, today):
    urls = [(BASE + "/", lastmods.get("README.md", today), "1.0"),
            (BASE + "/about.html", today, "0.5")]
    for _, slug, lp in collect():
        lm = lastmods.get(f"{slug}/lesson.md", today)
        urls.append((f"{BASE}/{slug}/", lm, "0.8"))
    body = "\n".join(
        f"  <url><loc>{html.escape(u)}</loc><lastmod>{lm}</lastmod>"
        f"<changefreq>monthly</changefreq><priority>{p}</priority></url>"
        for u, lm, p in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{body}\n</urlset>\n")
    write_if_changed(os.path.join(ROOT, "sitemap.xml"), xml)


def build_llms(items):
    lines = [f"# {SITE_NAME}", "", f"> {SITE_DESC}", "",
             f"Trang chủ: {BASE}/  ·  Sitemap: {BASE}/sitemap.xml  ·  Giới thiệu: {BASE}/about.html", "",
             "Mỗi bài có URL riêng dạng /<id>-<slug>/; bản Markdown gốc ở /<id>-<slug>/lesson.md.", "",
             "## Bài học"]
    for uid, slug, lp in collect():
        text = read(lp)
        fm, body = split_frontmatter(text)
        h1 = re.search(r"^#\s+(.+)$", body, re.M)
        title = (h1.group(1) if h1 else slug).strip()
        override = PATTERN_DESC.get(slug)
        desc = plain(override, 158) if override else plain(first_paragraph(body), 120)
        lines.append(f"- [{title}]({BASE}/{slug}/) — {desc}")
    lines += ["", "## Ghi chú", "",
              "- Nội dung tổng hợp từ y văn mở, có trích dẫn PMCID/DOI trong sources.md.",
              "- Không dùng để chẩn đoán độc lập khi chưa có người hướng dẫn.",
              "- Ảnh giữ nguyên giấy phép ghi trong images/CREDITS.md từng bài."]
    write_if_changed(os.path.join(ROOT, "llms.txt"), "\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
