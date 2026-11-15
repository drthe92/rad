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

# ── Đợt 2–3 (task rad-desc-std-003): 360 bài `primary_pattern` còn lại —
# cùng quy tắc: 1 câu tiếng Việt ≤ 158 ký tự rút từ chính nội dung bài.
# Hết nhóm: 26 (89203a74) + 180 (đợt 1) + 360 (đợt này) = 566.
PATTERN_DESC.update({
    "1447-rach-the-mi-sau-migs-va-yamane":
        "Rách thể mi sau MIGS hoặc sau cố định IOL kiểu Yamane tạo đường rò nội bộ: hạ nhãn áp, tiền phòng nông, khe góc thấy trên UBM/AS-OCT.",
    "1448-glaucoma-ac-tinh-sau-mo-noi-nhan":
        "Glôcôm ác tính sau mổ nội nhãn là tiền phòng dẹt kèm nhãn áp cao do thủy dịch đi lạc hướng ra sau, không phải do chèn ép.",
    "1449-tiem-noi-nhan-o-benh-nhan-dung-thuoc-chong-dong":
        "Tiêm nội nhãn ở người dùng chống đông hoặc kháng kết tập tiểu cầu: nguy cơ xuất huyết thấp, phần lớn tiếp tục thuốc chứ không ngừng.",
    "1453-oct-rnfl-gcl-opg-nf1":
        "Theo dõi OPG–NF1 bằng OCT: mỏng lớp tế bào hạch và RNFL phản ánh teo ngược sợi trục sau chèn ép đường thị, có thể báo trước giảm thị lực.",
    "1454-dat-iol-mat-phacolytic":
        "Ở mắt phacolytic đã lấy thể thủy tinh, bao–dây chằng không vững nên phải chọn IOL trong bao, rãnh thể mi hay không đặt, và hiệu chỉnh công suất.",
    "1455-anti-vegf-mat-da-cat-dich-kinh":
        "Sau cắt dịch kính, anti-VEGF bị thải nhanh hơn vì mất tác dụng giữ thuốc của gel dịch kính, nên khoảng tái tiêm phải ngắn lại.",
    "1457-glaucom-te-bao-hong-cau-sau-xuat-huyet-dich-kinh":
        "Glôcôm tế bào hồng cầu ma sau xuất huyết dịch kính gây tăng nhãn áp MUỘN, không viêm, không flare, không dính đồng tử.",
    "1458-benh-than-kinh-thi-do-xa-o-tre":
        "Bệnh thần kinh thị do xạ ở trẻ cho ngấm thuốc và phì đại đoạn dây thị trong trường chiếu như 'giả u', rồi teo và mù muộn không hồi phục.",
    "1460-viem-giac-mac-do-nam":
        "Viêm giác mạc do nấm có ổ thâm nhiễm nhu mô bờ lông vũ kèm tổn thương vệ tinh và mảng nội mô; IVCM và natamycin 5% là cốt lõi chẩn đoán – điều trị.",
    "1461-ap-xe-duoi-mang-xuong-hoc-mat-o-tre":
        "Áp-xe dưới màng xương hốc mắt ở trẻ là ổ dịch hình thấu kính ngoài nón kèm nâng màng xương, thường lan từ viêm xoang sàng.",
    "1462-sinh-trac-iol-sau-ghep-giac-mac":
        "Giác mạc sau ghép làm sai cả công suất K lẫn vị trí hiệu dụng IOL, nên phải tính bằng công thức hai mặt phẳng hoặc ray tracing.",
    "1463-suy-thuong-than-do-corticoid":
        "Suy thượng thận thứ phát do corticoid kéo dài để lại tuyến thượng thận teo đối xứng, aldosteron vẫn bình thường; phải giảm liều theo lịch.",
    "1465-tang-nhan-ap-sau-tiem-noi-nhan":
        "Tăng nhãn áp cấp sau tiêm nội nhãn đạt đỉnh trong 30 giây và về bình thường trong 30 phút; chỉ chọc tiền phòng khi không tự hạ.",
    "1466-phu-bach-huyet-bam-sinh-o-tre":
        "Phù bạch huyết bẩm sinh ở trẻ (Milroy–Meige) là phù mềm không ấn lõm do ứ dịch giàu protein, lâu dần dày và xơ hóa mô dưới da.",
    "1467-mang-truoc-vong-mac-erm":
        "ERM là màng tăng phản xạ trên bề mặt võng mạc kèm co kéo; đọc theo 4 giai đoạn Govetto trên OCT để quyết định bóc màng.",
    "1469-bong-vong-mac-co-lo-sau-tiem-noi-nhan":
        "Bong võng mạc có lỗ sau tiêm nội nhãn xảy ra vì đường kim 30 G xuyên qua pars plana vào vùng ora serrata, kèm lỗ ngoại vi ± PVR.",
    "1472-viem-giac-mac-acanthamoeba":
        "Viêm giác mạc do Acanthamoeba gây đau nhiều hơn tổn thương, viêm thần kinh tỏa tia và nang vách đôi trên IVCM, gần như chỉ ở người đeo kính tiếp xúc.",
    "1473-viem-xoang-nam-xam-lan-cap-hoc-mat":
        "Viêm xoang nấm xâm lấn cấp lan hốc mắt gây đặc xoang, hủy xương, hoại tử ít ngấm thuốc do nấm xâm lấn mạch — khác viêm xoang vi khuẩn.",
    "1608-ung-thu-nieu-mac-thu-phat-sau-xa-tri-tieu-khung":
        "Ung thư niệu mạc thứ phát sau xạ trị tiểu khung cho dày thành bàng quang hoặc khối trong lòng, nguy cơ cao gấp khoảng 2,5 lần.",
    "1612-colpocleisis-va-bien-chung":
        "Colpocleisis bịt kín âm đạo nên hình ảnh hậu phẫu dễ nhầm; biến chứng cần nghĩ là ứ mủ trong khoang mổ (pyocolpos/pyometra).",
    "1616-ung-thu-vu-the-viem":
        "Ung thư vú thể viêm là đỏ da, phù và da cam trên ≥ 1/3 vú dưới 6 tháng, do tế bào u bít bạch mạch trung bì — không phải viêm.",
    "1618-di-can-da-thanh-nguc-ung-thu-vu":
        "Di căn da và thành ngực của ung thư vú là dày da khu trú hoặc lan tỏa kèm nốt dưới da, khác hẳn xâm lấn da trực tiếp T4b.",
    "1627-nguoi-mang-opa1-khong-trieu-chung":
        "Người mang OPA1 có thể không triệu chứng vì độ thấm không hoàn toàn: mất tế bào hạch tiến triển âm thầm nên vẫn phải theo dõi OCT.",
    "1631-thai-tiep-tuc-sau-chua-seo-mo-lay-thai":
        "Thai tiếp tục sau chửa ở sẹo mổ lấy thai có thể tiến triển thành thai sống và nhau cài răng lược, nên phải theo dõi RMT và khuyết sẹo.",
    "1633-viem-bang-quang-xa-chay-mau-nang":
        "Viêm bàng quang xạ chảy máu nặng cho thành bàng quang dày lan tỏa và bàng quang co nhỏ; cầm máu theo bậc thang, nút mạch rồi cắt bàng quang.",
    "1639-dau-xuong-di-can-xa-tri-giam-dau":
        "Đau do di căn xương chọn 8 Gy × 1 hay chia liều, SBRT, đồng vị phóng xạ hay tạo hình đốt sống tùy cơ chế đau và tiên lượng.",
    "1641-opmd-opdm-va-cpeo":
        "OPMD/OPDM khác CPEO ở kiểu yếu cơ: OPMD yếu ưu thế gốc chi và nuốt khó, còn OPDM yếu ngọn chi; MRI cơ và DWI sọ giúp phân biệt.",
    "1642-sa-tang-chau-tai-phat-sau-colpocleisis":
        "Sa tạng chậu tái phát sau colpocleisis do ba cơ chế riêng; MRI động học giúp xác định kiểu sa và chọn cách mổ lại.",
    "1643-glaucoma-sau-mo-duc-thuy-tinh-the-bam-sinh":
        "Glaucoma sau mổ đục thể thủy tinh bẩm sinh xuất hiện muộn nhiều năm, góc mở, kèm lõm đĩa thị tiến triển và nhãn cầu dài ra.",
    "1648-di-can-gan-ung-thu-vu":
        "Di căn gan ở ung thư vú là nốt giảm tỷ trọng nhiều ổ, bờ không đều, ngấm viền; phải phân biệt u máu, gan nhiễm mỡ do điều trị và gan giả xơ.",
    "1649-di-can-buong-trung-ung-thu-vu":
        "Di căn buồng trứng của ung thư vú là khối phần phụ đặc thường hai bên kèm dịch ổ bụng và bánh mỡ phúc mạc, hay gặp ở nhóm ER dương.",
    "1650-gay-xuong-suon-xuong-don-sau-xa-tri":
        "Gãy xương sườn và xương đòn sau xạ trị là gãy thiếu vững kiểu giả u, do xương mất mạch, mất tế bào tạo xương và xơ hóa tủy.",
    "1660-stent-nieu-quan-luu-quen":
        "Stent niệu quản lưu quên bị kết vôi thành vật cản quang dạng ống, gặp ở 0,9–12% người đặt stent và gây nhiễm trùng, suy thận.",
    "1662-doc-tinh-asparaginase-trong-enktl":
        "Asparaginase trong ENKTL gây viêm tụy hoại tử và huyết khối do thiếu antithrombin/fibrinogen; MRV–CTV là chuỗi xung chốt để phát hiện.",
    "1666-hep-nieu-quan-sau-va-ro-va-sau-xa-tri":
        "Hẹp niệu quản sau vá rò và sau xạ trị do sợi xơ thay cơ trơn, gây ứ nước – ứ niệu quản; thể do xạ hay gặp ở đoạn xa.",
    "1669-hoi-chung-qua-kich-buong-trung":
        "Hội chứng quá kích buồng trứng cho buồng trứng đa nang hai bên và cổ trướng do VEGF làm tăng tính thấm mao mạch.",
    "1675-vo-kinh-trung-uong-mri-tuyen-yen":
        "Vô kinh trung ương trên MRI tuyến yên: mất xung GnRH làm LH/FSH và estradiol thấp, có thể do u hố yên hoặc tuyến yên trông bình thường.",
    "1676-bon-ommaya-vi-tri-catheter":
        "Bồn Ommaya cần đầu catheter đúng vị trí não thất để bơm thuốc nội tủy và lấy dịch não tủy lặp lại; phải theo dõi nhiễm và tắc catheter.",
    "1680-viem-tuy-tang-triglyceride-nguoi-lon":
        "Viêm tụy cấp do tăng triglyceride ở người lớn nặng hơn viêm tụy mật (46,9% so với 17,6%), hình ảnh là hoại tử và ổ dịch quanh tụy.",
    "1684-nuot-kho-sau-xa-tri-dau-co":
        "Nuốt khó sau xạ trị đầu cổ là xơ hóa cơ nuốt tiến triển muộn, khác nuốt đau cấp do viêm niêm mạc trong lúc đang xạ.",
    "1688-siliconoma-lan-xa-ngoai-vu":
        "Siliconoma lan xa ngoài vùng vú cho khối mô mềm tăng hồi âm kiểu 'bão tuyết' và tín hiệu chọn lọc silicone trên MRI sau tiêm silicone lậu.",
    "1690-benh-paget-num-vu":
        "Bệnh Paget núm vú là trợt – đóng vảy MỘT BÊN ở núm, 93% có ung thư vú nằm dưới và chỉ dưới 10% sờ thấy khối.",
    "1692-u-tuyen-num-vu":
        "U tuyến núm vú gây trợt – loét một bên ± nốt và chảy dịch; tổn thương ≤ 10 mm sát da nên siêu âm đầu dò 12–18 MHz là chốt.",
    "1693-thrombophlebitis-migrans-trousseau":
        "Thrombophlebitis migrans (Trousseau) là dây cứng đỏ – đau tái phát di chuyển nhiều vị trí; siêu âm ép là chốt vì lòng mạch không xẹp.",
    "1695-ac225-dotatate-ppgl-sau-lu177":
        "²²⁵Ac-DOTATATE dùng sau thất bại ¹⁷⁷Lu ở PPGL: hạt alpha quãng chạy 47–85 µm, LET gấp hàng trăm lần beta; chọn bệnh nhân theo SSTR/FDG.",
    "1698-hoi-chung-tac-mach-silicone":
        "Hội chứng tắc mạch silicone sau tiêm mông gây viêm phổi, xuất huyết phế nang và ARDS trong 72 giờ, hình ảnh là kính mờ lan tỏa.",
    "1699-benh-cushing-tre-em":
        "Bệnh Cushing ở trẻ biểu hiện chậm tăng trưởng kèm tăng cân; chẩn đoán bằng xét nghiệm động học và BIPSS theo tuổi, MRI 3T tìm microadenoma.",
    "1700-cushing-chu-ky":
        "Cushing chu kỳ có cortisol dao động lúc cao lúc bình thường nên xét nghiệm âm giả; phải lấy mẫu lặp thay vì 'chụp đúng lúc trũng'.",
    "1703-dinh-khop-thai-duong-ham-bam-sinh":
        "Dính khớp thái dương–hàm bẩm sinh ở trẻ gây hạn chế mở miệng cố định; CT thấy cầu xương lồi cầu–ổ chảo, phân độ Sawhney/He định hướng mổ.",
    "1704-vtg-man-cholesteatoma-tre-cay-oc-tai":
        "Cholesteatoma ở trẻ có cấy ốc tai là khối mô mềm tiêu xương vùng thượng nhĩ ± hạn chế khuếch tán; phải xử lý tai trước khi đặt điện cực.",
    "1705-theo-doi-tiet-nieu-dai-tien-sau-cat-u-quai-cung-cut":
        "Sau cắt u quái cùng cụt phải theo dõi tiết niệu – đại tiện: bàng quang thần kinh, tồn lưu cao, trào ngược, tủy bám thấp và bón.",
    "1706-tui-thua-bang-quang-o-tre":
        "Túi thừa bàng quang ở trẻ là túi cùng lòng bàng quang lồi ra ngoài thành, chỉ đầy rõ ở thì đi tiểu; phải phân biệt túi thừa thật với giả.",
    "1707-trat-khop-thai-duong-ham-o-tre":
        "Trật khớp thái dương–hàm ở trẻ có lồi cầu ra TRƯỚC ụ khớp và ổ chảo trống; bán trật tự về, còn trật thật phải nắn.",
    "1708-gay-loi-cau-xuong-ham-duoi-o-tre":
        "Gãy lồi cầu xương hàm dưới ở trẻ do lực gián tiếp qua cằm, chiếm 25–45% gãy xương hàm; đọc mất chiều cao cành lên và góc di lệch.",
    "1710-dai-thao-nhat-trung-uong-sau-mo-tuyen-yen":
        "Đái tháo nhạt trung ương sau mổ tuyến yên diễn tiến ba pha; mất điểm sáng thùy sau trên T1 là mất kho hạt dự trữ, không phải mất mô.",
    "1712-trousseau-dong-mach-nbte":
        "Trousseau thể động mạch gây nhồi máu não nhiều ổ nhiều lãnh thổ và vegetate vô khuẩn trên van tim; cấy máu âm không loại trừ.",
    "1713-cholesteatoma-xuong-da-o-tre":
        "Cholesteatoma xương đá ở trẻ gây 'liệt mặt Bell' không phải Bell, với khối mô mềm tiêu xương đỉnh xương đá; DWI không-EPI và phân độ Sanna định hướng.",
    "1714-chay-dich-num-mot-ong":
        "Chảy dịch núm tự nhiên MỘT ỐNG là tổn thương khu trú trong một nhánh ống, nên soi và chụp ống dẫn đi theo được còn siêu âm dễ bỏ sót.",
    "1715-ro-dich-nao-tuy-sau-mo-xuyen-me-dao":
        "Rò dịch não tủy sau mổ xuyên mê đạo: T2 3D lát mỏng 0,5–1 mm thấy dải dịch liên tục từ ống tai trong ra vòi nhĩ, hoặc pseudomeningocele dưới da.",
    "1716-gay-phuc-hop-go-ma-ham-tren-o-tre":
        "Gãy phức hợp gò má–hàm trên ở trẻ đọc theo bốn trụ đỡ và phân độ Zingg, dựa vào mất lồi gò má và ngưỡng di lệch để chỉ định mổ.",
    "1717-vo-tu-cung-tren-seo-mo-lay-thai":
        "Vỡ tử cung trên sẹo mổ lấy thai là mất liên tục thành tử cung kèm dịch ổ bụng cấp; TOLAC có nguy cơ 0,3–0,7%, cần đọc dấu tiền triệu.",
    "1718-gay-xuong-cung-sau-xa-tri":
        "Gãy xương cùng do thiếu xương sau xạ trị tiểu khung cho dải phù tủy và đường gãy song song khớp cùng chậu, phải phân biệt với di căn xương.",
    "1719-bang-quang-doi-va-nang-nieu-ron":
        "Bàng quang đôi, vách bàng quang và nang niệu rốn ở trẻ cùng nguồn gốc phôi thai, có thể kèm chia đôi trực tràng, âm đạo, tử cung, cột sống.",
    "1722-ha-natri-muon-sau-mo-tuyen-yen":
        "Hạ natri máu muộn sau mổ tuyến yên do SIADH thoáng qua: Na < 135 xuất hiện sau ngày 3, đáy ngày 5–10, lúc bệnh nhân đã ra viện.",
    "1725-vo-oi-non-thang-truoc-24-tuan-tren-seo-mo-lay-thai":
        "Vỡ ối non tháng trước 24 tuần trên sẹo mổ lấy thai nặng hơn vì sẹo mỏng, nguy cơ nhiễm và nhau bám sẹo cao; phải đo độ dày sẹo.",
    "1728-chay-mau-sau-vo-tu-cung":
        "Chảy máu sau vỡ tử cung đến từ ba nguồn cùng lúc; xử trí theo bậc: khâu bảo tồn, bóng chèn, thuyên tắc động mạch tử cung rồi mới cắt tử cung.",
    "1729-suy-tuy-xa-tri-hat-alpha-225ac":
        "Suy tủy do ²²⁵Ac-PSMA phân độ theo CTCAE với liều tủy quy đổi RBE = 5; hạt alpha quãng chạy 50–100 µm nên tổn thương tủy không đồng nhất.",
    "1730-hoi-chung-ong-tuy-dut":
        "Hội chứng ống tụy đứt sau hoại tử tụy là mất liên tục ống tụy chính ≥ 2 cm kèm ổ dịch dai dẳng vì đuôi tụy vẫn còn tiết dịch.",
    "1731-u-mam-noi-so-vung-tren-yen-o-tre":
        "U mầm nội sọ vùng trên yên ở trẻ là khối đường giữa ngấm mạnh, hạn chế khuếch tán, mất điểm sáng T1 thùy sau; u tinh bào có vôi hóa.",
    "1732-doc-gan-cdk46-tdxd":
        "Thuốc ức chế CDK4/6 và T-DXd gây tổn thương gan lan tỏa (giảm đậm độ, tụt tín hiệu) kèm tăng enzym gan, không phải khối di căn.",
    "1733-not-tai-tao-fnh-like-sau-hoa-tri":
        "Nốt FNH-like sau hóa trị (oxaliplatin, cyclophosphamide) là nốt mới ngấm mạnh thì động mạch và tăng tín hiệu thì gan mật — 'di căn giả'.",
    "1736-co-truong-tuy-ro-tuy-noi-bo":
        "Cổ trướng tụy là dịch báng giàu amylase do ống tụy vỡ thành trước; vỡ thành sau cho tràn dịch màng phổi, gọi chung là rò tụy nội bộ.",
    "1737-ro-tuy-mang-phoi":
        "Rò tụy–màng phổi gây tràn dịch màng phổi tái phát giàu amylase, thường bên trái, với đường rò ống tụy xuyên hoành thấy trên MRCP.",
    "1738-ngo-doc-co-khoi-lua-o-tre":
        "Ngộ độc CO ở trẻ cho tổn thương đối xứng nhân bèo ± chất trắng, hạn chế khuếch tán; COHb không đo được độ nặng của bệnh.",
    "1740-thoat-vi-amyand-o-tre":
        "Thoát vị Amyand ở trẻ chứa ruột thừa trong túi thoát vị bẹn, hình ảnh là cấu trúc hình ống cụt không đè xẹp; quyết định cắt ruột thừa và đặt lưới.",
    "1741-kallmann-thieu-san-hanh-khuu-giac":
        "Hội chứng Kallmann: thiểu sản hoặc không có hành khứu giác trên MRI kèm dậy thì muộn, vì tế bào GnRH không di trú được tới hạ đồi.",
    "1742-xoan-buong-trung-ohss":
        "Xoắn buồng trứng trên buồng trứng quá kích: buồng trứng to nhất chưa chắc đã xoắn và Doppler còn dòng không loại trừ.",
    "1743-huyet-khoi-xoang-ohss":
        "Huyết khối xoang tĩnh mạch não và tĩnh mạch cảnh trong ở OHSS gây đau đầu mới sau kích thích rụng trứng; CTV–MRV thấy mất dòng.",
    "1750-utuc-than-ghep":
        "UTUC ở thận ghép là khuyết lòng bể thận ghép hoặc khối giả viêm, kẻ bắt chước viêm thận – bể thận ở người suy giảm miễn dịch.",
    "1751-lch-vung-duoi-doi-tuyen-yen-o-tre":
        "Bệnh mô bào Langerhans vùng dưới đồi–tuyến yên ở trẻ cho cuống yên dày, mất điểm sáng T1 thùy sau và khối dưới đồi ngấm thuốc.",
    "1752-suy-tuyen-yen-sau-xa-tri-so-o-tre":
        "Suy tuyến yên sau xạ trị sọ ở trẻ là thiếu hụt hormone tiến triển theo liều xạ và thời gian, trong đó GH thường mất trước.",
    "1753-viem-tuyen-yen-cuong-yen-tang-sinh-lympho-o-tre":
        "Viêm tuyến yên–cuống yên tăng sinh lympho ở trẻ cho cuống yên dày nhẵn đối xứng, mất điểm sáng T1 thùy sau, ngấm mạnh và tự thu nhỏ.",
    "1754-hoi-chung-duoi-doi-o-tre":
        "Hội chứng dưới đồi ở trẻ sau u, mổ hoặc xạ gây béo phì tăng nhanh, mất khát, rối loạn điều nhiệt và giấc ngủ — không chỉ thiếu hormone tuyến yên.",
    "1755-csws":
        "Hạ natri máu sau mổ u vùng trên yên ở trẻ phải phân biệt SIADH với hội chứng mất muối não, vì hướng xử trí truyền dịch ngược nhau.",
    "1756-hoi-chung-gian-nao":
        "Hội chứng gian não ở nhũ nhi là gầy teo mỡ dưới da dù ăn đủ, tăng động, kèm u đường thị–dưới đồi; chẩn đoán muộn trung bình 11 tháng.",
    "1757-ha-natri-mau-muon-sau-xuat-vien":
        "Hạ natri máu muộn sau xuất viện ở trẻ mổ vùng trên yên có đáy Na rơi vào ngày 5–7, tức sau khi bệnh nhi đã ra viện.",
    "1758-glioma-duong-thi-nf1":
        "U thần kinh đệm đường thị gặp ở 15–30% trẻ NF1, là dày và tăng tín hiệu đường thị; theo dõi bằng MRI kết hợp thị lực, dùng MEK inhibitor khi tiến triển.",
    "1761-trismus-sau-xa-tri-dau-co":
        "Trismus sau xạ trị đầu cổ là xơ hóa – teo cơ nhai một bên do nguyên bào cơ tăng tổng hợp collagen, với ngưỡng mở miệng ≤ 35 mm.",
    "1762-hoi-chung-ruot-ngan-nguoi-lon":
        "Hội chứng ruột ngắn ở người lớn là ruột non còn lại dưới 200 cm sau cắt đoạn rộng; hình ảnh là mất đoạn ruột non và giãn tá tràng bù trừ.",
    "1764-v3-sau-xa-tri-dau-co":
        "Bệnh thần kinh sinh ba V3 sau xạ trị đầu cổ gây dị cảm – đau thần kinh và teo cơ nhai đơn thuần không có khối, phải phân biệt với tái phát u.",
    "1765-ha-thiet-sau-xa-tri-dau-co":
        "Bệnh thần kinh hạ thiệt XII sau xạ trị đầu cổ gây teo nửa lưỡi và lệch lưỡi về bên liệt nhiều năm sau xạ, không có khối.",
    "1766-first-bite-syndrome":
        "Hội chứng đau khi cắn miếng đầu tiên là đau co thắt tuyến mang tai một bên ngay miếng đầu rồi giảm khi nhai tiếp, hình ảnh không có khối.",
    "1768-co-dong-cung-sau-xa-duong-tho-kho":
        "Cổ đông cứng sau xạ trị gây hạn chế mở miệng và biến dạng thanh môn; siêu âm đàn hồi cho thấy mô cứng hơn hẳn người không xạ.",
    "1769-co-dong-cung-sau-xa-duong-tho-kho":
        "Mở khí quản và front-of-neck access trên cổ đã xạ là vùng nguy hiểm vì da dày, mất lớp mỡ và collagen xơ hóa, nên phải chuẩn bị đường thở trước.",
    "1770-tac-tinh-mach-canh-trong-hai-ben-sau-xa":
        "Tắc tĩnh mạch cảnh trong hai bên sau xạ là bệnh của não hơn của cổ, vì ở tư thế nằm đây là đường dẫn lưu chính, hệ quanh sống chỉ là đường phụ.",
    "1771-clabsi-catheter-trung-tam-o-tre":
        "Nhiễm khuẩn huyết liên quan catheter trung tâm ở trẻ: cấy máu đôi với hiệu số thời gian mọc ≥ 120 phút chốt nguồn, vị trí đầu catheter quyết định rút hay giữ.",
    "1773-boc-tach-dong-mach-canh-co":
        "Bóc tách động mạch cảnh cổ có hai lòng thật–giả và vạt nội mạc; siêu âm Doppler không đủ chốt cơ chế nên cần HRMRI.",
    "1774-benh-co-corticoid-va-icu":
        "Bệnh cơ do corticoid và bệnh cơ bệnh nặng ở ICU: thể mạn teo cơ thay mỡ không phù, thể cấp phù cơ lan tỏa đối xứng.",
    "1775-boc-tach-dong-mach-dot-song":
        "Bóc tách động mạch đốt sống cho huyết khối thành mạch hình liềm và hẹp vót nhọn; T1 fat-sat thấy tăng tín hiệu trong thành là dấu chốt.",
    "1776-benh-co-hoanh-do-tho-may":
        "Bệnh cơ hoành do thở máy gây teo cơ và giảm phân suất dày, đo trên siêu âm vùng áp thành — cơ hoành là cơ 'dùng hoặc mất'.",
    "1777-ro-dich-nao-tuy-nen-so-truoc-tu-phat":
        "Rò dịch não tủy nền sọ trước 'ẩn' cần CT cisternography lúc đang rò mới thấy thuốc thoát ra; âm tính khi không chảy là âm tính giả.",
    "1778-chan-thuong-phoi-song-no-tre":
        "Chấn thương phổi do sóng nổ ở trẻ cho đông đặc hoặc kính mờ hai bên không theo phân thùy, X-quang có thể bình thường trong 24 giờ đầu.",
    "1781-huyet-khoi-tinh-mach-nao-tre-thieu-mau-huyet-tan":
        "Huyết khối tĩnh mạch não ở trẻ thiếu máu do tam chứng Virchow đảo chiều: lưu lượng tăng gây chảy rối, hồng cầu giảm khả năng biến dạng.",
    "1783-huyet-khoi-xoang-sau-chan-thuong-dau-tre":
        "Huyết khối xoang sau chấn thương đầu ở trẻ: tăng đậm độ trong xoang trên CT không cản quang và mất dòng trên CTV–MRV, kèm vỡ sọ hoặc máu tụ đè xoang.",
    "1784-hoi-chung-tuoi-mau-qua-muc-sau-tai-thong-moyamoya":
        "Hội chứng tưới máu quá mức sau tái thông moyamoya là triệu chứng thần kinh mới kèm tăng tưới máu khu trú trên ASL/CTP, không do nhồi máu hay xuất huyết.",
    "1786-di-dang-tinh-mach-galen-so-sinh":
        "Dị dạng túi phình tĩnh mạch Galen ở sơ sinh là túi tĩnh mạch giãn lớn giữa đường giữa do shunt động–tĩnh mạch tốc độ cao, gây suy tim lưu lượng cao.",
    "1787-avm-nao-tre-da-vo":
        "AVM não ở trẻ đã vỡ: xuất huyết nhu mô kèm búi mạch có động mạch nuôi và tĩnh mạch dẫn lưu sớm, phân tầng từ CT/CTA đến DSA.",
    "1789-viem-phoi-do-cmv-o-nguoi-ghep-tang":
        "Viêm phổi do CMV ở người ghép tạng cho kính mờ, nốt nhỏ ± đông đặc, do virus nhiễm tế bào nội mô mao mạch và đại thực bào phế nang.",
    "1792-lach-to-giam-tieu-cau-do-oxaliplatin":
        "Lách to kèm giảm tiểu cầu do oxaliplatin là 'áp kế' của hệ cửa: thuốc gây tổn thương nội mô xoang gan dẫn tới tăng áp cửa.",
    "1793-fnh-like-o-tre-sau-hoa-tri-ghep-te-bao-goc":
        "Nốt FNH-like ở trẻ sau hóa trị hoặc ghép tế bào gốc là nốt gan mới ngấm mạnh thì động mạch — 'di căn giả' của người sống sót ung thư nhi.",
    "1794-soc-doc-to-bang-ve-sinh-o-tre":
        "Sốc độc tố do băng vệ sinh ở trẻ vị thành niên chẩn đoán bằng lâm sàng với ban đỏ lan tỏa; hình ảnh chỉ để tìm ổ và loại bắt chước.",
    "1796-chylomicronemia-trong-thai-ky-va-tu-van-sinh-san":
        "Chylomicronemia trong thai kỳ do estrogen ức chế lipoprotein lipase tới 85% và gan tăng VLDL, nên triglyceride tăng gấp ~2,5 lần và dễ viêm tụy cấp.",
    "1797-vi-chay-mau-hang-mach-sau-xa":
        "Vi chảy máu và hang mạch do xạ trị sọ ở trẻ là đốm mất tín hiệu trên SWI/T2* và hang mạch có vòng hemosiderin, phải phân biệt với tái phát u.",
    "1798-phan-do-bang-he-quanh-nao-that-funaki-va-gian-dong-mach-mang-mach-truoc":
        "Phân độ Funaki đọc mạng bàng hệ quanh não thất và giãn động mạch màng mạch trước trên MRA/DSA để định nguy cơ xuất huyết và chỉ định tái thông.",
    "1800-tac-mach-mo-sau-hut-mo-va-ghep-mo":
        "Tắc mạch mỡ gây kính mờ lan tỏa và nhiều nốt hạn chế khuếch tán rải rác kiểu 'bầu trời sao'; CTPA làm mỡ gần đồng đậm với máu nên dễ bỏ.",
    "1801-benh-gan-do-thuyen-tac-phong-xa-reild":
        "REILD sau TARE Y-90 gây cổ trướng và vàng da 4–8 tuần kèm teo gan do tắc xoang gan, phải phân biệt với tiến triển u.",
    "1802-theo-doi-dai-han-sau-pphn":
        "Theo dõi dài hạn sau PPHN phải tìm tăng áp phổi tái phát, chậm phát triển thần kinh và nghe kém, vì bốn trục tổn thương cùng tồn tại.",
    "1804-suy-giap-tieu-thu-do-u-mach-mau-ngoai-gan":
        "Suy giáp tiêu thụ do D3 lạc vị cho TSH cao kháng levothyroxine và rT3 cao, có thể KHÔNG có khối gan vì hoạt tính phụ thuộc khối u chứ không vị trí.",
    "1806-viem-phoi-do-xa-sau-tare":
        "Viêm phổi do xạ sau TARE cho kính mờ quanh rốn phổi và chừa màng phổi, vì hạt mắc ở mạch lớn và tia β chỉ đi 2,5 mm.",
    "1807-boc-tach-dmc-bung-do-chan-thuong-va-sau-thu-thuat":
        "Bóc tách động mạch chủ bụng do chấn thương hoặc sau thủ thuật để lại vạt nội mạc; hiếm nhưng tử vong tới 17–92% trong y văn.",
    "1808-sirolymus-di-dang-bach-huyet-theo-doi-ngung-thuoc":
        "Sirolimus trong dị dạng bạch huyết phức tạp cần theo dõi nồng độ đáy, độc tính và ngưỡng ngừng, vì thuốc ức chế mTORC1 làm giảm lymphangiogenesis.",
    "1811-loet-da-day-ta-trang-sau-tace-tare":
        "Loét và hẹp thực quản–dạ dày–tá tràng do trào ngược vi cầu không đích sau TACE/TARE: vị trí tổn thương chỉ ra nhánh động mạch tội phạm.",
    "1815-suy-giap-do-qua-tai-iod-so-sinh":
        "Suy giáp do quá tải iod ở sơ sinh do cản quang tồn lưu trong ruột gây hiệu ứng Wolff–Chaikoff; trẻ non tháng không 'thoát' ức chế trong 48 giờ.",
    "1818-soi-nieu-quan-thai":
        "Sỏi niệu quản ở thai phụ gây ứ nước, phải phân biệt ứ nước sinh lý; siêu âm – MRI định hướng và dẫn lưu tạm bằng JJ hoặc nephrostomy.",
    "1819-chay-mau-muon-gia-phinh-mach-tang":
        "Chảy máu tiêu hóa muộn do giả phình động mạch tạng: túi đầy đồng thời và cùng đậm độ động mạch chủ ở thì động mạch rồi rửa trôi song song.",
    "1823-trametinib-di-dang-bach-huyet-ras-mapk":
        "Trametinib trong dị dạng bạch huyết do đột biến RAS/MAPK phải chọn bệnh nhân theo gen và đọc đáp ứng trên DCMRL, không theo hình thái.",
    "1826-viem-phoi-do-thuoc-uc-che-mtor":
        "Viêm phổi do thuốc ức chế mTOR là kính mờ hai bên đối xứng ± đông đặc dải, do thuốc làm nội mô co lại và tăng tính thấm.",
    "1827-hep-tinh-mach-cua-sau-ghep-gan":
        "Hẹp tĩnh mạch cửa sau ghép gan là hẹp khu trú tại miệng nối; vì dòng áp lực thấp nên một vòng xơ vài mm đã đủ làm mất chênh áp.",
    "1828-voi-hoa-nao-sau-xa-tri-tre":
        "Vôi hóa não do xạ trị ở trẻ là vi mạch khoáng hóa: vôi hóa đối xứng dạng chấm hoặc gyriform, tăng đậm độ CT, tăng T1, giảm trên SWI.",
    "1834-hoi-chung-sau-nut-mach":
        "Hội chứng sau nút mạch là viêm vô khuẩn do hoại tử đông giải phóng cytokine; phải phân biệt với nhiễm trùng hoặc áp-xe, nhất là khi có khí trong tổn thương.",
    "1837-dau-silicone-tien-phong-ton-thuong-noi-mo":
        "Dầu silicone trong tiền phòng gây tổn thương nội mô giác mạc: giọt dầu bám nội mô, mất tế bào nội mô và bệnh giác mạc dải.",
    "1838-kho-mieng-do-225ac-psma":
        "Khô miệng do ²²⁵Ac-PSMA vì tuyến nước bọt biểu hiện PSMA sinh lý và là cơ quan giới hạn liều của xạ trị hạt alpha.",
    "1842-takotsubo-hau-phau-icu":
        "Bệnh cơ tim do stress ở ICU gây rối loạn vận động vùng thoáng qua và phù cơ tim; LGE thường vắng vì không có hoại tử lan rộng.",
    "1843-benh-re-dam-roi-than-kinh-do-xa":
        "Bệnh rễ và đám rối do xạ cho dày lan tỏa và tăng T2 đám rối trong trường xạ, ngấm mờ, kèm phù cơ do mất thần kinh, không có khối.",
    "1844-ro-hoai-tu-thuc-quan-do-xa":
        "Rò và hoại tử thực quản do xạ: u teo nhanh hơn mô lành kịp sửa nên vùng u cũ thành chỗ yếu nhất, cản quang thoát ra ngoài lòng và khí trung thất.",
    "1845-bang-quang-than-kinh-tre":
        "Bàng quang thần kinh ở trẻ dị tật tủy cho bàng quang thành dày hình 'cây thông' kèm trào ngược; DLPP và compliance quyết định bậc thang bảo vệ thận.",
    "1847-hep-ruot-thieu-mau-sau-nut-mach":
        "Hẹp ruột do thiếu máu sau nút mạch mạc treo là hẹp chu vi đơn độc xuất hiện vài tuần sau thiếu máu, tổn thương xơ chứ không phải viêm.",
    "1848-nut-mach-lach-trong-chan-thuong":
        "Nút mạch lách trong chấn thương chọn gần hay xa theo kiểu tổn thương mạch trong nhu mô: thoát mạch hoạt động, giả phình hay rò.",
    "1849-liet-co-hoanh-mot-ben-sau-mo-tim-nguc":
        "Liệt cơ hoành một bên sau mổ tim/ngực cho nâng cao nửa hoành và vận động nghịch thường trên M-mode; hướng đi là dấu chốt, không phải độ dày.",
    "1850-sieu-am-co-hoanh-cai-may-tre-so-sinh":
        "Siêu âm cơ hoành dự báo cai máy ở sơ sinh qua biên độ và phân suất dày, vì cơ hoành trẻ làm việc gần ngưỡng mỏi.",
    "1851-hep-thuc-quan-lanh-tinh-sau-xa":
        "Hẹp thực quản lành tính sau xạ là hẹp lòng nhẵn, đối xứng, đoạn dài, không có khối niêm mạc, do viêm nội mạc tắc nghẽn tiến triển.",
    "1852-ro-dong-mach-chu-thuc-quan":
        "Rò động mạch chủ–thực quản là thông trực tiếp giữa ĐMC và lòng thực quản, kèm giả phình hoặc loét xuyên thành và mất mặt phẳng mỡ quanh thực quản.",
    "1857-tran-duong-trap-mang-phoi-sau-mo-cot-song":
        "Tràn dưỡng trấp màng phổi sau mổ cột sống ngực–thắt lưng xuất hiện muộn, thường sau khi ăn lại mỡ chuỗi dài làm lưu lượng dưỡng trấp tăng.",
    "1860-chan-thuong-lach-tre-em":
        "Chấn thương lách ở trẻ gây tụ máu, đường rách và tổn thương mạch; lồng ngực trẻ đàn hồi nên có thể vỡ lách nặng với X-quang ngực bình thường.",
    "1861-hep-dong-mach-gan-ghep-gan":
        "Hẹp động mạch gan sau ghép gan là 'bệnh của đường mật' vì đường mật chỉ sống bằng đám rối quanh ống mật nuôi bởi động mạch gan.",
    "1862-hoi-chung-nelson-sau-cat-thuong-than":
        "Hội chứng Nelson: sau cắt thượng thận hai bên cortisol xuống nhưng ACTH và u yên vẫn lớn dần, kèm sạm da; đọc MRI theo mốc và chặn bằng thuốc.",
    "1863-duc-the-thuy-tinh-mat-bom-dau-silicone":
        "Đục thể thủy tinh ở mắt bơm dầu gây lệch khúc xạ viễn thị khi còn dầu và cận thị sau lấy dầu, nên phải chọn mổ một thì hay hai thì.",
    "1864-dau-silicone-nang-bien-chung-phia-duoi":
        "Dầu silicone nặng có tỷ trọng > 1 nên đọng ở phía DƯỚI: lớp dầu ở đáy tiền phòng, giọt dưới võng mạc và bít bè phía dưới gây tăng nhãn áp.",
    "1865-bong-vong-mac-tai-phat-sau-thao-dau":
        "Bong võng mạc tái phát sau tháo dầu gặp ở 14,9% mắt, 75% do PVR; bờ bong ngang theo trọng lực là mẫu hình đọc trên ảnh góc rộng.",
    "1866-hoi-chung-huy-myelin-tham-thau-ods":
        "Hội chứng hủy myelin thẩm thấu sau sửa natri nhanh cho T2/FLAIR tăng hình trident ở trung tâm cầu và hạn chế khuếch tán sớm.",
    "1867-tao-bon-sau-keo-truc-trang":
        "Táo bón và ứ phân sau kéo trực tràng ở trẻ do cơ thắt hậu môn trong luôn vô hạch ở Hirschsprung, cộng thêm hẹp miệng nối hoặc cuff còn lại.",
    "1868-dong-kinh-sau-xuat-huyet-nhoi-mau-nao":
        "Động kinh sau xuất huyết hoặc nhồi máu não: cơn trong 7 ngày là cơn triệu chứng cấp, còn cơn muộn không kích thích mới là động kinh sau đột quỵ.",
    "1869-vo-thuc-quan-tu-phat":
        "Vỡ thực quản tự phát (Boerhaave) cho khí trung thất và tràn dịch – tràn khí màng phổi sau nôn dữ dội, vì áp lực lòng vọt lên ~200 mmHg.",
    "1873-bao-sau-duc-thu-phat-mat-bom-dau-yag":
        "Bao sau đục sau phaco trên mắt bơm dầu tiến triển nhanh hơn; phải cân nhắc Nd:YAG khi còn dầu vì dầu có thể sang tiền phòng sau khi mở bao.",
    "1874-ha-calci-mau-sau-cat-tuyen-giap":
        "Hạ calci máu sau cắt tuyến giáp: đọc calci hiệu chỉnh và PTH 1–6 giờ, QT dài, không có tổn thương khu trú trên hình ảnh, và tiêu chuẩn xuất viện.",
    "1875-phu-hoang-diem-dang-nang-mat-bom-dau":
        "Phù hoàng điểm dạng nang sau phacovitrectomy trên mắt bơm dầu là nang giảm hồi âm ở INL, tăng CST; phải phân biệt khoang giả do dầu trong võng mạc.",
    "1877-pfcl-ton-luu-duoi-vong-mac":
        "PFCL tồn lưu dưới võng mạc là giọt tăng phản xạ kèm bóng che trên OCT, tạo dấu Ω khi nằm dưới hoàng điểm và có thể phải lấy bằng kim 41 G.",
    "1880-suy-can-giap-vinh-vien-sau-cat-giap":
        "Suy cận giáp vĩnh viễn sau cắt giáp gây hạ calci máu mạn và vôi hóa lạc chỗ ở thận, não, mắt; phải quản lý calci niệu và PTH thay thế suốt đời.",
    "1881-tran-duong-trap-mang-phoi-chan-thuong-kin":
        "Tràn dưỡng trấp màng phổi sau chấn thương ngực kín chẩn đoán khi triglyceride dịch ≥ 110 mg/dL; bên tràn phụ thuộc vị trí tổn thương ống ngực.",
    "1882-phu-hoang-diem-prostaglandin-sau-phaco":
        "Phù hoàng điểm do prostaglandin sau phaco xảy ra ở mắt giả thủy tinh thể không viêm, bao sau nguyên vẹn; phải cân nhắc ngưỡng ngừng thuốc.",
    "1883-rach-bao-sau-phaco-mat-da-cat-dich-kinh":
        "Rách bao sau trong phaco trên mắt đã cắt dịch kính dễ xảy ra vì mất hỗ trợ màng hyaloid và tiền phòng dao động mạnh (LIDRS), kèm sa dịch kính.",
    "1885-viem-mang-ngoai-tim-co-that":
        "Viêm màng ngoài tim co thắt cho dày ± vôi hóa màng ngoài tim và rối loạn đổ đầy phụ thuộc hô hấp do phụ thuộc liên thất.",
    "1886-benh-co-tim-han-che-amyloid-tim":
        "Amyloid tim gây dày thất 'giả' do lắng protein ngoài tế bào, ngấm thuốc dưới nội tâm mạc lan tỏa và apical sparing trên xạ hình xương.",
    "1889-parsonage-turner-than-kinh-hoanh":
        "Parsonage–Turner tổn thương thần kinh hoành gây đau vai rồi yếu và nâng cao một nửa hoành; M-mode thấy nửa hoành đi lên khi hít vào.",
    "1892-theo-doi-sau-ods-hoi-chung-huy-myelin-tham-thau":
        "Theo dõi sau ODS: DWI/ADC đổi sớm nhất (giờ đầu – 48 giờ), T2/FLAIR sáng muộn 1–2 tuần và teo về sau, nên lịch chụp theo chuỗi mô bệnh.",
    "1894-thung-thanh-tu-do-phinh-gia":
        "Vỡ thành tự do thất trái sau nhồi máu xảy ra ngày 3–7 khi mô nhũn nhất, gây mất liên tục thành thất kèm dịch màng tim; phình giả là thể có lỗ thông.",
    "1905-bien-chung-va-an-toan-thu-thuat-pipac":
        "PIPAC là thủ thuật nội soi nhỏ có biến chứng riêng: không vào được ổ bụng vì dính, thủng ruột do trocar, rò thuốc và phơi nhiễm nghề nghiệp.",
    "1906-hep-dong-ra-tm-gan-sau-ghep-gan":
        "Hẹp dòng ra tĩnh mạch gan sau ghép cho gan ngấm thuốc không đồng nhất và mất sóng ba pha; phổ ba pha liên tục loại trừ, ngưỡng chênh áp 5 mmHg.",
    "1907-shunt-cua-chu-lon-khong-xo-gan":
        "Shunt cửa–chủ lớn không xơ gan (CEPS/Abernethy) gây teo nhu mô, nốt gan và tăng amoniac; phải đo áp lực tĩnh mạch cửa bằng bóng chẹn trước khi bít.",
    "1908-thieu-mau-mac-treo-va-boc-tach-dong-mach-tang":
        "Thiếu máu mạc treo cấp và mạn, bóc tách động mạch tạng tự phát: CTA 3 thì đánh giá hẹp–tắc, vách giả và mức thiếu tưới máu ruột để chọn can thiệp.",
    "1909-hep-tinh-mach-cua-sau-ghep-gan":
        "Hẹp tĩnh mạch cửa sau ghép gan là bệnh của dòng VÀO: tăng tốc tại chỗ hẹp, giãn đoạn trước hẹp; tỉ lệ vận tốc 3,21 xuống 1,01 sau nong bóng.",
    "1910-hoi-chung-tac-xoang-gan-sos":
        "Hội chứng tắc xoang gan cho gan to và ngấm thuốc 'da báo' lan tỏa kèm tăng áp cửa, không có chỗ hẹp khu trú; lưới giảm tín hiệu 50% trên HBP là nặng.",
    "1911-viem-dai-trang-thieu-mau":
        "Viêm đại tràng thiếu máu cho dày thành đại tràng từng đoạn, phù quanh đại tràng, dấu thumbprinting và mất ngấm thuốc thành ruột.",
    "1912-phinh-dong-mach-tang":
        "Phình động mạch tạng: thành mạch quan trọng hơn đường kính, vì phình thật do thoái hóa áo giữa lớn chậm còn giả phình dễ vỡ; đừng nhầm giả nang tụy.",
    "1913-hep-huyet-khoi-hep-dong-mach-gan-sau-ghep":
        "Hẹp và huyết khối động mạch gan sau ghép: mất tín hiệu màu, phổ tardus-parvus, PSV > 200 cm/s tại chỗ hẹp; RI 0,8 trong 3 ngày đầu là bất thường.",
    "1914-suy-chuc-nang-manh-ghep-som":
        "Suy chức năng mảnh ghép gan sớm chẩn đoán bằng tiêu chuẩn Olthoff (sinh hóa); CĐHA chỉ tìm nhồi máu, ứ mật và loại trừ hẹp–tắc mạch.",
    "1915-hep-dong-mach-gan-tre-sau-ghep":
        "Hẹp động mạch gan ở trẻ sau ghép gặp ở 1,2% (registry HEPATIC), 82,4% trong tháng đầu; phải chọn nong bóng lặp lại hay stent không lớn theo trẻ.",
    "1916-thai-ghep-cap-te-bao-sau-ghep-gan":
        "Thải ghép cấp tế bào sau ghép gan chẩn đoán bằng mô học Banff; siêu âm chỉ để loại trừ nguyên nhân cơ học, không chẩn đoán thải ghép.",
    "1917-thai-ghep-the-dich-sau-ghep-gan":
        "Thải ghép thể dịch sau ghép gan dựa vào DSA, C4d vi mạch và viêm/phì đại nội mạc vi mạch theo Banff 2016; hình ảnh chỉ để loại trừ.",
    "1919-phinh-dong-mach-chu-bung-nhiem-khuan":
        "Phình động mạch chủ bụng nhiễm khuẩn là túi phình dạng túi kèm viêm quanh ĐMC; mất liên tục vôi hóa khu trú là dấu hiệu chốt trên CTA.",
    "1920-tran-dich-mang-phoi-ac-tinh-catheter-hay-pleurodesis":
        "Tràn dịch màng phổi ác tính tái phát phải chọn catheter màng phổi lưu hay talc pleurodesis; phổi không nở là yếu tố quyết định lựa chọn.",
    "1921-nhiem-khuan-nieu-thai-ky":
        "Nhiễm khuẩn niệu ở thai phụ: cấy ≥ 10⁵, phải phân biệt ứ nước sinh lý với tắc nghẽn nhiễm trùng; thận to và vùng giảm ngấm hoặc thận dạng sọc là dấu hiệu.",
    "1923-ap-xe-than-quanh-than-thai":
        "Áp-xe thận và quanh thận ở thai phụ là ổ dịch có viền ngấm sau viêm thận–bể thận, có thể kèm khí; ngưỡng dẫn lưu tùy kích thước và đáp ứng.",
    "1926-viem-mang-oi-nhiem-khuan-oi":
        "Viêm màng ối – nhiễm khuẩn ối chẩn đoán bằng lâm sàng và dịch ối; hình ảnh chỉ hỗ trợ, với cổ tử cung ngắn và bùn ối là dấu hiệu nguy cơ.",
    "1927-that-dong-mach-tu-cung-va-dong-mach-chau-trong":
        "Thắt động mạch tử cung (O'Leary) và thắt động mạch chậu trong khi băng huyết sau sinh không cầm: mục tiêu là hạ áp lực chứ không đưa lưu lượng về 0.",
    "1929-viem-duong-mat-cap-thai-ky":
        "Viêm đường mật cấp ở thai phụ chẩn đoán theo TG18, phải dẫn lưu trong 6–24 giờ bằng ERCP với liều dưới 0,5 mGy.",
    "1930-soi-mat-khong-bien-chung-thai-ky":
        "Sỏi mật không biến chứng ở thai phụ: chỉ một phần chờ được sau sinh vì sludge 31% và tái phát 77%; SAGES 2024 còn để ngỏ quý III.",
    "1931-thai-ky-sau-nut-mach-tu-cung-uae":
        "Thai kỳ sau nút mạch tử cung cần tư vấn sinh sản và dự phòng băng huyết tái phát vì nguy cơ nhau cài răng lược cao hơn.",
    "1932-truyen-mau-khoi-luong-lon-bang-huyet-sau-sinh":
        "Truyền máu khối lượng lớn trong băng huyết sau sinh phải xử lý tứ giác tử vong: hạ thân nhiệt, toan, hạ calci và rối loạn đông máu.",
    "1933-viem-gan-adenovirus-sau-ghep-gan-o-tre":
        "Viêm gan do adenovirus sau ghép gan ở trẻ cho hoại tử không đặc hiệu, chỉ 33% có tổn thương khu trú nên không thể chẩn đoán bằng hình ảnh.",
    "1934-ro-tuy-phe-quan":
        "Rò tụy–phế quản gây viêm phổi tái phát cùng thùy, với nang giả tụy chứa khí xuyên hoành và đường rò vào phế quản.",
    "1935-duc-the-thuy-tinh-sau-migs":
        "Đục thể thủy tinh sau MIGS tiến triển ở nhân hoặc dưới bao sau, kèm tổn thương bao và zôn do dụng cụ; AS-OCT giúp quyết định phaco.",
    "1938-viem-tuy-cap-do-soi-thai-ky":
        "Viêm tụy cấp do sỏi ở thai phụ do sỏi kẹt tạm thời ở bóng Vater; ngưỡng lipase giúp không mổ oan, ERCP khi có tắc mật.",
    "1940-soi-mat-sot-tai-phat-sau-cat-tui-mat":
        "Sỏi sót, sỏi tái phát và sỏi rơi sau cắt túi mật là ba cơ chế khác nhau, cho ba bộ hình ảnh khác nhau trên MRCP.",
    "1945-viem-gan-tu-mien-de-novo-sau-ghep-gan-tre":
        "Viêm gan tự miễn de novo sau ghép gan ở trẻ là viêm khoảng cửa giàu tương bào có viêm gan giao diện; anti-GSTT1 dương ở 100% ca được xét nghiệm.",
    "1946-chen-ep-khoang-bung-acs":
        "Chèn ép khoang bụng: CT báo động trước khi kịp đo áp lực bàng quang, với bụng tròn, tĩnh mạch chủ dưới dẹt, cơ hoành cao và nhu mô ngấm kém.",
    "1947-co-that-dong-mach-gan-va-cuop-mau-lach-sau-ghep-gan":
        "Co thắt động mạch gan và hội chứng cướp máu lách sau ghép gan là hai nguyên nhân mất dòng có hồi phục, khác huyết khối.",
    "1952-ung-thu-tuyen-giap-lac-cho":
        "Ung thư tuyến giáp trong bướu giáp lạc chỗ là khối tăng đậm đường giữa đáy lưỡi, ngấm mạnh ± vôi hóa; quyết định theo dõi hay mổ kèm iod phóng xạ.",
    "1956-thuyen-tac-oi-anmion":
        "Thuyên tắc ối chẩn đoán bằng loại trừ: sụp tuần hoàn – hô hấp cấp trong chuyển dạ kèm DIC, hình ảnh chỉ để tìm nguyên nhân khác.",
    "1957-hoai-tu-vo-than-sau-bang-huyet":
        "Hoại tử vỏ thận sau băng huyết sau sinh cho vỏ không ngấm thuốc trong khi tủy vẫn ngấm, vì vỏ là đoạn cuối cây mạch không có bàng hệ.",
    "1959-tan-huyet-vi-mach-sau-sinh-hellp-ahus-ttp":
        "Tán huyết vi mạch sau sinh cần phân biệt HELLP, aHUS và TTP theo ba dấu hiệu bắt buộc; aHUS thường bị chẩn đoán quá tay.",
    "1960-sibo-sau-cat-ruot-ngan":
        "SIBO sau cắt ruột ngắn: điểm chuyển tiếp là chốt phân biệt giãn thích nghi lan tỏa với hẹp cơ học, và quyết định ai cần test hơi thở.",
    "1971-bat-san-giam-san-day-than-kinh-oc-tai":
        "Bất sản dây thần kinh ốc tai là khuyết cấu trúc trong ống tai trong trên T2 3D CISS–FIESTA, kèm hẹp lỗ ốc tai ≤ 1,2 mm.",
    "1982-tieu-chay-muoi-mat-sau-cat-hoi-trang":
        "Tiêu chảy muối mật sau cắt hồi tràng do mất bề mặt tái hấp thu ở hồi tràng tận; muối mật xuống đại tràng gây tiêu chảy nước.",
    "1983-duc-the-thuy-tinh-sau-trabeculectomy":
        "Đục thể thủy tinh sau trabeculectomy do tuổi và do phaco có thể làm hỏng bọng lọc, nên phải chọn đường mổ giữ bọng.",
    "1985-migs-glocom-goc-dong":
        "MIGS ở glôcôm góc đóng dựa vào cơ chế thể thủy tinh đẩy mống mắt ra trước; phaco ± goniosynechialysis mở góc và hạ nhãn áp.",
    "1986-viem-mo-hoai-tu-o-tre":
        "Viêm mô hoại tử ở trẻ phải mổ ngay không chờ hình ảnh khi có khí trong mô mềm và dày cân không ngấm thuốc.",
    "1987-dong-kinh-khong-co-giat-sau-dot-quy-tre":
        "Trạng thái động kinh không co giật sau đột quỵ ở trẻ biểu hiện bằng tri giác không hồi phục với phóng điện liên tục trên EEG.",
    "1988-choc-oi-song-thai":
        "Chọc ối và sinh thiết gai nhau ở song thai phải nhớ hai buồng ối có hai bộ gen, nên kết quả thai này không nói gì về thai kia.",
    "1989-choc-do-cuong-ron":
        "Chọc dò cuống rốn cho karyotype nhanh, chẩn đoán nhiễm trùng bào thai hoặc truyền máu thai; biến chứng và theo dõi sau thủ thuật là phần chính.",
    "3003-uc-che-diem-kiem-soat-u-nao-cmmrd":
        "Ức chế điểm kiểm soát ở u não CMMRD gây giả tiến triển và đáp ứng muộn, nên đọc MRI theo iRANO và chọn bệnh nhân theo gánh nặng đột biến.",
    "3004-hsct-cmmrd-dong-loai":
        "Ghép tế bào gốc đồng loài ở trẻ CMMRD thay 'nhà máy tạo máu' nhưng không thay được mô đích nên không chặn hết ung thư.",
    "3005-u-mau-duoi-thanh-mon-nhu-nhi":
        "U máu dưới thanh môn ở nhũ nhi gây rít hai thì tiến triển và có u máu vùng râu; CECT thấy khối ngấm mạnh dưới dây thanh, propranolol là đầu tay.",
    "3006-ruot-ngan-ifald-o-tre":
        "Ruột ngắn và bệnh gan do nuôi dưỡng tĩnh mạch ở trẻ: phải đọc bản đồ cắt ruột, theo ngưỡng bilirubin trực tiếp và đổi lipid khi ứ mật tiến triển.",
    "3007-etv-etv-cpc-o-tre":
        "ETV/ETV-CPC ở trẻ dựa vào MRI và điểm ETVSS; sau mổ dấu chốt là dòng chảy qua lỗ thông, không phải kích thước não thất.",
    "3008-trat-chuoi-xuong-con-sau-vo-xuong-thai-duong-o-tre":
        "Trật chuỗi xương con sau chấn thương xương thái dương ở trẻ hay gặp ở xương đe vì đây là mắt yếu; HRCT đọc từng khớp búa–đe–bàn đạp.",
    "3012-apxe-ngoai-mang-cung-sau-gay-te-ngoai-mang-cung":
        "Áp-xe ngoài màng cứng sau gây tê ngoài màng cứng có catheter làm cửa vào; khí ngoài màng cứng cũng có thể giả áp-xe trên MRI.",
    "3013-hoi-chung-duoi-ngua-sau-mo-cot-song":
        "Hội chứng đuôi ngựa sau mổ cột sống do máu tụ, phù, mủ hoặc đĩa tái phát; vì tổn thương thiếu máu–chèn ép nên thời gian quan trọng hơn mức độ.",
    "3015-hoi-chung-dau-sau-mo-cot-song":
        "Hội chứng đau sau mổ cột sống (FBSS/PSPS-2) do sẹo xơ, đĩa tái phát, tầng kế cận hoặc dụng cụ hỏng, nên phải đọc theo từng cơ chế.",
    "3016-ha-ap-luc-noi-so-tu-phat":
        "Hạ áp lực nội sọ tự phát là đau đầu thế đứng không có tiền sử chọc dò; MRI sọ định hướng, CT myelography động định vị rò, rồi blood patch hoặc mổ.",
    "3019-thuyen-tac-phoi-do-xi-mang-cement":
        "Thuyên tắc phổi do xi măng sau bơm đốt sống là dị vật cản quang dạng ống hoặc phân nhánh trong động mạch phổi, đậm độ khoảng 500 HU.",
    "3022-choc-do-tuy-song-khang-dong":
        "Chọc dò tủy sống ở người dùng kháng đông: khoang ngoài màng cứng thắt lưng có đám rối Batson thành mỏng nên dễ rỉ máu, và tổn thương ở ngực nguy hiểm hơn.",
    "3024-choc-do-tuy-song-quanh-tieu-soi-huyet-khoi":
        "Chọc dò tủy sống quanh tiêu sợi huyết: nghiệm pháp hồng cầu giảm dần mất giá trị, phải tìm xanthochromia bằng quang phổ kế trong cửa sổ 24 giờ.",
    "3025-dao-nguoc-khang-dong-xuat-huyet-noi-so":
        "Đảo ngược kháng đông trong xuất huyết nội sọ cấp nhắm vào lan rộng máu tụ 20–30% trong 3–6 giờ đầu; máu chưa đông có tỷ trọng thấp hơn trên CT.",
    "3026-tut-nao-nghich-ly-sau-choc-do-shunt-mo-so":
        "Chọc dò tủy sống ở người có shunt hoặc sau mở sọ giảm áp có thể gây tụt não nghịch lý, vì hộp sọ khi đó không còn kín.",
    "3027-xuat-huyet-thuy-caa-nguoi-gia":
        "Xuất huyết do bệnh mạch amyloid não ở người già nằm ở thùy não kèm vi chảy máu vỏ não; Boston 2.0 quyết định dùng lại kháng đông hay LAAO.",
    "3028-va-so-sau-mo-so-giam-ap":
        "Vá sọ sau mở sọ giảm áp: nắp sọ lún và lệch đường giữa về phía khuyết là hạ áp lực, còn lệch ra xa khuyết là tăng áp lực.",
    "3029-aria-khang-the-khang-amyloid":
        "ARIA khi dùng kháng thể kháng amyloid gồm ARIA-E (phù vận mạch, tràn dịch rãnh) và ARIA-H (vi chảy máu, siderosis), phải sàng lọc CAA trước.",
    "3030-tu-mau-duoi-mang-cung-man":
        "Tụ máu dưới màng cứng mạn tính phát sinh từ lớp tế bào bờ màng cứng, có màng và vách, tỷ trọng hỗn hợp theo giai đoạn.",
    "3031-pres-benh-nao-sau-phuc-hoi":
        "PRES là phù vận mạch đối xứng vùng đỉnh–chẩm với ADC tăng nên khác nhồi máu; thể trung tâm và xuất huyết kèm theo là các cạm bẫy.",
    "3032-nao-ung-thuy-ap-luc-binh-thuong":
        "iNPH là giãn não thất do rối loạn hấp thu dịch não tủy với áp lực mở bình thường; DESH và tap test 30 mL định hướng đặt shunt.",
    "3033-benh-nao-wernicke-thieu-thiamin":
        "Bệnh não Wernicke cho T2/FLAIR tăng đối xứng quanh cống Sylvius, đồi thị và thể vú; tam chứng chỉ gặp 10–33% nên đừng chờ đủ.",
    "3034-chay-mau-nao-that-ivh-nao-ung-thuy":
        "Chảy máu não thất gây não úng thủy theo hai cơ chế: tắc nghẽn cơ học do cục máu và hỏng hấp thu do hồng cầu ly giải; Graeb và mGS định mức.",
    "3035-hie-sau-ngung-tim-nguoi-lon":
        "HIE sau ngừng tim ở người lớn cho hạn chế khuếch tán vỏ não ± hạch nền; CT bình thường trong 6 giờ đầu không loại trừ.",
    "3036-trang-thai-myoclonus-sau-ngung-tim":
        "Trạng thái myoclonus sau ngừng tim gồm bốn thực thể với bốn tiên lượng khác nhau, nên phải đọc EEG và HIBI trên MRI cùng lúc.",
    "3037-nhiem-trung-nao-that-evd":
        "Nhiễm trùng não thất và nhiễm trùng liên quan EVD cho mủ trong não thất, ngấm màng nội tủy với DWI sáng ADC tối; biofilm trên catheter là ổ nhiễm.",
    "3038-chet-nao-cta-ct-tuoi-mau":
        "Chết não: tiêu chuẩn lâm sàng và test ngưng thở là chính; CTA/CT tưới máu chỉ đọc đúng khi hiểu thứ tự mất tín hiệu từ vỏ vào trong, CBF < 10.",
    "3039-nhiem-trung-shunt-nao-that-phuc-mac":
        "Nhiễm trùng shunt não thất–phúc mạc và nang giả phúc mạc: hình ảnh không phân biệt vô khuẩn với nhiễm, quyết định nằm ở cấy dịch não tủy và đầu catheter.",
    "3040-chet-nao-tre-em":
        "Chẩn đoán chết não ở trẻ em và sơ sinh: tuổi quyết định khoảng quan sát, trẻ đẻ non dưới 37 tuần không đủ tiêu chuẩn vì phản xạ thân não chưa hoàn chỉnh.",
    "3041-shunt-nao-that-nhi":
        "Shunt não thất–nhĩ dẫn lưu dịch não tủy ra tuần hoàn tĩnh mạch; phải đọc biến chứng đầu xa và chuyển lại VP khi áp lực nhĩ quá cao.",
    "3043-hep-tinh-mach-chu-tren-tre":
        "Hẹp–tắc tĩnh mạch chủ trên lành tính ở trẻ sau catheter trung tâm: đọc CTV/MRV trước khi đặt shunt VA, vì dòng quanh catheter có thể giảm tới 93%.",
    "3044-catheter-tinh-mach-trung-tam-o-tre":
        "Catheter tĩnh mạch trung tâm ở trẻ: đầu catheter phải ở ngã ba tĩnh mạch chủ trên–nhĩ phải; X-quang thẳng không đủ chốt và ba vị trí sai có hậu quả riêng.",
    "3045-catheter-ron-so-sinh-uvc-uac":
        "Catheter rốn ở sơ sinh: UVC phải qua ống tĩnh mạch tới ngã ba tĩnh mạch chủ dưới–nhĩ phải; lạc vào xoang cửa hoặc nhĩ trái gây biến chứng nặng.",
    "3046-chay-mau-cam-do-vo-gia-phinh-dong-mach-canh-trong-xoang-buom":
        "Chảy máu cam ồ ạt do vỡ giả phình động mạch cảnh trong vào xoang bướm: có khối đập trong xoang, và giả phình không có thành thật nên không tự cầm.",
    "3047-hep-khi-quan-sau-dat-noi-khi-quan-o-tre":
        "Hẹp khí quản mắc phải sau đặt nội khí quản ở trẻ hay ở dưới thanh môn; phân độ Myer–Cotton và thời gian hẹp quyết định nong, laser hay cắt nối.",
    "3048-u-mau-gan-o-nhu-nhi":
        "U máu gan ở nhũ nhi là nhiều ổ giảm âm hoặc T2 sáng kèm shunt mạch, gây suy tim và suy giáp tiêu thụ; dùng propranolol khi có biến chứng.",
    "3049-hep-thanh-khi-quan-tai-phat-sau-tao-hinh-o-tre":
        "Hẹp thanh–khí quản tái phát sau tạo hình hay cắt nối hay ở chính miệng nối; phải phân biệt mô hạt với sẹo để chọn nong lại, stent hay mổ lại.",
    "3050-ton-thuong-dong-mach-canh-trong-trong-mo-noi-soi":
        "Tổn thương động mạch cảnh trong trong mổ nội soi mũi xoang gây chảy máu ồ ạt vì mạch áp lực cao nằm trong ống xương, chỉ chèn ép gián tiếp qua xoang.",
    "3052-u-mach-mau-gan-bam-sinh-rich-nich-o-tre":
        "U mạch máu gan bẩm sinh (RICH/NICH) có từ trong tử cung và GLUT1 âm, khác u mạch máu nhũ nhi; phải phân loại ISSVA trước khi quyết định can thiệp.",
    "3053-phau-thuat-keo-dai-ruot-step-lilt":
        "Phẫu thuật kéo dài ruột STEP/LILT ở trẻ ruột ngắn nhắm vào quai giãn và phụ thuộc nuôi dưỡng tĩnh mạch; kiểu giải phẫu còn lại quyết định tiên lượng.",
    "3057-vo-khi-quan-phe-quan-sau-dat-noi-khi-quan":
        "Vỡ khí quản–phế quản lớn sau đặt nội khí quản cho khí trung thất có thể không kèm tràn khí màng phổi; thành sau màng không có sụn đỡ nên là chỗ rách.",
    "3059-thieu-mau-nao-sau-bit-dong-mach-canh-trong":
        "Thiếu máu não sau bít động mạch cảnh trong có thể xảy ra dù BTO âm; vùng nước chết trước vì là bãi tưới xa nhất, nên phải cân nhắc bypass.",
    "3060-hoi-chung-tang-tuoi-mau-nao":
        "Hội chứng tăng tưới máu não sau tái thông cảnh gây đau đầu, co giật, rối loạn tri giác trong 0–14 ngày; CT thường bình thường rồi xuất huyết thùy.",
    "3062-viem-mang-nao-tai-dien-di-tat-tai-trong":
        "Viêm màng não tái diễn ở trẻ có dị tật tai trong và ốc tai hẹp do đường rò dịch não tủy, vì tai trong bình thường vẫn là khoang kín.",
    "3064-reboa-o-tre-em-chon-bong-the-tich-bom-nguong-thoi-gian":
        "REBOA ở trẻ phải chọn cỡ bóng theo đường kính động mạch chủ đo trên CT (zone 1: 6,18–15,21 mm) và giới hạn thời gian chèn.",
    "3065-dau-to-o-nhi-sieu-am-qua-thop":
        "Đầu to ở nhũ nhi: đo chu vi đầu rồi siêu âm qua thóp; phải phân biệt giãn não thủy, khoang dưới nhện rộng lành tính, tụ dịch ngoài trục và phì đại não.",
    "3067-hep-nieu-quan-do-bk-sau-ghep-than":
        "Hẹp niệu quản do BK sau ghép thận là hẹp đoạn dài kèm ứ nước, do virus sinh sản trong biểu mô niệu; phải giảm miễn dịch chứ không chỉ nong.",
    "3068-liet-day-thanh-sau-mo-duong-tho-o-tre":
        "Liệt dây thanh sau mổ đường thở ở trẻ: một bên gây khàn, hai bên gây khó thở; dây thanh liệt nằm ở tư thế trung gian vì mất cơ mở duy nhất.",
    "3069-an-toan-propranolol-o-nhu-nhi":
        "Propranolol ở nhũ nhi có thể gây hạ đường huyết, nhịp chậm và tụt huyết áp vì chẹn β2 ức chế tân tạo glucose và che mất cảnh báo adrenergic.",
    "3074-u-mach-kaposi-kasabach-merritt":
        "U mạch dạng Kaposi (KHE) gây hội chứng Kasabach–Merritt với khối tím lan sâu và tiểu cầu tụt; truyền tiểu cầu là sai vì làm nặng tiêu thụ.",
    "3076-theo-doi-sau-contour-noi-tui":
        "Theo dõi sau thiết bị nội túi Contour cần thang đọc riêng cho lưới hình chén, chú ý di trú, xoay, biến dạng dù lật và tồn dư cổ.",
    "3077-ap-xe-tui-tinh":
        "Áp-xe túi tinh là ổ dịch có vỏ dày, ngấm viền kèm cặn sau bàng quang; tắc ống phóng tinh tạo ổ mủ, chỉ kháng sinh khi nhỏ, còn lại phải dẫn lưu.",
    "3078-nang-ong-utricle-mullerian":
        "Nang ống utricle và nang ống Müllerian là ổ dịch đường giữa thành mỏng thông với niệu đạo sau; theo dõi khi nhỏ, mổ khi có triệu chứng.",
    "3083-chan-thuong-khi-phe-quan-do-luc-tu":
        "Chấn thương khí–phế quản do lực tù gây tràn khí dai dẳng dù đã dẫn lưu và dấu 'phổi rơi', chiếm 0,2–5% chấn thương ngực.",
    "3090-bacteriuria-khong-trieu-chung-be-chua-ruot":
        "Bacteriuria không triệu chứng ở trẻ có bể chứa ruột phải phân biệt với nhiễm khuẩn tiểu có triệu chứng, vì bạch cầu niệu không giúp phân biệt.",
    "3091-coil-hoa-sau-contour-cocojambo":
        "Coil hóa phối hợp thiết bị Contour (CoCoJaMBO) dùng khi còn tồn dư cổ kiểu 'tai chó'; kỹ thuật 'giam' microcatheter quyết định thành công.",
    "3092-nhiem-manh-ghep-sau-nan-go-ma-o-tre":
        "Nhiễm mảnh ghép sau nắn cố định gò má–hàm trên ở trẻ gây sưng mặt muộn, do biofilm trên titanium; khác áp-xe cấp sau mổ vài ngày.",
    "3093-nhoi-mau-nao-do-u-nhay-tim":
        "Nhồi máu não do u nhầy tim thường nhiều ổ vì u ở nhĩ trái di động theo nhịp; có thể kèm túi phình myxoma nên cần mổ tim sớm.",
    "3095-ton-thuong-dong-mach-dui-sau-can-thiep-noi-mach-tre":
        "Tổn thương động mạch đùi–chậu sau can thiệp nội mạch ở trẻ phụ thuộc cỡ sheath; giả phình có tiếng thổi và dấu 'yin-yang' trên Doppler.",
    "3096-benh-than-do-bk-polyomavirus":
        "Bệnh thận do BK polyomavirus sau ghép thận là viêm ống thận–kẽ kèm creatinin tăng; hình ảnh mờ nhạt nên chẩn đoán dựa vào virus học.",
    "3097-zinner-nang-tui-tinh-than-bat-san":
        "Hội chứng Zinner là nang túi tinh cạnh đường giữa sau bàng quang kèm bất sản thận cùng bên và tắc ống phóng tinh, do khiếm khuyết mầm niệu quản.",
    "3099-khe-nguoi-lon-va-the-sau-phuc-mac":
        "KHE ở người lớn và thể sâu sau phúc mạc, trung thất, mũi xoang không có dấu hiệu da nên dễ nhầm sarcoma mạch và thường được chẩn đoán muộn.",
    "3100-quan-ly-ruot-va-kiem-soat-dai-tien-sau-mo-arm":
        "Sau mổ ARM, són phân và táo bón phải đọc theo bốn trụ cột tự chủ đại tiện: cảm giác hậu môn, cơ thắt, nhu động và chức năng chứa.",
    "3104-hoai-tu-xuong-thai-duong-sau-xa":
        "Hoại tử xương thái dương sau xạ vòm họng gây 'viêm tai ngoài' kéo dài 8–10 năm, kèm hẹp ống tai ngoài, theo tam chứng Marx.",
    "3108-vo-mom-phe-quan-sau-cat-phoi":
        "Vỡ mỏm phế quản sau cắt phổi gây rò khí – khoang màng phổi, vì mỏm phế quản không có mạch nuôi trực tiếp tại chỗ.",
    "3109-ap-xe-co-chau-lao-tre":
        "Lao cột sống ở trẻ có thể tạo áp-xe lạnh cơ chậu lan theo bao cơ, kèm hủy thân sống trước sát đĩa đệm.",
    "3110-suy-giap-va-ung-thu-giap-sau-xa-dau-co":
        "Suy giáp và ung thư tuyến giáp thứ phát sau xạ đầu cổ: nang giáp là cấu trúc nhạy xạ nhất và nằm trong trường chiếu của hầu hết phác đồ.",
    "3112-gossypiboma-gac-sot-sau-mo":
        "Gạc sót sau mổ là khối giả u có khí, vôi hóa và dấu xoắn; CT chẩn đoán đúng 90,9% nên đừng chọc dẫn lưu hay cắt nhầm.",
    "3113-avm-nao-tre-tui-phinh-lien-quan-dong-chay":
        "Túi phình kèm AVM não ở trẻ gồm typ không liên quan, typ liên quan dòng chảy trên cuống nuôi và typ trong nidus; mỗi typ xử trí khác nhau.",
    "3115-giam-tieu-cau-thai-nait":
        "Giảm tiểu cầu thai miễn dịch gây xuất huyết nội sọ thai nhi do kháng thể mẹ anti-HPA-1a qua nhau thai; ngưỡng truyền tiểu cầu trong tử cung.",
    "3116-di-can-buong-trung-krukenberg":
        "Di căn buồng trứng Krukenberg là khối đặc hoặc đặc–nang hai bên giữ hình dạng buồng trứng, T2 trung–thấp; ADC không phân biệt được với u nhầy nguyên phát.",
    "3121-nhiem-khuan-manh-ghep-cot-song-o-tre":
        "Nhiễm khuẩn mảnh ghép cột sống ở trẻ tiến triển âm thầm do biofilm nên CRP bình thường không loại trừ; quyết định giữ nẹp hay tháo nẹp theo lâm sàng.",
    "3122-huyet-khoi-tinh-mach-than-ghep-cap":
        "Huyết khối tĩnh mạch thận ghép cấp gây thận phù to, mất phổ tĩnh mạch và đảo dòng tâm trương động mạch, phần lớn trong tuần đầu sau ghép.",
    "3124-coil-loi-di-tru-mach-me":
        "Coil lồi hoặc di trú vào mạch mẹ sau coil hóa túi phình: vật liệu cản quang trong lòng mạch mẹ kèm mất dòng xa, phải phân biệt protrusion với migration.",
    "3129-iga-tai-phat-sau-ghep-than":
        "Bệnh thận IgA tái phát sau ghép thận là bệnh toàn thân của hệ miễn dịch niêm mạc, nên thận ghép 'sạch' vẫn bị: protein niệu và creatinin tăng.",
    "3130-viem-than-be-than-cap-than-ghep":
        "Viêm thận–bể thận cấp ở thận ghép cho vùng nhu mô giảm âm hoặc không ngấm thuốc kèm viêm quanh thận ghép; mất thần kinh nên đau mơ hồ.",
    "3131-hoi-chung-horner-o-tre":
        "Horner một bên ở trẻ là chỉ định chụp MRI cổ–trung thất, vì khối mô mềm cạnh khí quản ở trung thất trên có thể là nguyên nhân.",
    "3132-bien-chung-lo-thong-ace-tre":
        "Biến chứng lỗ thông ACE gồm hẹp da–niêm, hạt thịt, sa niêm mạc, rò dịch và tắc do góc gập; không có ngưỡng HU nào chốt được.",
    "3133-mri-san-chau-sau-mo-arm-tre":
        "MRI sàn chậu sau mổ ARM đánh giá vị trí và calibre neorectum, cơ nâng, ROOF và tủy căng; tới 79% trẻ còn táo bón hoặc són nên đây là câu hỏi thường ngày.",
    "3136-choc-oi-som-truoc-15-tuan":
        "Chọc ối sớm trước 15 tuần làm bàn chân khoèo tăng từ 0,1% lên 1,3% vì màng ối–màng đệm chưa dính; chỉ chọn khi thật cần kết quả sớm.",
    "3138-hoai-tu-xuong-ham-duoi-sau-xa-tri":
        "Hoại tử xương hàm dưới sau xạ trị cho xơ hóa không đồng nhất, tiêu xương vỏ và mảnh xương chết; tủy mỡ thay bằng mô xơ làm xương đặc hơn trên CT.",
    "3139-tui-phinh-nhiem-khuan-noi-so-o-tre":
        "Túi phình nhiễm khuẩn nội sọ ở trẻ mọc trong vài ngày ở nhánh xa, 2 mm vẫn vỡ; CTA có thể bỏ sót nên dấu chốt là nốt tăng đậm dính vào mạch.",
    "3145-chan-thuong-tuy-kin-o-tre":
        "Chấn thương tụy kín ở trẻ có thể âm tính trên CT sớm; phải tìm đứt ống tụy và dịch quanh tụy vì tụy bị kẹp giữa vật đâm và cột sống.",
    "3149-hoi-chung-quai-toi":
        "Hội chứng quai tới sau Whipple là quai ruột giãn chứa dịch có điểm chuyển tiếp — 'tắc mà không tắc' ở quai mật–tụy.",
    "3150-hev-sau-ghep-gan-tre":
        "Viêm gan E mạn sau ghép gan ở trẻ gây tăng transaminase đơn độc kéo dài; phải tìm HEV RNA trong phân và dùng ribavirin khi RNA còn ≥ 3 tháng.",
    "3154-van-nieu-dao-sau-o-tre":
        "Van niệu đạo sau ở bé trai cho giãn niệu đạo sau, thành bàng quang dày và dấu 'keyhole' trên VCUG; chẩn đoán muộn để lại suy thận.",
    "3200-viem-giac-mac-pythium":
        "Viêm giác mạc do Pythium là 'nấm giả' không có ergosterol nên kháng nấm vô hiệu; đặc trưng là tua, chấm nội nhu mô và rãnh ngoại vi.",
    "3201-seo-giac-mac-ghep":
        "Sẹo giác mạc sau loét đã lành phải đo độ sâu để chọn kiểu ghép, vì mô học vẫn có thể còn viêm và làm tăng thải ghép.",
    "3202-viem-giac-mac-do-microsporidia":
        "Viêm giác mạc do microsporidia cho chấm dưới biểu mô dai dẳng, cấy âm; bào tử chỉ 1–4 µm nên đèn khe thấy 'chấm', phải dùng IVCM.",
    "3840-rach-dut-gan-goc-co-gan-kheo":
        "Rách và đứt gân gốc cơ gân kheo cấp hoặc mạn cho đứt gân co rút và khoảng dịch quanh ụ ngồi; phải chú ý thần kinh tọa nằm ngay sau–ngoài.",
    "3841-chen-ep-than-kinh-toa-man-sau-chan-thuong":
        "Chèn ép thần kinh tọa mạn sau chấn thương hay mổ cho dày và tăng tín hiệu khu trú dây thần kinh, mất mặt phẳng mỡ quanh thần kinh.",
    "3842-chen-ep-than-kinh-mac-dau-xuong-mac":
        "Chèn ép thần kinh mác chung tại cổ xương mác gây 'bàn chân rũ' kèm teo cơ trước xương chày; đau lưng không có nghĩa là tổn thương rễ L5.",
    "3843-dau-than-kinh-then-ong-alcock":
        "Đau thần kinh thẹn do chèn ép trong ống Alcock cho dày và tăng tín hiệu dây thần kinh kèm xơ hóa dây chằng và hẹp ống.",
    "3844-di-vat-sot-mo-mem-chi":
        "Dị vật sót trong mô mềm chi: gỗ 'vô hình' trên X-quang vì cellulose có Z hiệu dụng gần mô mềm, nên siêu âm thấy hồi âm mạnh có bóng lưng.",
    "3845-ban-chan-charcot-cap":
        "Bàn chân Charcot cấp cho phù tủy xương và phù mô mềm quanh khớp ở bàn chân nóng đỏ, do mất cảm giác đau cộng với giãn mạch.",
    "6100-cham-soc-va-cai-ong-mo-khi-quan-tre":
        "Chăm sóc ống mở khí quản ở trẻ: hẹp hoặc tắc lòng ống và hẹp khí quản mắc phải, với sức cản đường thở tỉ lệ nghịch lũy thừa 4 bán kính.",
    "6102-nhiem-cmv-bao-thai":
        "Nhiễm CMV bào thai cho vôi hóa quanh não thất và bất thường vỏ não; nguy cơ di chứng phụ thuộc thời điểm nhiễm hơn mức độ nhiễm.",
    "6103-nhiem-toxoplasma-va-zika-bao-thai":
        "Nhiễm Toxoplasma và Zika bào thai khác nhau ở kiểu vôi hóa: toxo vôi hóa rải rác kèm giãn não thất, Zika ở ranh giới vỏ–chất trắng.",
    "6106-benh-giac-mac-do-aniridia-dieu-tri-va-phuc-hoi-be-mat":
        "Bệnh giác mạc do aniridia là thiếu hụt tế bào gốc vùng rìa gây tân mạch lan vào trục thị giác; đừng 'thấy mờ là mổ' vì thị lực kém chủ yếu do hố hoàng điểm.",
    "6107-thay-khop-hang-nguoi-song-sot-ung-thu-nhi":
        "Thay khớp háng ở người sống sót ung thư nhi phải chọn implant theo chất lượng xương và theo dõi cả lỏng vô khuẩn lẫn nhiễm trùng lâu dài.",
    "6108-hoai-tu-xuong-ham-MRONJ-o-tre":
        "Hoại tử xương hàm do thuốc ở trẻ cho mảnh xương chết đậm kèm viền tiêu xương trên CBCT/CT; phân độ AAOMS quyết định ngưỡng ngưng thuốc.",
    "6109-niv-tai-nha-quanh-mo-o-tre":
        "Trẻ thông khí không xâm nhập tại nhà bước vào phòng mổ: phải đánh giá giảm thông khí khi ngủ và ngưỡng hậu phẫu để quyết định giữ hay ngắt NIV.",
    "6112-xuat-huyet-thuong-than-so-sinh":
        "Xuất huyết thượng thận ở sơ sinh là khối trên thận đổi cấu trúc theo ngày, không có dòng chảy bên trong, gặp ở 0,2–0,55% trẻ sinh sống.",
    "6113-huyet-khoi-dong-mach-chu-so-sinh-uac":
        "Huyết khối động mạch chủ ở sơ sinh sau catheter động mạch rốn gây thiếu máu chi dưới; Doppler là chốt, kháng đông hay tiêu sợi huyết tùy mức tắc.",
    "6116-hep-eo-dong-mach-chu-o-tre":
        "Hẹp eo động mạch chủ cho dấu '3' trên phim ngực, khuyết sườn và chênh huyết áp tay–chân, do tổ chức ống động mạch lấn vào thành ĐMC.",
    "6118-hoi-chung-dong-mach-chu-giua":
        "Hội chứng động mạch chủ giữa là hẹp đoạn dài hoặc nhiều đoạn ĐMC bụng kèm hẹp lỗ nhánh tạng và tăng huyết áp kháng trị, có thể không chênh huyết áp.",
    "6119-tang-huyet-ap-ton-luu-sau-can-thiep-hep-eo-dmc":
        "Sau can thiệp hẹp eo động mạch chủ phải trả lời hai câu riêng: còn hẹp lại không và huyết áp còn cao không, vì vòng khâu không lớn theo trẻ.",
    "6120-u-tuy-o-tre":
        "U tụy ở trẻ hay gặp nhất là u đặc–nhầy nhú: khối lớn bờ rõ, hỗn hợp đặc–nang có xuất huyết trong u và vỏ xơ ngấm thuốc muộn.",
    "6121-ro-tuy-sau-mo-tuy-o-tre":
        "Rò tụy sau cắt thân–đuôi tụy ở trẻ phân độ theo ISGPS với amylase dịch dẫn lưu > 3 lần giới hạn trên, đo từ ngày hậu phẫu 3.",
    "6122-gia-phinh-dong-mach-tang-sau-viem-tuy-o-tre":
        "Giả phình động mạch tạng sau viêm tụy hoặc chấn thương tụy ở trẻ có 'sentinel bleed' là tiếng chuông; CTA âm không loại trừ vì túi không có cơ trơn.",
    "6128-rubella-bam-sinh":
        "Rubella bẩm sinh cho tam chứng Gregg: đục thủy tinh thể hai bên, điếc tiếp nhận và hẹp nhánh động mạch phổi, kèm viêm võng mạc muối tiêu.",
    "6129-dot-nhiet-phoi-o-tre-khi-khong-mo-duoc":
        "Đốt nhiệt qua da nốt phổi ở trẻ dùng khi không mổ được; kỹ thuật phá hủy tại chỗ mọi tế bào trong thể tích đốt nên nốt thành quầng mờ ngay sau đốt.",
    "6136-viem-tuy-do-thuoc-o-tre":
        "Viêm tụy cấp do thuốc ở trẻ chiếm 15% ca tại trung tâm nhi; chẩn đoán loại trừ theo bảng Badalov và thời gian tiềm tàng của từng thuốc.",
    "6137-nang-ong-mat-chu-o-tre":
        "Nang ống mật chủ ở trẻ phân loại Todani và cần MRCP trước mổ; cơ chế chính là nối mật–tụy bất thường làm dịch tụy trào ngược vào đường mật.",
    "6140-long-vo-khuan-quanh-khop-hang-nhan-tao":
        "Lỏng vô khuẩn quanh khớp háng nhân tạo ở người trẻ cho đường sáng tiến triển và tiêu xương quanh implant, gặp ở 1,96% ca trong gộp 20 nghiên cứu.",
    "6142-nhiem-trung-va-di-tru-stent-mach-o-tre":
        "Nhiễm trùng, di trú và gãy stent mạch ở trẻ: sốt sau can thiệp gợi ý stentitis hoặc giả phình giả nhiễm trùng, còn stent không lớn theo trẻ nên dễ di trú.",
    "6145-viem-tuy-tu-mien-tre":
        "Viêm tụy tự miễn ở trẻ cho tụy to lan tỏa mất phân thùy kiểu 'xúc xích', ngấm muộn dạng đốm, vỏ bao quanh tụy và hẹp ống tụy dài không giãn phía trên.",
    "6146-soi-tui-mat-o-tre":
        "Sỏi túi mật ở trẻ tăng âm có bóng lưng, còn bùn mật tăng âm không bóng; sỏi ống mật chủ cho giãn ống mật chủ và khuyết lòng.",
    "6150-mycoplasma-pneumoniae-nang-khang-macrolide-o-tre":
        "Viêm phổi do Mycoplasma pneumoniae nặng ở trẻ cho đông đặc và kính mờ không đều kèm tắc phế quản do bã nhầy; đổi thuốc khi kháng macrolide.",
    "6151-trat-khop-hang-nhan-tao-tai-dien":
        "Trật khớp háng nhân tạo tái diễn do mất chiều cao nhảy; phân loại Dorr và đo anteversion trên CT để chọn mổ lại theo nguyên nhân.",
    "6152-viem-tuy-man-o-tre":
        "Viêm tụy mạn ở trẻ cho vôi hóa nhu mô hoặc ống tụy, sỏi ống, giãn ống không đều và teo nhu mô; nguyên nhân ở trẻ là gen và bất thường giải phẫu.",
    "6153-hach-ton-du-sau-dieu-tri-lymphoma-tre":
        "Hạch tồn dư sau điều trị lymphoma ở trẻ có thể vôi hóa dạng chấm và PET âm tính, vì mô xơ thay tế bào u không co ngay.",
    "6154-soi-mat-o-tre-benh-tan-mau":
        "Sỏi mật ở trẻ bệnh tan máu là sỏi sắc tố do bilirubin không liên hợp kết tủa với calci; phải cân nhắc cắt túi mật dự phòng cùng lúc cắt lách.",
    "6156-viem-phoi-mycoplasma-tre-duoi-3-tuoi":
        "Viêm phổi do Mycoplasma ở trẻ dưới 3 tuổi cho mẫu hình viêm tiểu phế quản, thâm nhiễm kẽ quanh phế quản và xẹp phổi, ít đông đặc thùy.",
    "6159-ro-khi-quan-dong-mach-khong-ten":
        "Rò khí quản – động mạch không tên gây chảy máu 'báo trước' qua lỗ mở khí quản; cuff bơm căng làm hoại tử thành trước rồi ăn mòn động mạch.",
    "6160-roi-loan-nuot-sau-cai-ong-mo-khi-quan-tre":
        "Sau cai ống mở khí quản ở trẻ phải tìm rối loạn nuốt và hít sặc cùng hẹp đường thở mới, vì ống làm thay đổi cơ học nuốt.",
    "6161-chylothorax-sau-mo-tim-o-tre":
        "Tràn dưỡng trấp màng phổi sau mổ Fontan/Glenn do áp lực tĩnh mạch hệ thống quyết định, vì dòng bạch huyết chảy theo gradient áp lực.",
    "6162-viem-co-tim-do-ici":
        "Viêm cơ tim do thuốc ức chế điểm kiểm soát có thể có men tim tăng mà MRI 'bình thường'; dấu hiệu là phù cơ tim và LGE vách giữa thành.",
    "6163-viem-dia-dem-than-song-va-phinh-dmc-nhiem-khuan":
        "Viêm đĩa đệm–thân sống kèm phình động mạch chủ nhiễm khuẩn là hai ổ liền kề; túi lệch tâm tiến triển nhanh nên 3–4 cm đã có thể vỡ.",
    "6164-u-nhu-dao-nguoc-tai-phat-sau-mo":
        "U nhú đảo ngược tái phát sau mổ phải phân biệt tái phát thật, nang nhầy và sẹo xơ; mẫu hình cuộn não trên T2 và ADC thấp chỉ là gợi ý.",
    "6165-phu-phoi-crs-sau-car-t-blinatumomab-o-tre":
        "Phù phổi do phản ứng cytokine sau CAR-T và blinatumomab ở trẻ là phù phổi không do tim kèm rò mao mạch toàn thân.",
    "6168-suy-tuy-ngoai-tiet-tre-elastase-1":
        "Suy tụy ngoại tiết ở trẻ đọc bằng elastase-1 phân: enzym không bị phân hủy dọc ruột và không có trong chế phẩm PERT nên kết quả vẫn đọc được.",
    "6169-benh-nao-do-cum-o-tre":
        "Bệnh não do cúm ở trẻ cho tổn thương đồi thị hai bên đối xứng, hạn chế khuếch tán, có thể xuất huyết; MRI là chốt và phải chụp lại sau 48–72 giờ.",
    "6170-shwachman-diamond-tuy-mo-hoa":
        "Hội chứng Shwachman–Diamond cho tụy thay mỡ, tủy giảm sinh và loạn sản metaphysis, với elastase-1 phân thấp là xét nghiệm chức năng chốt.",
    "6171-viem-tuy-cap-do-asparaginase-tre-all":
        "Viêm tụy cấp do asparaginase ở trẻ ALL có thể có hình ảnh bình thường sớm; tế bào nang tụy nhạy nhất vì tổng hợp enzym tiêu hóa rất nhanh.",
    "6172-bat-san-tuy-bam-sinh-thieu-lipase":
        "Bất sản tụy bẩm sinh và thiếu lipase đơn thuần làm tụy 'biến mất' một phần hoặc toàn bộ; MRCP mất mầm lưng giúp phân biệt với IPFD.",
    "6175-ro-khi-da-cai-ong-mo-khi-quan-tre":
        "Rò khí–da sau cai ống mở khí quản ở trẻ là đường hàn có biểu mô lót; phải chọn chờ tự đóng hay vá và cảnh giác hội chứng rò khí sau vá.",
    "6177-viem-nao-hsv-o-tre":
        "Viêm não do herpes simplex ở trẻ gây viêm vỏ não khu trú thái dương–đảo có hạn chế khuếch tán, không theo lãnh thổ mạch; đừng chờ PCR mới chụp.",
    "6178-long-ruot-o-tre":
        "Lồng ruột ở trẻ cho dấu bia và dấu thận giả trên siêu âm, do hạch bạch huyết phì đại kéo đoạn ruột vào trong; quyết định thụt hơi hay mổ.",
    "6179-viem-xuong-tuy-cap-o-tre":
        "Viêm xương tủy cấp ở trẻ bắt đầu ở hành xương với phù tủy, áp-xe dưới màng xương và trong tủy; trẻ dưới 18 tháng có thể lan vào đầu xương.",
    "6181-ro-dnt-sau-mo-so-mat-tre":
        "Rò dịch não tủy sau mổ sọ mặt nâng–tiến ra trước ở trẻ xảy ra vì đường cắt monobloc và Le Fort III đi sát màng cứng ở trần sàng và trần ổ mắt.",
    "6182-lymphangiectasia-ruot-nguyen-phat-tre":
        "Lymphangiectasia ruột nguyên phát ở trẻ gây dày thành ruột non và giãn mạch bạch huyết niêm mạc, nên mất albumin kéo theo mất IgG và lymphocyte.",
    "6194-tang-ap-luc-noi-so-vo-can-o-tre":
        "Tăng áp lực nội sọ vô căn ở trẻ: bộ dấu hiệu MRI–MRV và ngưỡng ONSD theo tuổi; DWI/ADC không tăng là điểm chốt để loại phù não.",
    "6703-benh-co-tim-do-anthracycline-o-nguoi-song-sot-ung-thu-nhi":
        "Bệnh cơ tim do anthracycline ở người sống sót ung thư nhi có EF còn bảo tồn nhưng GLS giảm; LGE thường âm vì xơ hóa lan tỏa, nên GLS là biến sớm.",
    "6704-benh-co-tim-do-xa-o-nguoi-song-sot-ung-thu-nhi":
        "Bệnh cơ tim do xạ ở người sống sót ung thư nhi: trường chiếu quyết định hình ảnh xơ hóa, còn liều tim trung bình quyết định lịch theo dõi.",
    "6705-benh-van-tim-do-xa-o-nguoi-song-sot-ung-thu":
        "Bệnh van tim do xạ xuất hiện sau 10–20 năm, chủ yếu ở van trái; phải chọn thời điểm mổ và cân nhắc van cơ học hay sinh học ở ngực đã xạ.",
    "6706-benh-mach-vanh-do-xa-o-nguoi-song-sot-ung-thu":
        "Bệnh động mạch vành do xạ hẹp ở lỗ và đoạn gần với mảng không vôi trong trường chiếu; thời gian tiềm tàng khoảng 15 năm, tầm soát bằng CTA.",
    "6707-benh-dong-mach-ngoai-bien-do-xa":
        "Bệnh động mạch ngoại biên do xạ hẹp dài, nhẵn, ít vôi và đúng trường chiếu, trong khi mạch ngoài trường chiếu lành — đó là chốt phân biệt với xơ vữa.",
    "6708-hep-dong-mach-than-do-xa-o-tre":
        "Hẹp động mạch thận do xạ ở trẻ gây tăng huyết áp sau nhiều năm với phổ parvus–tardus và thận nhỏ cùng bên; cần giữ liều xạ thận dưới 10–15 Gy.",
    "6709-hep-tinh-mach-chau-dui-do-xa":
        "Hẹp tĩnh mạch chậu–đùi do xạ gây phù chân muộn sau xạ tiểu khung; tổn thương xơ cả ba lớp nên hồi phục kém sau nong và dễ vỡ khi nong quá tay.",
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
