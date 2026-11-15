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
#lb .x{position:absolute;top:10px;right:16px;color:#fff;font-size:28px;line-height:1;cursor:pointer;background:none;border:0}
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
<div id="lb" role="dialog" aria-modal="true" aria-label="Xem ảnh phóng to"><button class="x" type="button" aria-label="Đóng">×</button><img alt="" draggable="false"><div class="cap"></div></div>
<script>
(function(){
  var box=document.getElementById('noi-dung'), lb=document.getElementById('lb');
  if(!box||!lb) return;
  var im=lb.querySelector('img'), cap=lb.querySelector('.cap'), xb=lb.querySelector('.x');
  var sc=1, tx=0, ty=0, drag=null;
  function tf(){ im.style.transform='translate('+(tx?tx+'px':'0')+','+(ty?ty+'px':'0')+') scale('+sc+')'; }
  function reset(){ sc=1; tx=0; ty=0; tf(); }
  function close(){ lb.classList.remove('open'); reset(); }
  function open(src,alt){ im.src=src; im.alt=alt||''; cap.textContent=alt||''; reset(); lb.classList.add('open'); }
  box.addEventListener('click',function(e){
    var el=e.target, img=el&&el.closest?el.closest('img'):null;
    if(!img||!box.contains(img)) return;
    e.preventDefault();
    open(img.currentSrc||img.src,img.alt);
  });
  lb.addEventListener('click',function(e){ if(e.target!==im) close(); });
  xb.addEventListener('click',function(e){ e.stopPropagation(); close(); });
  document.addEventListener('keydown',function(e){
    if((e.key==='Escape'||e.key==='Esc')&&lb.classList.contains('open')) close();
  });
  im.addEventListener('wheel',function(e){
    e.preventDefault(); e.stopPropagation();
    sc=Math.min(4,Math.max(1,sc+(e.deltaY<0?0.25:-0.25)));
    if(sc===1){ tx=0; ty=0; }
    tf();
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
