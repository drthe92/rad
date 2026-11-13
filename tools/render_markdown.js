#!/usr/bin/env node
/**
 * tools/render_markdown.js — render markdown của lesson.md thành HTML tĩnh.
 *
 * Dùng marked (vendored, MIT) để đạt parity với view.html: bảng GFM,
 * <details>/<summary>, HTML thô, fenced code, mermaid.
 *
 * Giao thức (batch, 1 tiến trình cho N bài):
 *   stdin : {"items":[{"id":"020-not-phoi","md":"..."}]}
 *   stdout: {"items":[{"id":"...","html":"...","mermaid":true,"firstImage":"images/x.jpg"}]}
 *
 * Không đọc/ghi file — builder Python chịu trách nhiệm I/O.
 */
import { marked } from "../assets/vendor/marked.esm.mjs";

const escAttr = (s = "") =>
  String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const escHtml = (s = "") =>
  String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const slugify = (s = "") =>
  s
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60) || "muc";

marked.use({
  gfm: true,
  breaks: false,
  renderer: {
    heading({ tokens, depth }) {
      const inner = this.parser.parseInline(tokens);
      const plain = inner.replace(/<[^>]+>/g, "");
      return `<h${depth} id="${escAttr(slugify(plain))}">${inner}</h${depth}>\n`;
    },
    link({ href = "", title, tokens }) {
      let h = href;
      let m = h.match(/^(?:\.\.\/)?(\d{3,4}-[^/]+)\/lesson\.md(#.*)?$/);
      if (m) h = `/${m[1]}/${m[2] || ""}`;
      else if ((m = h.match(/^\.\.\/(\d{3,4}-[^/]+)\/?$/))) h = `/${m[1]}/`;
      else if (h === "index.html") h = "/";
      const t = title ? ` title="${escAttr(title)}"` : "";
      const ext = /^https?:\/\//.test(h) ? ' target="_blank" rel="noopener"' : "";
      return `<a href="${escAttr(h)}"${t}${ext}>${this.parser.parseInline(tokens)}</a>`;
    },
    image({ href = "", title, text }) {
      const t = title ? ` title="${escAttr(title)}"` : "";
      return `<img loading="lazy" decoding="async" src="${escAttr(href)}" alt="${escAttr(text || "")}"${t}>`;
    },
    code({ text, lang }) {
      const l = (lang || "").trim().toLowerCase();
      if (l === "mermaid") return `<pre class="mermaid">${escHtml(text)}</pre>\n`;
      const cls = l ? ` class="language-${escAttr(l)}"` : "";
      return `<pre><code${cls}>${escHtml(text)}</code></pre>\n`;
    },
  },
});

let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  const input = JSON.parse(raw || '{"items":[]}');
  const out = [];
  for (const it of input.items || []) {
    let html = "";
    try {
      html = marked.parse(it.md || "");
    } catch (e) {
      html = `<pre class="render-error">Lỗi render: ${escHtml(String(e && e.message))}</pre>`;
    }
    const mm = html.match(/<img[^>]+src="([^"]+)"/);
    out.push({
      id: it.id,
      html,
      mermaid: html.includes('class="mermaid"'),
      firstImage: mm ? mm[1] : null,
    });
  }
  process.stdout.write(JSON.stringify({ items: out }));
});
