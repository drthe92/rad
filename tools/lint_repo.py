#!/usr/bin/env python3
"""Lint kho lưu trữ CĐHA — kiểm tra frontmatter, khung 6 mục, link bảng đầu bài,
ảnh nhúng, thẻ <details>, bảng Markdown và link bài học gãy.

Chạy: python3 tools/lint_repo.py   (từ thư mục gốc repo)
Exit 0 = không có lỗi; exit 1 = có lỗi nghiêm trọng.
Không cần PyYAML: có fallback parser cho frontmatter đơn giản của repo.
"""
import os
import re
import sys
from pathlib import Path

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


def parse_frontmatter(text):
    """Parse YAML minimal (key: value, list inline [a, b], có/không dấu nháy)."""
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            data[key] = items
        else:
            data[key] = val.strip("\"'")
    return data


def load_frontmatter(text):
    if HAVE_YAML:
        return yaml.safe_load(text)
    return parse_frontmatter(text)


def lint_repo():
    root_dir = Path(".")
    errors = []
    warnings = []
    total_lessons = 0

    print("🔍 Bắt đầu quét và kiểm tra (Linting) kho lưu trữ CĐHA...")
    if not HAVE_YAML:
        print("   (không có PyYAML — dùng parser YAML nội bộ cho frontmatter đơn giản)")

    # Tìm tất cả file lesson.md (bỏ qua thư mục ẩn, tools, templates, node_modules)
    lesson_files = []
    for path in sorted(root_dir.rglob("lesson.md")):
        if any(part.startswith(".") or part in ["tools", "templates", "node_modules"] for part in path.parts):
            continue
        lesson_files.append(path)

    for lesson_path in lesson_files:
        total_lessons += 1
        rel_path = str(lesson_path)
        folder_dir = lesson_path.parent

        content = lesson_path.read_text(encoding="utf-8")

        # 1. Frontmatter YAML
        match_fm = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
        if not match_fm:
            errors.append(f"[{rel_path}] Thiếu hoặc sai định dạng Frontmatter YAML ở đầu file.")
            continue

        fm_text = match_fm.group(1)
        body_text = match_fm.group(2)

        try:
            fm_data = load_frontmatter(fm_text)
        except Exception as e:
            errors.append(f"[{rel_path}] Lỗi cú pháp YAML Frontmatter: {e}")
            continue
        if not isinstance(fm_data, dict):
            errors.append(f"[{rel_path}] Frontmatter không parse được thành key-value.")
            continue

        required_fields = ["unit_id", "subspecialty", "anatomical_location",
                           "primary_pattern", "tags", "certainty"]
        for field in required_fields:
            if field not in fm_data:
                errors.append(f"[{rel_path}] Frontmatter thiếu trường bắt buộc: '{field}'")

        # 2. Khung 6 mục — miễn file tổng quan (001, 100, 200, ... / tên tong-quan, overview)
        unit_id = str(fm_data.get("unit_id", ""))
        slug = folder_dir.name
        is_overview = (len(unit_id) == 3 and unit_id.endswith("00")) or unit_id == "001" \
            or "tong-quan" in slug or "overview" in slug

        if not is_overview:
            prev = -1
            for i in range(1, 7):
                m_h = re.search(rf"^##\s+{i}\.\s+", body_text, re.M)
                if not m_h:
                    errors.append(f"[{rel_path}] Thiếu tiêu chuẩn Mục {i} (phải có dạng '## {i}. ...')")
                elif prev >= 0 and m_h.start() < prev:
                    errors.append(f"[{rel_path}] Sai thứ tự: Mục {i} xuất hiện trước các mục nhỏ hơn.")
                else:
                    prev = m_h.start()

        # 3a. Ảnh Markdown: ![alt](images/filename.jpg)
        img_matches = re.findall(r"!\[.*?\]\((images/[^)\s]+)\)", body_text)
        # 3b. Ảnh HTML: <img src="images/...">
        img_matches += re.findall(r"<img[^>]+src=[\"'](images/[^\"'\s]+)[\"']", body_text, re.IGNORECASE)
        for img_rel_path in img_matches:
            if not (folder_dir / img_rel_path).exists():
                errors.append(f"[{rel_path}] Tham chiếu ảnh không tồn tại trên đĩa: '{img_rel_path}'")

        # 3c. Link bài học gãy: ](../NNN-slug/lesson.md)
        for m_link in re.finditer(r"\]\(\.\./([^)]+)/lesson\.md\)", body_text):
            if not (root_dir / m_link.group(1) / "lesson.md").exists():
                errors.append(f"[{rel_path}] Link bài học gãy: ../{m_link.group(1)}/lesson.md")

        # 4. Thẻ Blind Quiz <details> đóng/mở khớp nhau
        open_details = len(re.findall(r"<details\b", body_text, re.IGNORECASE))
        close_details = len(re.findall(r"</details>", body_text, re.IGNORECASE))
        if open_details != close_details:
            warnings.append(f"[{rel_path}] Số thẻ mở <details> ({open_details}) "
                            f"không khớp số thẻ đóng </details> ({close_details}).")

        # 5a. Bảng Markdown lệch cột (mỗi khối bảng liên tục phải cùng số cột)
        blocks, cur = [], []
        for line in body_text.splitlines():
            if line.lstrip().startswith("|"):
                cur.append(line)
            elif cur:
                blocks.append(cur)
                cur = []
        if cur:
            blocks.append(cur)
        for b in blocks:
            n = b[0].count("|")
            bad = [l[:60] for l in b if l.count("|") != n]
            if bad:
                errors.append(f"[{rel_path}] Bảng Markdown lệch cột: {bad[0]}...")
                break

        # 5b. Dấu hiệu gõ phím thường gặp
        for line_no, line in enumerate(body_text.splitlines(), 1):
            if re.search(r"\]\([^)]*$", line):
                warnings.append(f"[{rel_path}] Dòng ~{line_no}: link Markdown thiếu dấu ')' đóng")
            elif line.count("**") % 2 == 1:
                warnings.append(f"[{rel_path}] Dòng ~{line_no}: số '**' lẻ — nhãn bold có thể thiếu đóng")

    # Bỏ trùng lặp (giữ thứ tự) — một ảnh/bảng hỏng có thể được nhắc nhiều lần
    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))

    print(f"\n📊 Kết quả quét: Đã kiểm tra {total_lessons} file bài học.")
    if errors:
        print(f"❌ Phát hiện {len(errors)} lỗi nghiêm trọng (Errors):")
        for err in errors:
            print(f"  - {err}")
    else:
        print("✅ Không phát hiện lỗi nghiêm trọng nào trong Frontmatter, "
              "cấu trúc 6 mục, link ảnh và bảng.")
    if warnings:
        print(f"\n⚠️ Phát hiện {len(warnings)} cảnh báo (Warnings):")
        print("  *(Cảnh báo không chặn build nhưng cần rà soát lại)*")
        for warn in warnings:
            print(f"  - {warn}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(lint_repo())
