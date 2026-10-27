#!/usr/bin/env python3
"""Dựng lại index.html (hub tra cứu) từ frontmatter của 132 lesson.md.
Giữ microcopy đã biên tập (tiêu đề/mô tả/ảnh trong thẻ cũ), bổ sung thẻ mới
cho bài tổng quan, tabs phân hệ, chips RADS, dark mode, table view.

Chạy: python3 tools/build_index.py   (từ thư mục gốc repo)
Idempotent: chạy lại vẫn cho kết quả như nhau.
"""
import html
import os
import re
from pathlib import Path

CERT_LABEL = {"tong-hop-y-van": "Tổng hợp y văn",
              "ca-nguyen-van": "Ca nguyên văn",
              "suy-luan": "Suy luận"}
OV_DESC = "📚 Bài tổng quan hệ: bảng DDx bắt buộc + bài liên quan chéo."
REQUIRED_SCORES = ["LI-RADS", "Lung-RADS", "BI-RADS", "O-RADS", "TI-RADS",
                   "PI-RADS", "Bosniak", "ASPECTS", "Atlanta"]
TABS = [("", "🌐 Tất cả"), ("nguc", "🫁 Ngực 000–099"),
        ("bung", "🩺 Bụng 100–199"), ("thankinh", "🧠 TK & Cổ 200–299"),
        ("msk", "🦴 MSK 300–399"), ("mat", "👁️ Mắt 400–499"),
        ("vuspk", "🌸 Vú & SPK 500–599"), ("nhi", "👶 Nhi 600–699"),
        ("dauco", "👃 Đầu Cổ 700–"), ("tim", "❤️ Tim 800–"),
        ("canthiep", "🧰 Can thiệp 900–")]


