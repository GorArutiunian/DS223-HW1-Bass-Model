"""Convert report/report_source.md into report/report.html and report/report.pdf.

The PDF is printed with headless Google Chrome; equations are rendered with MathJax.
"""

import re
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "report"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Georgia", "Times New Roman", serif; font-size: 10.5pt;
       line-height: 1.45; color: #222; max-width: 820px; margin: auto; }
h1 { font-size: 20pt; margin-bottom: 0; color: #1c4e80; }
h2 { font-size: 14pt; color: #1c4e80; border-bottom: 1px solid #ccd; padding-bottom: 2px;
     margin-top: 22px; }
h3 { font-size: 12pt; color: #333; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 8px 0 12px;
        page-break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 3px 6px; }
th { background: #eef2f7; }
img { display: block; max-width: 92%; margin: 10px auto; page-break-inside: avoid; }
a { color: #1c4e80; word-break: break-all; }
p, li { text-align: justify; }
"""

MATHJAX = """
<script>
window.MathJax = { tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] } };
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
"""


def protect_math(text):
    """Swap math for placeholders so Markdown does not touch it."""
    store = []

    def keep(rendered):
        store.append(rendered)
        return f"@@MATH{len(store) - 1}@@"

    text = text.replace(r"\$", "@@DOLLAR@@")
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(r"\[" + m.group(1) + r"\]"), text,
                  flags=re.S)
    text = re.sub(r"\$(.+?)\$", lambda m: keep(r"\(" + m.group(1) + r"\)"), text)
    return text, store


def restore_math(html, store):
    for i, rendered in enumerate(store):
        html = html.replace(f"@@MATH{i}@@", rendered)
    return html.replace("@@DOLLAR@@", "$")


def main():
    source = (REPORT / "report_source.md").read_text(encoding="utf-8")
    text, store = protect_math(source)
    body = markdown.markdown(text, extensions=["tables"])
    body = restore_math(body, store)

    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>DS 223 HW1 - Bass Model - BMW iX3</title><style>{CSS}</style>{MATHJAX}"
        f"</head><body>{body}</body></html>"
    )
    html_path = REPORT / "report.html"
    html_path.write_text(html, encoding="utf-8")

    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--virtual-time-budget=15000",
            f"--print-to-pdf={REPORT / 'report.pdf'}",
            html_path.as_uri(),
        ],
        check=True,
    )
    print(f"Wrote {REPORT / 'report.pdf'}")


if __name__ == "__main__":
    main()
