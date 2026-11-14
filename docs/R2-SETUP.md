# R2 — chuyển ảnh sang `img.matcauvong.com`

Mục tiêu: ảnh bài học phục vụ từ Cloudflare R2 thay vì GitHub Pages, giảm site
tĩnh từ ~842 MB xuống còn phần HTML/Markdown, tăng tốc tải và tránh ngưỡng 1 GB.

## Kiến trúc

```
repo:  <slug>/images/<file>            (nguồn gốc, vẫn giữ trong git)
R2:    rad-img/<slug>/images/<file>    (bản phát hành)
CDN:   https://img.matcauvong.com/<slug>/images/<file>
build: nếu file có trong tools/r2_manifest.json → HTML dùng URL CDN
       nếu chưa có → giữ đường dẫn local (không vỡ ảnh)
```

- `tools/r2_upload.py` — upload S3/SigV4 thuần Python (không cần aws-cli).
- `tools/r2_manifest.json` — sha256/size/etag từng ảnh đã upload; **commit** để build tất định.
- `tools/cdn.py` — builder tra manifest, đổi `src` sang CDN.
- `sitemap.xml` / `llms.txt` không phụ thuộc ảnh.

## Phần đã làm trên máy

- Viết uploader có `--plan`, `--upload`, `--verify`, `--selftest`; retry 5xx/429,
  upload song song, resume theo sha256.
- SigV4 đã đối chiếu **vector chuẩn AWS** (`get-vanilla`): `SELFTEST OK`.
- Tích hợp đổi ảnh sang CDN trong trang bài + thumbnail hub; cổng `static`
  kiểm ảnh CDN phải có trong manifest.
- Manifest khởi tạo rỗng; build hiện vẫn dùng ảnh local (không thay đổi gì trên site).

## Phần bạn làm trên Cloudflare (một lần)

### 1. Tạo bucket
1. Cloudflare Dashboard → **R2 Object Storage** → **Create bucket**.
2. Tên: `rad-img` (khớp `R2_BUCKET`), location: **Automatic** (hoặc APAC).
3. Không cần bật “Public access” mặc định; ta dùng custom domain.

### 2. Gắn custom domain
1. Vào bucket `rad-img` → **Settings** → **Custom Domains** → **Connect Domain**.
2. Nhập `img.matcauvong.com` → Cloudflare tự tạo DNS record (zone đang ở Cloudflare).
3. Chờ trạng thái **Active** (vài phút). Cache mặc định của Cloudflare là đủ;
   `Cache-Control: immutable` đã được uploader gắn cho từng object.

### 3. Tạo API token (chỉ bucket này)
1. R2 → **Manage R2 API Tokens** → **Create API token**.
2. Permission: **Object Read & Write**.
3. Scope: **Only specific bucket** → `rad-img`.
4. TTL: để trống (hoặc 1 năm) — lưu **Access Key ID** và **Secret Access Key** ngay,
   secret chỉ hiện một lần.
5. Lấy **Account ID**: góc phải dashboard Cloudflare (hoặc URL
   `dash.cloudflare.com/<account_id>/r2`).

### 4. Lưu khóa trên máy chạy build (không commit)
```sh
mkdir -p ~/.config/rad
cat > ~/.config/rad/r2.env <<'ENV'
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=rad-img
R2_PUBLIC_BASE=https://img.matcauvong.com
ENV
chmod 600 ~/.config/rad/r2.env
```
Script tự đọc file này; biến môi trường có sẵn được ưu tiên hơn.

### 5. Kiểm tra và upload
```sh
python3 tools/r2_upload.py --selftest     # ký đúng chuẩn AWS
python3 tools/r2_upload.py --plan         # xem bao nhiêu ảnh cần đưa lên
python3 tools/r2_upload.py --upload       # ~5.970 ảnh / ~730 MB
python3 tools/r2_upload.py --verify --sample 50 --public
```
Upload chạy song song 8 luồng, lưu manifest dần nên có thể dừng/chạy lại.
Ước tính 10–30 phút tùy đường truyền. R2 miễn phí 10 GB lưu trữ, egress 0 đồng.

