#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_mermaid.py — Sửa các lỗi Mermaid 10.x hay gặp trong lesson.md.

Lỗi điển hình (Mermaid 10.9.1 báo "Syntax error in text"):
  1. `\\n` bên trong label  → phải dùng `<br/>`.
  2. Label KHÔNG quote mà chứa `(` hoặc `)` → phải bọc trong nháy kép.

Script chỉ sửa trong khối ```mermaid, giữ nguyên phần còn lại.
Idempotent: chạy lại không đổi gì nếu đã sạch.

Dùng:
    python3 tools/fix_mermaid.py --check   # chỉ báo, không sửa (exit 1 nếu còn lỗi)
    python3 tools/fix_mermaid.py           # sửa tại chỗ
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK = re.compile(r'(```mermaid\n)(.*?)(```)', re.S)


def fix_text(b):
    b = b.replace("\\n", "<br/>")

    # (0) ngoặc đóng sai: X[...} hoặc X{...]
    b = re.sub(r'([A-Za-z0-9_]+)\[([^\[\]}]*)\}',
               lambda m: "%s[%s]" % (m.group(1), m.group(2)), b)
    b = re.sub(r'([A-Za-z0-9_]+)\{([^{}\]]*)\]',
               lambda m: "%s{%s}" % (m.group(1), m.group(2)), b)

    # (1) node label: quote nếu chưa quote mà chứa ( ) hoặc "
    def sq(m):
        node, lab = m.group(1), m.group(2)
        if lab.strip().startswith('"'):
            return m.group(0)
        if any(ch in lab for ch in '()"'):
            return '%s["%s"]' % (node, lab.replace('"', "'"))
        return m.group(0)

    def cu(m):
        node, lab = m.group(1), m.group(2)
        if lab.strip().startswith('"'):
            return m.group(0)
        if any(ch in lab for ch in '()"'):
            return '%s{"%s"}' % (node, lab.replace('"', "'"))
        return m.group(0)

    b = re.sub(r'([A-Za-z0-9_]+)\[([^\[\]]*)\]', sq, b)
    b = re.sub(r'([A-Za-z0-9_]+)\{([^{}]*)\}', cu, b)

    # (2) edge label |...|: ngoặc đơn -> HTML entity
    def edge(line):
        if not re.search(r'(-\.?->|==>|---)', line):
            return line
        return re.sub(r'\|([^|\n]*)\|',
                      lambda m: "|" + m.group(1).replace("(", "&#40;").replace(")", "&#41;") + "|",
                      line)

    b = "\n".join(edge(l) for l in b.split("\n"))
    return b


def scan(b):
    """Trả về danh sách lỗi còn lại trong 1 block."""
    errs = []
    if "\\n" in b:
        errs.append("còn \\n trong label")

    # ngoặc đóng sai
    if re.search(r'\[[^\[\]]*\}', b) or re.search(r'\{[^{}]*\]', b):
        errs.append("ngoặc đóng sai (X[...} hoặc X{...])")

    # node label chưa quote mà chứa ngoặc/nháy
    for m in re.finditer(r'[\[\{]([^\]\}\n]*)[\]\}]', b):
        lab = m.group(1)
        if lab.strip().startswith('"'):
            continue
        if any(ch in lab for ch in '()"'):
            errs.append("node label chưa quote: %s" % lab[:50])

    # edge label chứa ngoặc
    for line in b.split("\n"):
        if not re.search(r'(-\.?->|==>|---)', line):
            continue
        for m in re.finditer(r'\|([^|\n]*)\|', line):
            if "(" in m.group(1) or ")" in m.group(1):
                errs.append("edge label chứa ngoặc: %s" % m.group(1)[:50])
    return errs


def main(argv):
    check = "--check" in argv
    files = sorted(glob.glob(os.path.join(ROOT, "*/lesson.md")))
    changed, still = [], []
    for f in files:
        t = open(f, encoding="utf-8").read()
        if "```mermaid" not in t:
            continue
        new = BLOCK.sub(lambda m: m.group(1) + fix_text(m.group(2)) + m.group(3), t)
        if new != t:
            changed.append(f)
            if not check:
                open(f, "w", encoding="utf-8").write(new)
        probe = t if check else new
        for m in BLOCK.finditer(probe):
            for e in scan(m.group(2)):
                still.append((os.path.relpath(f, ROOT), e))

    print("file có mermaid: %d | sửa: %d | lỗi còn lại: %d"
          % (len([f for f in files if "```mermaid" in open(f, encoding="utf-8").read()]),
             len(changed), len(still)))
    for r, e in still[:20]:
        print("  ⚠️  %s — %s" % (r, e))
    if check and (changed or still):
        print("→ chạy `python3 tools/fix_mermaid.py` để sửa.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
