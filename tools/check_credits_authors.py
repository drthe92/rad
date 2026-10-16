#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_credits_authors.py — Kiểm tra TRUNG THỰC NGUỒN ẢNH.

Đối chiếu tên tác giả khai báo (trong lesson.md / sources.md / images/CREDITS.md)
với tác giả THẬT của PMCID tương ứng (tra Europe PMC).

Vì sao: worker từng "đoán" tên tác giả theo trí nhớ → sai (120/434/525/655:
Balci/Bass/Solanki/Saxena/Martinello đều khác với PMCID thực tế).

Cách dùng:
    python3 tools/check_credits_authors.py                # quét toàn repo
    python3 tools/check_credits_authors.py 655-* 120-*     # chỉ vài folder
    python3 tools/check_credits_authors.py --offline       # chỉ dùng cache, không tra mạng
    python3 tools/check_credits_authors.py --refresh       # xóa cache rồi tra lại

Tối ưu: tra Europe PMC theo lô (OR nhiều PMCID/lần) + cache đĩa
(/tmp/opencode/credits_authors_cache.json) để các lần sau gần như tức thời.

Exit code:
    0 = không có sai lệch xác nhận (kể cả khi mạng lỗi — chỉ cảnh báo)
    1 = có ít nhất 1 tên tác giả SAI so với PMCID
"""
import sys, re, glob, json, os, urllib.request, urllib.parse

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CACHE = "/tmp/opencode/credits_authors_cache.json"
BATCH = 15

RE_NAME = re.compile(r"([A-Z][A-Za-zÀ-ỹ'\-]{2,})(?:\s+[A-Z]{1,3})?\s*,?\s+et al")
RE_NAME_DO = re.compile(r"\bdo\s+([A-Z][A-Za-zÀ-ỹ'\-]{2,})\s+et al")
RE_PMC = re.compile(r"PMC\d+")


def load_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(c):
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(c, f)
    except Exception:
        pass


def batch_fetch(pmcids):
    """Trả về (map pmcid->authorString, tap pmcid-loi)."""
    got, failed = {}, set()
    pmcids = list(pmcids)
    for i in range(0, len(pmcids), BATCH):
        chunk = pmcids[i:i + BATCH]
        q = " OR ".join("PMCID:" + p for p in chunk)
        url = "%s?query=%s&format=json&resultType=core&pageSize=%d" % (
            EPMC, urllib.parse.quote(q), max(25, len(chunk) * 2))
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                j = json.load(r)
            res = j.get("resultList", {}).get("result", [])
            found = set()
            for x in res:
                pid = x.get("pmcid") or ""
                if pid:
                    got[pid] = x.get("authorString", "")
                    found.add(pid)
            for p in chunk:
                if p not in found:
                    failed.add(p)  # không tra được (hoặc không tồn tại)
        except Exception:
            failed.update(chunk)
    return got, failed


def surnames(authorstring):
    out = set()
    for part in authorstring.split(","):
        part = part.strip()
        if part:
            out.add(part.split()[0].lower().rstrip("."))
    return out


def token_set(authorstring):
    """Mọi mảnh tên (tách cả dấu cách & gạch nối) đã lower — xử lý họ có tiền tố
    kiểu 'van Aswegen', 'Al-Hseinat', 'Al-Ani'."""
    return {t for t in re.split(r"[,\s\-]+", authorstring.lower()) if t.strip(".")}


def name_ok(claimed, actual_tokens):
    """Đúng nếu MỌI mảnh của tên khai báo đều có trong tên thật."""
    parts = [p for p in re.split(r"[,\s\-]+", claimed.lower()) if p.strip(".")]
    return bool(parts) and all(p in actual_tokens for p in parts)


def scan(files):
    rows = []
    for f in files:
        try:
            txt = open(f, encoding="utf-8").read()
        except Exception:
            continue
        for ln in txt.split("\n"):
            pm = RE_PMC.findall(ln)
            if not pm:
                continue
            names = RE_NAME.findall(ln) + RE_NAME_DO.findall(ln)
            if names:
                rows.append((f, sorted(set(pm)), sorted(set(names))))
    return rows


def resolve_files(folders):
    if not folders:
        return sorted(set(glob.glob("*/lesson.md") + glob.glob("*/sources.md")
                            + glob.glob("*/images/CREDITS.md")))
    files = []
    for pat in folders:
        hits = (glob.glob(os.path.join(pat, "lesson.md"))
                + glob.glob(os.path.join(pat, "sources.md"))
                + glob.glob(os.path.join(pat, "images", "CREDITS.md"))
                + glob.glob(pat))
        files += hits
    return sorted(set(files))


def main(argv):
    offline = "--offline" in argv
    refresh = "--refresh" in argv
    folders = [a for a in argv if not a.startswith("-")]

    files = resolve_files(folders)
    rows = scan(files)
    all_pmc = sorted({p for _, pms, _ in rows for p in pms})

    cache = {} if refresh else load_cache()
    missing = [p for p in all_pmc if p not in cache]
    net_fail = set()
    if missing and not offline:
        got, failed = batch_fetch(missing)
        cache.update(got)
        save_cache(cache)
        net_fail = failed
    elif missing and offline:
        net_fail = set(missing)

    mismatches = []
    for f, pms, names in rows:
        if any(p not in cache for p in pms):
            continue  # thiếu dữ liệu → không kết luận
        actual_tokens = set()
        actual_union = set()
        for p in pms:
            actual_tokens |= token_set(cache[p])
            actual_union |= surnames(cache[p])
        miss = [n for n in names if len(n) > 2 and not name_ok(n, actual_tokens)]
        if miss:
            mismatches.append((f, pms, names, miss, sorted(actual_union),
                               " | ".join(cache[p] for p in pms)))

    print("🔎 check_credits_authors — kiểm tra tên tác giả vs PMCID")
    print("   file quét: %d | dòng có PMCID+tên: %d | PMCID: %d (cache %d)"
          % (len(files), len(rows), len(all_pmc), len(all_pmc) - len(missing)))
    if offline:
        print("   (--offline: chỉ dùng cache)")
    if net_fail:
        print("   ⚠️  %d PMCID chưa tra được (bỏ qua, không kết luận): %s"
              % (len(net_fail), ", ".join(sorted(net_fail)[:10])))
    if mismatches:
        print("\n❌ SAI TÊN TÁC GIẢ (%d):" % len(mismatches))
        for f, pms, names, miss, actual, full in mismatches:
            print("   %s\n     PMCID=%s khai báo=%s SAI=%s\n     thực tế=%s"
                  % (f, pms, names, miss, full))
        print("\n→ Sửa tên cho khớp PMCID trước khi commit "
              "(hoặc ghi 'Tạp chí Năm (PMCID)' không kèm tên).")
        return 1
    print("✅ Không phát hiện tên tác giả sai lệch (so với PMCID).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
