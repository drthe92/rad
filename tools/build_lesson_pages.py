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


def first_paragraph(body):
    """Đoạn văn đầu tiên đủ dài, bỏ qua frontmatter/tiêu đề/tag/bảng/code/blockquote."""
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
    return SITE_DESC


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
    items = []
    for d in sorted(os.listdir(ROOT)):
        m = LESSON_RE.match(d)
        if not m or not os.path.isdir(os.path.join(ROOT, d)):
            continue
        lp = os.path.join(ROOT, d, "lesson.md")
        if not os.path.exists(lp):
            continue
        if only and m.group(1) != str(only):
            continue
        items.append((m.group(1), d, lp))
    return items


def render(items):
    payload = []
    bodies = {}
    for uid, slug, lp in items:
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
    ap.add_argument("--only", help="chỉ một ID (vd 020)")
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
        tags = fm.get("tags") or []
        spec = spec_label(uid, tags, title)
        cert = fm.get("certainty", "")
        cert_label = {"ca-nguyen-van": "ca nguyên văn", "tong-hop-y-van": "tổng hợp y văn",
                      "suy-luan": "suy luận"}.get(cert, cert or "tổng hợp y văn")
        desc = plain(first_paragraph(body), 158) or SITE_DESC
        pattern = plain(str(fm.get("primary_pattern", "")), 155)
        if len(pattern) >= 80:
            desc = pattern
        else:
            tvi = re.sub(r"^\d+\s*[—–-]\s*", "", title).split(" / ")[0].strip()
            desc = plain(f"{tvi}: {desc}", 158)
        lastmod = lastmods.get(f"{slug}/lesson.md", today)
        url = f"{BASE}/{slug}/"
        img = it.get("firstImage") or "/assets/og-default.png"
        if img.startswith("images/"):
            img = f"{BASE}/{slug}/{img}"
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
    for uid, slug, lp in items:
        text = read(lp)
        fm, body = split_frontmatter(text)
        h1 = re.search(r"^#\s+(.+)$", body, re.M)
        title = (h1.group(1) if h1 else slug).strip()
        desc = plain(first_paragraph(body), 120)
        lines.append(f"- [{title}]({BASE}/{slug}/) — {desc}")
    lines += ["", "## Ghi chú", "",
              "- Nội dung tổng hợp từ y văn mở, có trích dẫn PMCID/DOI trong sources.md.",
              "- Không dùng để chẩn đoán độc lập khi chưa có người hướng dẫn.",
              "- Ảnh giữ nguyên giấy phép ghi trong images/CREDITS.md từng bài."]
    write_if_changed(os.path.join(ROOT, "llms.txt"), "\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