def spec_of(uid):
    try:
        n = int(str(uid))
    except ValueError:
        return "khac"
    return {0: "nguc", 1: "bung", 2: "thankinh", 3: "msk", 4: "mat",
            5: "vuspk", 6: "nhi", 7: "dauco", 8: "tim", 9: "canthiep"}.get(n // 100, "khac")


# ID 4 chữ số là dải tràn (overflow) — gán phân hệ thủ công cho đúng tab.
SPEC_OVERRIDE = {"1601": "vuspk", "1602": "vuspk", "1604": "vuspk", "1605": "vuspk", "1606": "vuspk", "1607": "vuspk", "1608": "bung", "1609": "vuspk", "1610": "vuspk", "1611": "vuspk", "1636": "vuspk", "1780": "nhi", "1801": "bung", "1803": "nhi", "1805": "nhi", "6102": "nhi", "6701": "nhi", "1622": "dauco", "3003": "thankinh", "1627": "mat", "1613": "vuspk", "1614": "vuspk", "1600": "vuspk", "1618": "vuspk", "1901": "bung", "1902": "bung", "1903": "bung", "1904": "bung", "1905": "bung", "1906": "bung", "1907": "bung", "1623": "vuspk", "1615": "msk", "1616": "vuspk", "1782": "nhi", "1420": "mat", "1421": "mat", "1795": "nhi", "1620": "vuspk", "1621": "vuspk", "1624": "vuspk", "1625": "nhi", "1640": "vuspk", "1804": "nhi", "1807": "bung", "3001": "nhi", "3002": "thankinh", "3012": "thankinh", "3013": "thankinh", "3014": "thankinh", "3015": "thankinh"}


def frontmatter(path):
    t = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", t, re.S)
    fm, body = m.group(1), m.group(2)
    out = {}
    for key in ("unit_id", "subspecialty", "tags", "certainty"):
        mm = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
        out[key] = (mm.group(1).strip().strip('"') if mm else "")
    h1 = re.search(r"^#\s+(.+)$", body, re.M)
    out["h1"] = h1.group(1).strip() if h1 else Path(path).parent.name
    imgs = re.findall(r"!\[.*?\]\((images/[^)\s]+)\)", body)
    out["thumb"] = next((i for i in imgs if (Path(path).parent / i).exists()), "")
    return out


def curated_copy(index_text):
    """Tiêu đề/mô tả/ảnh đã biên tập trong các thẻ hiện có (neo bằng class ctitle)."""
    cards = {}
    for b in re.split(r'(?=<div class="card")', index_text):
        if not b.startswith('<div class="card"'):
            continue
        m = re.search(r'view\.html\?b=([^&]+)&', b)
        if not m:
            continue
        d = m.group(1)
        mt = re.search(r'class="ctitle"[^>]*>([^<]*)</a>', b)
        if mt:  # định dạng hub mới: neo bằng class ctitle
            mt_text = html.unescape(mt.group(1))
        else:  # định dạng thẻ cũ (trước hub mới): link tiêu đề là anchor có text
            links = re.findall(r'<a href="[^"]+">([^<]*)</a>', b)
            mt_text = next((t for t in links if t and t not in ("Bài học", "Nguồn")), "")
            mt_text = html.unescape(mt_text)
        if mt_text in ("Bài học", "Nguồn"):
            mt_text = ""
        mp = re.search(r'<p>(.*?)</p>', b, re.S)
        mi = re.search(r'<img[^>]+src="([^"]+)" alt="([^"]*)"', b)
        cards[d] = {"title": mt_text,
                    "desc": mp.group(1) if mp else "",
                    "img": (mi.group(1), html.unescape(mi.group(2))) if mi else None}
    return cards


def main():
    root = Path(".")
    # Chỉ nhận bài "hoàn chỉnh" (có lesson.md + sources.md theo bất biến repo);
    # bài đang viết dở (chưa có sources.md) sẽ không lên hub tới khi hoàn tất.
    dirs = sorted(d for d in os.listdir(".")
                  if re.match(r"^\d{3,4}-", d) and (root / d / "lesson.md").exists()
                  and (root / d / "sources.md").exists())
    old = root.joinpath("index.html").read_text(encoding="utf-8") if root.joinpath("index.html").exists() else ""
    keep = curated_copy(old)

    recs, card_html, overviews = [], [], []
    for d in dirs:
        fm = frontmatter(f"{d}/lesson.md")
        tags = [t.strip() for t in fm["tags"].strip("[]").split(",") if t.strip()]
        uid = fm["unit_id"]
        spec = SPEC_OVERRIDE.get(uid, spec_of(uid))
        scores = [t.split(":", 1)[1] for t in tags if t.startswith("score:")]
        cert = CERT_LABEL.get(fm["certainty"], fm["certainty"])
        k = keep.get(d, {})
        title = k.get("title") or fm["h1"]
        desc = k.get("desc") or OV_DESC
        img = k.get("img") or ((f"{d}/{fm['thumb']}", title) if fm["thumb"] else None)
        search = f"{uid} {title} {' '.join(tags)} {d}"
        spans = " ".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags[:4])
        if len(tags) > 4:
            spans += f' <span class="tag more">+{len(tags) - 4}</span>'
        img_html = (f'<a href="view.html?b={d}&f=lesson.md">'
                    f'<img loading="lazy" src="{img[0]}" alt="{html.escape(img[1])}"></a>' if img else "")
        card_html.append(
            f'<div class="card" data-id="{html.escape(uid)}" data-spec="{spec}" '
            f'data-scores="{html.escape(" ".join(scores))}" data-cert="{html.escape(fm["certainty"])}" '
            f'data-tags="{html.escape(" ".join(tags))}" data-search="{html.escape(search)}">{img_html}'
            f'<div class="cid">{html.escape(uid)} · {spec.upper()}</div>'
            f'<a class="ctitle" href="view.html?b={d}&f=lesson.md">{html.escape(title)}</a><br>'
            f'{spans}<span class="cert">{html.escape(cert)}</span><p>{desc}</p>'
            f'<a href="view.html?b={d}&f=lesson.md">Bài học</a> · '
            f'<a href="view.html?b={d}&f=sources.md" target="_blank" rel="noopener">Nguồn</a> '
            f'<button class="learn" data-learn="{html.escape(uid)}" '
            f'title="Đánh dấu bài này đã học (lưu trong trình duyệt của bạn)">✓ Đã học</button></div>')
        recs.append((uid, tags))
        if "tong-quan" in d or "overview" in d:
            vi = fm["h1"].split(" / ")[0].strip()
            vi = re.sub(r"^\d{3}\s*[—–-]\s*", "", vi)
            vi = re.sub(r"^Tổng quan\s+", "", vi, flags=re.I).split(":")[0].strip()
            vi = vi[:1].upper() + vi[1:]
            overviews.append((uid, d, f"{uid} · {vi}"))

    ov_options = ['<option value="">📚 Bài tổng quan hệ (' + str(len(overviews)) + ")</option>"]
    ov_options += [f'<option value="view.html?b={d}&f=lesson.md">{html.escape(label)}</option>'
                   for _, d, label in sorted(overviews)]
    ov_select = '<select id="fOverview" title="Nhảy nhanh tới bài tổng quan của từng hệ">' \
                + "".join(ov_options) + "</select>"

    present = sorted({s for _, tags in recs for t in tags
                      for s in ([t.split(":", 1)[1]] if t.startswith("score:") else [])})
    chips = ['<button class="chip on" data-score="">🏷️ Tất cả</button>']
    chips += [f'<button class="chip" data-score="{s}">{s}</button>'
              for s in REQUIRED_SCORES if s in present]
    chips += [f'<button class="chip extra" data-score="{s}">{s}</button>'
              for s in present if s not in REQUIRED_SCORES]
    tabs = "".join(f'<button class="tab{" on" if not v else ""}" data-spec="{v}">{lab}</button>'
                   for v, lab in TABS)

    page = Path("tools/hub_template.html").read_text(encoding="utf-8")
    page = (page.replace("__TABS__", tabs).replace("__CHIPS__", "\n".join(chips))
                .replace("__OVSELECT__", ov_select).replace("__CARDS__", "\n".join(card_html))
                .replace("__N__", str(len(card_html))))
    root.joinpath("index.html").write_text(page, encoding="utf-8")
    print(f"index.html: {len(card_html)} thẻ, {len(chips)} chips, score tags: {present}")


if __name__ == "__main__":
    main()
