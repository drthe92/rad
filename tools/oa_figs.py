#!/usr/bin/env python3
"""Tìm & tải hình minh hoạ open-access từ Europe PMC (kèm license + caption).

Dùng:
  python3 tools/oa_figs.py --query 'FIG:"gantry tilt" AND lens' --dest DIR --prefix 9420 --max 4

Chỉ tải bài OPEN_ACCESS:Y; in JSON metadata (pmcid, title, journal, year, license,
caption, file) để ghi CREDITS. Không tải khi license không rõ.
"""
import argparse, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*"}


def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search(query, size=12):
    q = f'({query}) AND OPEN_ACCESS:Y'
    url = f"{EPMC}/search?query={urllib.parse.quote(q)}&format=json&pageSize={size}&resultType=core"
    return json.loads(get(url).decode("utf-8")).get("resultList", {}).get("result", [])


def xml_figs(pmcid):
    url = f"{EPMC}/{pmcid}/fullTextXML"
    try:
        x = get(url).decode("utf-8", "ignore")
    except Exception:
        return [], ""
    lic = ""
    m = re.search(r'<license[^>]*xlink:href="([^"]+)"[^>]*>(.*?)</license>', x, re.S)
    if m:
        lic = (m.group(1) or "").strip() or re.sub(r"<[^>]+>", " ", m.group(2)).strip()[:80]
    else:
        m2 = re.search(r'<license[^>]*>(.*?)</license>', x, re.S)
        if m2:
            lic = re.sub(r"<[^>]+>", " ", m2.group(1)).strip()[:80]
    figs = []
    for fm in re.finditer(r"<fig\b[^>]*>(.*?)</fig>", x, re.S):
        body = fm.group(1)
        g = re.search(r'xlink:href="([^"]+)"', body)
        if not g:
            continue
        cap = re.search(r"<caption>(.*?)</caption>", body, re.S)
        cap = re.sub(r"<[^>]+>", " ", cap.group(1)) if cap else ""
        cap = re.sub(r"\s+", " ", cap).strip()
        lab = re.search(r"<label>(.*?)</label>", body, re.S)
        figs.append({"href": g.group(1), "label": re.sub(r"<[^>]+>", "", lab.group(1)).strip() if lab else "",
                     "caption": cap[:400]})
    return figs, lic


def blob_url(pmcid, href):
    """PMC CDN không chặn bot; URL blob lấy từ trang HTML bài báo."""
    try:
        html = get(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/").decode("utf-8", "ignore")
    except Exception:
        return ""
    cands = re.findall(r'https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^"\'\s]+', html)
    base = href.rsplit("/", 1)[-1]
    for u in cands:
        if u.rsplit("/", 1)[-1] == base:
            return u
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--max", type=int, default=3)
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("--fig", type=int, default=1, help="lấy hình thứ N trong bài (1-based)")
    ap.add_argument("--pmcid", help="chỉ lấy từ một PMCID cụ thể")
    a = ap.parse_args()
    dest = Path(a.dest); dest.mkdir(parents=True, exist_ok=True)
    out = []
    recs = search(a.query, a.size)
    if a.pmcid:
        recs = [r for r in recs if r.get("pmcid") == a.pmcid] or recs
    for rec in recs:
        if len(out) >= a.max:
            break
        pmcid = rec.get("pmcid")
        if not pmcid:
            continue
        figs, lic = xml_figs(pmcid)
        if not figs or not lic:
            continue
        lic_l = lic.lower()
        if not any(k in lic_l for k in ("cc by", "cc0", "creative commons", "open access")):
            continue
        fig = figs[min(a.fig - 1, len(figs) - 1)]
        href = fig["href"]
        url = blob_url(pmcid, href)
        if not url:
            continue
        fn = f"{a.prefix}_{pmcid}-{href}"
        try:
            data = get(url)
            if len(data) < 8000:
                continue
            (dest / fn).write_bytes(data)
        except Exception:
            continue
        lic_short = (rec.get("license") or "").strip()
        out.append({
            "file": fn, "pmcid": pmcid, "doi": rec.get("doi", ""),
            "title": rec.get("title", ""), "journal": (rec.get("journalInfo", {}) or {}).get("journal", {}).get("title", ""),
            "year": rec.get("pubYear", ""), "license": (lic_short or lic), "label": fig["label"], "caption": fig["caption"],
            "url": f"https://europepmc.org/article/PMC/{pmcid}",
        })
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out else 1


if __name__ == "__main__":
    sys.exit(main())
