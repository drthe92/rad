#!/usr/bin/env python3
"""Ghép ảnh đối chiếu side-by-side, giữ nguyên tỷ lệ giải phẫu (letterbox nền đen).
Không crop, không kéo giãn (stretch). Mỗi ô: ảnh vừa khít + dải đen đáy ghi [Tên bệnh - chuỗi xung] + attribution.
Chạy local. Yêu cầu: Pillow
VD: python tools/make_composite.py "020-not-phoi/images/020_*.jpg" 020-not-phoi/images/composite_nodule.jpg --height 600
"""
import argparse, glob, os
from PIL import Image, ImageDraw

def load_list(patterns):
    files = []
    for p in patterns:
        files += sorted(glob.glob(p))
    return [f for f in files if "composite_" not in os.path.basename(f)]

def parse_labels(s):
    d = {}
    if s:
        for part in s.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                d[k.strip()] = v.strip()
    return d

def main():
    ap = argparse.ArgumentParser(description="Composite letterbox giữ aspect ratio")
    ap.add_argument("inputs", nargs="+", help="Glob ảnh nguồn + file OUT cuối cùng")
    ap.add_argument("--height", type=int, default=600, help="Chiều cao ô ảnh (px, mặc định 600)")
    ap.add_argument("--band", type=int, default=44, help="Chiều cao dải đen attribution (px)")
    ap.add_argument("--labels", default="", help='"file.jpg=[Bệnh - chuỗi xung] + attribution;..."')
    ap.add_argument("--bg", default="black", help="Màu nền letterbox (mặc định black)")
    ap.add_argument("--max-upscale", type=float, default=2.0, help="Trần phóng to (mặc định 2.0x — không upscale quá gây mờ)")
    a = ap.parse_args()
    *pats, out = a.inputs
    files = load_list(pats)
    assert files, "Không tìm thấy ảnh nguồn"
    caps = parse_labels(a.labels)
    H, BAND = a.height, a.band

    def label_of(path):
        base = os.path.basename(path)
        if base in caps:
            return caps[base]
        return base.replace("_", " ")[:70]

    cells = []
    for f in files:
        im = Image.open(f).convert("RGB")
        w, h = im.size
        scale = min(H / h, a.max_upscale)  # giữ aspect + không upscale quá trần -> tránh mờ
        nw = max(1, round(w * scale))
        im = im.resize((nw, H), Image.LANCZOS)
        cells.append((im, f))
    cell_w = max(im.width for im, _ in cells)  # ô chuẩn = ảnh rộng nhất
    strip_w = cell_w
    strip_h = H + BAND
    canvas = Image.new("RGB", (strip_w * len(cells), strip_h), "black")
    d = ImageDraw.Draw(canvas)
    for i, (im, f) in enumerate(cells):
        x0 = i * strip_w
        # letterbox: căn giữa trên nền đen, không crop/kéo giãn
        canvas.paste(im, (x0 + (strip_w - im.width) // 2, 0))
        d.rectangle([x0, H, x0 + strip_w, strip_h], fill="black")
        d.text((x0 + 6, H + 6), label_of(f), fill="white")
        # viền mỏng phân cách ô
        d.rectangle([x0, 0, x0 + strip_w - 1, strip_h - 1], outline="#333")
    canvas.save(out)
    print(f"OK: {out} từ {len(files)} ảnh | ô {strip_w}x{strip_h} | nền đen letterbox, giữ aspect")

if __name__ == "__main__":
    main()
