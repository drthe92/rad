#!/usr/bin/env python3
"""Ghép ảnh đối chiếu side-by-side + dải đen attribution (Argon đề xuất, ta chuẩn hóa).
Chạy local (không cần trên Pages). Yêu cầu: pip install Pillow
VD: python tools/make_composite.py 020-not-phoi/images/"020_*.jpg" 020-not-phoi/images/composite_nodule.jpg
"""
import sys, glob
from PIL import Image, ImageDraw

BAND = 34  # chiều cao dải đen

def load_list(patterns):
    files = []
    for p in patterns:
        files += sorted(glob.glob(p))
    # loại file composite cũ ra
    return [f for f in files if "composite_" not in f]

def label_of(path, captions):
    return captions.get(path, path.split("/")[-1].replace("_", " ")[:60])

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    *pats, out = sys.argv[1:]
    files = load_list(pats)
    assert files, "Không tìm thấy ảnh nguồn"
    # captions: đọc từ CREDITS.md nếu có? đơn giản: tên file
    ims = [Image.open(f).convert("RGB") for f in files]
    h = min(i.height for i in ims)
    ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    W = sum(i.width for i in ims)
    canvas = Image.new("RGB", (W, h + BAND * len(ims) // len(ims) + BAND), "white")
    # xếp ngang, mỗi ảnh có dải đen riêng ở đáy
    x = 0
    strip_h = h + BAND
    canvas = Image.new("RGB", (W, strip_h), "white")
    d = ImageDraw.Draw(canvas)
    for im, f in zip(ims, files):
        canvas.paste(im, (x, 0))
        d.rectangle([x, h, x + im.width, strip_h], fill="black")
        d.text((x + 6, h + 9), label_of(f, {}), fill="white")
        x += im.width
    canvas.save(out)
    print(f"OK: {out} từ {len(files)} ảnh")

if __name__ == "__main__":
    main()
