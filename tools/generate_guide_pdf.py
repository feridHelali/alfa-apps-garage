"""Generate a PDF copy of the user guide.

Usage:
    python tools/generate_guide_pdf.py [output.pdf]

Requires: PyQt6 (already a project dependency).
Output defaults to: docs/Guide_Utilisateur_GarageReparation.pdf
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from garage_app.tools.guide_generator.md_renderer import render as md_render

GUIDE_DIR = ROOT / "resources" / "guide" / "fr"
IMG_DIR = ROOT / "resources" / "guide" / "img"
OUTPUT_DIR = ROOT / "docs"

CHAPTERS = [
    "00_introduction.md",
    "01_reception.md",
    "02_atelier.md",
    "03_stock.md",
    "04_facturation.md",
    "05_administration.md",
    "06_rapports.md",
    "07_faq.md",
    "08_devis_proforma.md",
]


def build_combined_html() -> str:
    parts = [
        """<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
body{font-family:'Segoe UI',Arial,sans-serif;font-size:10pt;margin:20px 40px;color:#222;}
h1{font-size:18pt;color:#0055a5;border-bottom:3px solid #0055a5;padding-bottom:6px;
   margin-top:30px;page-break-before:always;}
h1:first-of-type{page-break-before:avoid;}
h2{font-size:13pt;color:#0055a5;border-bottom:1px solid #aac4e8;padding-bottom:3px;margin-top:20px;}
h3{font-size:11pt;color:#333;margin-top:14px;}
code{background:#f0f0f0;padding:1px 4px;border-radius:2px;font-family:Consolas,monospace;font-size:9pt;}
pre{background:#f0f0f0;padding:8px;border-left:3px solid #0055a5;font-size:9pt;overflow:auto;}
blockquote{border-left:4px solid #aaa;margin:8px 0;padding:4px 12px;background:#fafafa;color:#555;}
table{border-collapse:collapse;width:100%;margin:8px 0;}
th{background:#0055a5;color:white;padding:5px 8px;text-align:left;font-size:9pt;}
td{padding:4px 8px;border-bottom:1px solid #ddd;font-size:9pt;}
tr:nth-child(even) td{background:#f4f2ee;}
ul,ol{margin-left:18px;line-height:1.6;}
hr{border:none;border-top:1px solid #ccc;margin:16px 0;}
img{max-width:100%;display:block;margin:10px auto;}
.cover{text-align:center;padding:80px 0 40px;border-bottom:2px solid #0055a5;margin-bottom:40px;}
.cover h1{font-size:26pt;border:none;page-break-before:avoid;}
.cover .subtitle{font-size:14pt;color:#555;margin-top:8px;}
.cover .brand{font-size:11pt;color:#0055a5;margin-top:30px;font-style:italic;}
.toc{margin:20px 0;padding:16px;background:#f5f5f5;border-left:4px solid #0055a5;}
.toc h2{border:none;margin:0 0 8px;}
.toc ul{margin-left:16px;}
.toc li{line-height:1.8;}
</style>
</head><body>
<div class="cover">
  <div style="font-size:13pt;color:#0055a5;font-weight:bold;">Alfa Computers Apps</div>
  <div style="font-size:10pt;color:#888;font-style:italic;">Solutions de Gestion sur Mesure</div>
  <h1 style="margin-top:30px;">Guide Utilisateur</h1>
  <div class="subtitle">Gestion Réparation Voiture</div>
  <div class="brand">Version 1.0.0 — Juin 2026</div>
</div>

<div class="toc">
<h2>Table des matières</h2>
<ul>
<li>Introduction</li>
<li>1. Réception — Clients, Véhicules et Rendez-vous</li>
<li>2. Atelier — Dossiers de Réparation</li>
<li>3. Stock — Pièces et Fournisseurs</li>
<li>4. Facturation — Factures, Caisse et Créances</li>
<li>5. Administration</li>
<li>6. Rapports et Concepteur de Documents</li>
<li>7. Questions Fréquentes (FAQ)</li>
<li>8. Devis Commerciaux et Factures Proforma</li>
</ul>
</div>
"""
    ]

    for filename in CHAPTERS:
        md_path = GUIDE_DIR / filename
        if not md_path.exists():
            print(f"  [WARN] {filename} not found, skipping")
            continue
        markdown = md_path.read_text(encoding="utf-8")
        html = md_render(markdown, image_dir=IMG_DIR)
        # strip the <style> block from each chapter (already in head)
        import re
        html = re.sub(r"<style>.*?</style>", "", html, flags=re.DOTALL)
        parts.append(html)
        parts.append('<hr style="border:none;border-top:2px solid #e0e0e0;margin:30px 0;"/>')

    parts.append("</body></html>")
    return "\n".join(parts)


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_DIR / "Guide_Utilisateur_GarageReparation.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building combined HTML from {len(CHAPTERS)} chapters…")
    combined_html = build_combined_html()

    # Write intermediate HTML for inspection
    html_path = output.with_suffix(".html")
    html_path.write_text(combined_html, encoding="utf-8")
    print(f"  HTML: {html_path}")

    # Use Qt to print to PDF via QTextBrowser (no WebEngine required)
    print("  Converting to PDF via Qt…")
    from PyQt6.QtWidgets import QApplication, QTextBrowser
    from PyQt6.QtPrintSupport import QPrinter
    from PyQt6.QtGui import QPageLayout, QPageSize
    from PyQt6.QtCore import QMarginsF

    app = QApplication.instance() or QApplication(sys.argv)

    browser = QTextBrowser()
    browser.setHtml(combined_html)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(output))
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Unit.Millimeter)

    browser.print(printer)
    print(f"  PDF: {output}")
    print(f"\nDone! Guide saved to: {output.resolve()}")


if __name__ == "__main__":
    main()
