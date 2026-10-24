#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixture cho selfcheck — chặn hồi quy 2 lỗi đã sửa (2026-10-24):
  1. Bảng bối cảnh đứng TRƯỚC ma trận từng làm bài đúng bị báo thiếu cột.
  2. Folder ID 4 chữ số từng bị glob 3 chữ số bỏ sót.
  3. Bài tổng quan chỉ được miễn theo TÊN FOLDER, không phải vì nhắc chữ "tổng quan".

Chạy: python3 tools/tests/test_selfcheck.py
"""
import importlib.util
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location(
    "selfcheck", os.path.join(TOOLS, "selfcheck.py"))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

MATRIX = (
    "| Thực thể (entity) | Hình ảnh điển hình | Chốt vào (rule-in) | "
    "Chốt loại (rule-out) | Gợi ý xác nhận |\n"
    "|---|---|---|---|---|\n"
    "| A | B | **C** | **D** | E |\n"
)
CONTEXT = (
    "| Bối cảnh | Kỹ thuật | Lý do |\n"
    "|---|---|---|\n"
    "| Trẻ nhỏ | Gián tiếp | Mạch nhỏ |\n"
)


def lesson_body(matrix="", extra=""):
    return f"""---
unit_id: "999"
subspecialty: Chest
anatomical_location: "phổi (lung)"
primary_pattern: "nốt (nodule)"
tags: [pattern:not]
certainty: tong-hop-y-van
---

# 999 — Bài test

Mở đầu nhắc tới [tổng quan hệ](../001-tong-quan-he-nguc/lesson.md) — chữ này
không được biến bài thành "tổng quan".

## 1. Tổng quan
Nốt 5 mm là ngưỡng ví dụ.

## 2. Mẫu hình
A, B.

## 3. Ma trận
{matrix}

## 4. Protocol
CT 1 mm.

## 5. Cạm bẫy
Không.

## 6. Quiz
<details><summary>Đáp án</summary>A.</details>
{extra}"""


class SelfcheckFixture(unittest.TestCase):
    def setUp(self):
        sc.WARNINGS.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.old = os.getcwd()
        os.chdir(self.root)
        # Bài tổng quan thật để link chéo trong fixture không bị coi là link gãy.
        os.makedirs(os.path.join(self.root, "001-tong-quan-he-nguc"))
        open(os.path.join(self.root, "001-tong-quan-he-nguc", "lesson.md"), "w").close()

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def write(self, slug, body):
        d = os.path.join(self.root, slug)
        os.makedirs(os.path.join(d, "images"), exist_ok=True)
        with open(os.path.join(d, "lesson.md"), "w", encoding="utf-8") as f:
            f.write(body)
        open(os.path.join(d, "images", "CREDITS.md"), "w").close()
        open(os.path.join(d, "sources.md"), "w").close()
        return slug

    def test_context_table_before_matrix_passes(self):
        slug = self.write("999-bai-thuong", lesson_body(CONTEXT + "\n" + MATRIX))
        self.assertEqual(sc.check(slug), [])

    def test_only_context_table_fails_matrix(self):
        slug = self.write("999-bai-thuong", lesson_body(CONTEXT))
        errs = sc.check(slug)
        self.assertTrue(any("ma trận" in e for e in errs), errs)

    def test_four_digit_folder_discovered(self):
        self.write("9999-bai-bon-so", lesson_body(MATRIX))
        self.assertIn("9999-bai-bon-so", sc.discover())

    def test_overview_by_slug_is_exempt(self):
        slug = self.write("998-tong-quan-test", lesson_body(CONTEXT))
        self.assertEqual(sc.check(slug), [])

    def test_legacy_matrix_warns_not_fails(self):
        slug = self.write("997-bai-cu", lesson_body(CONTEXT))
        sc.LEGACY_MATRIX.add(slug)
        try:
            self.assertEqual(sc.check(slug), [])
            self.assertTrue(any(slug in w for w in sc.WARNINGS), sc.WARNINGS)
        finally:
            sc.LEGACY_MATRIX.discard(slug)

    def test_legacy_cleared_when_upgraded(self):
        slug = self.write("996-bai-nang-cap", lesson_body(MATRIX))
        sc.LEGACY_MATRIX.add(slug)
        try:
            sc.check(slug)
            self.assertTrue(any("xoá khỏi LEGACY_MATRIX" in w for w in sc.WARNINGS), sc.WARNINGS)
        finally:
            sc.LEGACY_MATRIX.discard(slug)


if __name__ == "__main__":
    unittest.main(verbosity=2)
