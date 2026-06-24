"""Pure-stdlib Markdown → HTML converter for the in-app user guide.

Supports: ATX headings (# … ######), bold, italic, inline code, fenced code
blocks, blockquotes, unordered/ordered lists, tables (GFM), horizontal rules,
paragraph-level image tags (![alt](path)), and bare paragraph text.

Images with a relative path starting with "img/" are resolved relative to
the guide's image directory and embedded as base64 data-URIs so they render
inside QTextBrowser without a live filesystem path.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path


_IMG_DIR: Path | None = None


def set_image_dir(path: Path) -> None:
    """Set the base directory used for resolving relative image paths."""
    global _IMG_DIR
    _IMG_DIR = path


def _embed_img(src: str) -> str:
    """Return a data-URI for a relative image path, or src unchanged."""
    if _IMG_DIR is None or src.startswith(("http://", "https://", "data:")):
        return src
    img_path = _IMG_DIR / src.lstrip("img/")
    if not img_path.exists():
        # try treating src as-is relative to _IMG_DIR parent
        img_path = _IMG_DIR.parent / src
    if not img_path.exists():
        return src
    mime = "image/svg+xml" if img_path.suffix == ".svg" else "image/png"
    data = base64.b64encode(img_path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


# --- inline transforms ---

def _inline(text: str) -> str:
    """Apply bold, italic, inline-code transforms to a span of text."""
    # inline code first (protect content from further transforms)
    parts: list[str] = []
    idx = 0
    for m in re.finditer(r"`([^`]+)`", text):
        parts.append(_escape(text[idx:m.start()]))
        parts.append(f"<code>{_escape(m.group(1))}</code>")
        idx = m.end()
    parts.append(_escape(text[idx:]))
    text = "".join(parts)

    # bold **..** or __..__ (greedy-avoided via [^*_])
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # italic *..* or _.._
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"_([^_]+)_", r"<i>\1</i>", text)
    return text


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- block-level rendering ---

def _render_table(rows: list[str]) -> str:
    if len(rows) < 2:
        return ""
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    # skip separator row (rows[1] contains --- patterns)
    body = rows[2:]
    th = "".join(f"<th>{_inline(h)}</th>" for h in header)
    html = (
        '<table border="1" cellspacing="0" cellpadding="4" '
        'style="border-collapse:collapse;width:100%;margin:8px 0;">'
        f"<thead><tr>{th}</tr></thead><tbody>"
    )
    for row in body:
        cells = [c.strip() for c in row.strip("|").split("|")]
        td = "".join(f"<td>{_inline(c)}</td>" for c in cells)
        html += f"<tr>{td}</tr>"
    html += "</tbody></table>"
    return html


def _render_list(items: list[str], ordered: bool) -> str:
    tag = "ol" if ordered else "ul"
    inner = "".join(f"<li>{_inline(item.lstrip('-*0123456789. '))}</li>" for item in items)
    return f"<{tag}>{inner}</{tag}>"


def render(markdown: str, image_dir: Path | None = None) -> str:
    """Convert *markdown* to an HTML fragment suitable for QTextBrowser."""
    if image_dir is not None:
        set_image_dir(image_dir)

    lines = markdown.splitlines()
    html_parts: list[str] = []

    # CSS for QTextBrowser (subset of CSS2 supported by Qt)
    html_parts.append(
        "<style>"
        "body{font-family:'Segoe UI',Arial,sans-serif;font-size:10pt;margin:12px;color:#333;}"
        "h1{font-size:16pt;color:#0055a5;border-bottom:2px solid #0055a5;padding-bottom:4px;}"
        "h2{font-size:13pt;color:#0055a5;border-bottom:1px solid #aac4e8;padding-bottom:2px;}"
        "h3{font-size:11pt;color:#333;}"
        "h4,h5,h6{font-size:10pt;color:#555;}"
        "code{background:#f0f0f0;padding:1px 3px;border-radius:2px;font-family:Consolas,monospace;}"
        "pre{background:#f0f0f0;padding:8px;border-left:3px solid #0055a5;}"
        "blockquote{border-left:4px solid #aaa;margin:4px 0;padding:4px 8px;"
        "background:#fafafa;color:#555;}"
        "table{border-collapse:collapse;width:100%;}"
        "th{background:#0055a5;color:white;padding:4px 6px;}"
        "td{padding:3px 6px;border:1px solid #ccc;}"
        "tr:nth-child(even)td{background:#f4f2ee;}"
        "ul,ol{margin-left:16px;}"
        "hr{border:none;border-top:1px solid #ccc;}"
        "img{max-width:100%;}"
        "</style>"
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        # fenced code block
        if line.startswith("```"):
            lang = line[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(_escape(lines[i]))
                i += 1
            code_html = "\n".join(code_lines)
            html_parts.append(f'<pre><code class="language-{lang}">{code_html}</code></pre>')
            i += 1
            continue

        # ATX headings
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            html_parts.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # horizontal rule
        if re.match(r"^[-*_]{3,}\s*$", line):
            html_parts.append("<hr/>")
            i += 1
            continue

        # blockquote
        if line.startswith(">"):
            bq_lines: list[str] = []
            while i < len(lines) and lines[i].startswith(">"):
                bq_lines.append(lines[i].lstrip("> "))
                i += 1
            inner = render("\n".join(bq_lines), image_dir)
            # strip outer <style> block from recursive call
            inner = re.sub(r"<style>.*?</style>", "", inner, flags=re.DOTALL)
            html_parts.append(f"<blockquote>{inner}</blockquote>")
            continue

        # table: starts with |
        if line.startswith("|"):
            table_rows: list[str] = []
            while i < len(lines) and lines[i].startswith("|"):
                table_rows.append(lines[i])
                i += 1
            html_parts.append(_render_table(table_rows))
            continue

        # unordered list
        if re.match(r"^[-*+]\s", line):
            list_items: list[str] = []
            while i < len(lines) and re.match(r"^[-*+]\s", lines[i]):
                list_items.append(lines[i])
                i += 1
            html_parts.append(_render_list(list_items, ordered=False))
            continue

        # ordered list
        if re.match(r"^\d+\.\s", line):
            list_items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                list_items.append(lines[i])
                i += 1
            html_parts.append(_render_list(list_items, ordered=True))
            continue

        # paragraph-level image  ![alt](src)
        m_img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line.strip())
        if m_img:
            alt, src = m_img.group(1), m_img.group(2)
            src = _embed_img(src)
            html_parts.append(
                f'<p style="text-align:center;">'
                f'<img src="{src}" alt="{_escape(alt)}" style="max-width:100%;"/></p>'
            )
            i += 1
            continue

        # blank line
        if not line.strip():
            i += 1
            continue

        # paragraph (collect until blank or block-level)
        para_lines: list[str] = []
        while i < len(lines):
            l = lines[i]
            if (
                not l.strip()
                or l.startswith("#")
                or l.startswith(">")
                or l.startswith("|")
                or l.startswith("```")
                or re.match(r"^[-*+]\s", l)
                or re.match(r"^\d+\.\s", l)
                or re.match(r"^[-*_]{3,}\s*$", l)
            ):
                break
            para_lines.append(l)
            i += 1
        if para_lines:
            html_parts.append(f"<p>{_inline(' '.join(para_lines))}</p>")

    return "\n".join(html_parts)
