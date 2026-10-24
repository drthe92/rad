#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixture cho verify_all — chặn hồi quy các luật đã chốt (2026-10-24):
  - parity hub ↔ folder là CỔNG (không phải chỉ số);
  - chạy thiếu cổng → PARTIAL, kể cả khi đủ 4 cổng cũ nhưng thiếu index;
  - `--only` thiếu giá trị → exit 2;
  - cảnh báo legacy của selfcheck được đếm vào entry.

Chạy: python3 tools/tests/test_verify_all.py
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location(
    "verify_all", os.path.join(TOOLS, "verify_all.py"))
va = importlib.util.module_from_spec(spec)
spec.loader.exec_module(va)


def write(path, text=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class MetricsFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_parity_and_image_buckets(self):
        d = os.path.join(self.root, "999-bai")
        write(os.path.join(d, "lesson.md"),
              "![a](images/999_hien-thi.jpg)\n![b](images/999_hien-thi-2.jpg)\n")
        write(os.path.join(d, "images", "CREDITS.md"), "999_hien-thi.jpg\n")
        write(os.path.join(d, "images", "999_hien-thi.jpg"), "")
        write(os.path.join(d, "images", "999_hien-thi-2.jpg"), "")
        write(os.path.join(d, "images", "999_khong-hien-thi.jpg"), "")
        write(os.path.join(self.root, "index.html"),
              '<a href="view.html?b=999-bai&x=1">x</a>')
        write(os.path.join(self.root, "BACKLOG.md"),
              "| A | 999 | x | y | chờ viết |\n| B | 999 | x | y | chờ viết |\n")

        m = va.metrics(self.root)
        self.assertEqual(m["lessons_total"], 1)
        self.assertEqual(m["index_cards"], 1)
        self.assertEqual(m["index_parity_delta"], 0)
        self.assertEqual(m["lessons_missing_card"], 0)
        self.assertEqual(m["images_total"], 3)
        self.assertEqual(m["images_referenced_uncredited"], 1)   # ...-2 chưa credit
        self.assertEqual(m["images_unreferenced"], 1)            # khong-hien-thi
        self.assertEqual(m["images_unreferenced_uncredited"], 1)
        self.assertEqual(m["backlog_waiting"], 2)
        self.assertEqual(m["backlog_duplicate_ids"], ["999"])

    def test_index_gate_fails_on_parity(self):
        write(os.path.join(self.root, "999-bai", "lesson.md"), "")
        write(os.path.join(self.root, "index.html"), "")          # thiếu card
        m = va.metrics(self.root)
        self.assertEqual(m["index_parity_delta"], -1)
        self.assertFalse(va.run_index(m)["pass"])

    def test_index_gate_passes_when_aligned(self):
        write(os.path.join(self.root, "999-bai", "lesson.md"), "")
        write(os.path.join(self.root, "index.html"),
              '<a href="view.html?b=999-bai&x=1">x</a>')
        self.assertTrue(va.run_index(va.metrics(self.root))["pass"])


class PartialFixture(unittest.TestCase):
    def test_full_set_is_not_partial(self):
        self.assertFalse(va.is_partial(None))
        self.assertFalse(va.is_partial(list(va.ALL_CHECKS)))

    def test_four_old_gates_without_index_is_partial(self):
        old_four = [g for g in va.GATES]
        self.assertTrue(va.is_partial(old_four))

    def test_subset_is_partial(self):
        self.assertTrue(va.is_partial(["selfcheck"]))


class CliFixture(unittest.TestCase):
    def run_cli(self, *args):
        cmd = [sys.executable, os.path.join(TOOLS, "verify_all.py")] + list(args)
        return subprocess.run(cmd, cwd=va.ROOT, capture_output=True, text=True)

    def test_only_without_value_exits_2(self):
        p = self.run_cli("--only")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)

    def test_unknown_gate_exits_2(self):
        p = self.run_cli("--only", "khong-co")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)

    def test_only_selfcheck_is_partial_and_dry(self):
        p = self.run_cli("--only", "selfcheck", "--dry-run", "--offline")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("PARTIAL PASS", p.stdout)

    def test_selfcheck_warning_parser(self):
        lines = ["SELFCHECK PASS (515 bài; 15 cảnh báo legacy)",
                 "SELFCHECK WARN (không chặn commit):",
                 " ! 011-tieu-thuy-phoi: chưa có ma trận 2 cột (legacy)"]
        self.assertEqual(va.parse_selfcheck_warnings(lines), 15)
        self.assertEqual(va.parse_selfcheck_warnings(
            ["SELFCHECK PASS (515 bài)"]), 0)
        self.assertEqual(va.parse_selfcheck_warnings([]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