### 6. Báo tôi sau khi upload xong
Tôi sẽ:
1. Chạy `--verify` toàn bộ.
2. Build lại **toàn bộ** trang + hub để `src` chuyển sang CDN.
3. Kiểm 20 ảnh ngẫu nhiên qua `img.matcauvong.com`, chạy `verify_all` 7/7, commit + push.

## Nén ảnh trước khi upload (đã áp dụng 2026-11-14)

- **Tier 1:** JPEG ≥ 300 KB → q85 progressive. 207 ảnh, 138,7 → 51,0 MB (−87,7 MB).
- **Tier 2:** JPEG 100–300 KB → q88 progressive. 1.614 ảnh, 331,1 → 167,5 MB (−163,6 MB).
- **Không nén:** 659 ảnh CC BY-ND/BY-NC-ND (97 MB), license không rõ, PNG, ảnh < 100 KB.
- Tổng ảnh còn **~605 MB**; site ~722 MB (trước 842 MB).
- Giữ nguyên tên/đuôi file → không sửa `lesson.md`/`CREDITS.md`.
- Backup bản gốc: `/tmp/opencode/img-backup/t1`, `/tmp/opencode/img-backup/t2`.
  Log sha: `tools/optimize_log.jsonl` (đã gitignore) — chạy lại sẽ không nén lặp.
- Rollback một ảnh: copy từ backup (hoặc `git checkout -- <file>` nếu chưa commit).

## Sau khi ảnh lên CDN: giảm dung lượng Pages (tuỳ chọn nhưng nên làm)

Hiện ảnh vẫn nằm trong repo nên GitHub Pages vẫn phục vụ chúng (site ~842 MB).
Muốn site nhẹ thật sự, chuyển Pages sang **GitHub Actions** và loại `*/images/*`
khỏi artifact:

1. Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Thêm workflow `.github/workflows/pages.yml`:

```yaml
name: Deploy site
on:
  push: { branches: [master] }
  workflow_dispatch:
permissions: { contents: read, pages: write, id-token: write }
concurrency: { group: pages, cancel-in-progress: true }
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: github-pages
    steps:
      - uses: actions/checkout@v4
      - name: Stage site (bỏ ảnh gốc, giữ HTML/MD/asset)
        run: |
          mkdir -p _site
          rsync -a --delete \
            --exclude='.git' --exclude='.github' --exclude='tools' \
            --exclude='templates' --exclude='*/images/*' \
            --exclude='BACKLOG*' --exclude='AGENTS.md' --exclude='README.md' \
            ./ _site/
      - uses: actions/upload-pages-artifact@v3
        with: { path: _site }
      - uses: actions/deploy-pages@v4
```

3. Điều kiện bắt buộc trước khi bật: **mọi ảnh phải có trong manifest**, nếu không
   ảnh chưa upload sẽ 404. Kiểm bằng:
   ```sh
   python3 tools/r2_upload.py --plan   # phải báo "cần upload: 0"
   ```

Nếu chưa muốn đổi Pages, giữ nguyên: ảnh CDN vẫn nhanh hơn nhưng site vẫn nặng.

## Rollback

- Một ảnh lỗi: xoá key khỏi `tools/r2_manifest.json`, build lại → trang dùng ảnh local.
- Toàn bộ: đặt `"files": {}` trong manifest, build lại.
- Không cần xoá object trên R2 ngay; dung lượng 730 MB vẫn trong free tier.

## Bảo mật

- Không commit `~/.config/rad/r2.env`; không dán secret vào chat.
- Token chỉ có quyền object trên đúng bucket `rad-img`.
- Uploader không in secret; log chỉ có key/etag/sha256.
