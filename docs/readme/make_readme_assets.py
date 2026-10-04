"""Generate the README zone strips and subsection labels (docs/readme/zones/, docs/readme/labels/).

Follows docs/readme-standard/README-STANDARD.md. Style A: every zone opens with a header
strip; every subsection gets a pill label (chevron + title) with its subtitle under it.

Palette: one violet for every zone, taken from the dashboard's dark theme
(core/dashboard_template.html):
    ZONE_BASE  #8b8bf0  (--accent,   dark)  contrast 6.33:1 against #131016
    ZONE_LIGHT #a5a5f5  (--accent-2, dark)  contrast 8.35:1 against #131016

Text widths are measured, not guessed: headless Chrome draws every text on a canvas
in Segoe UI and in Arial; the wider of the two, x 1.06, is used (standard, section 4).
Set CHROME to the browser executable if it isn't found on PATH.

Usage: python docs/readme/make_readme_assets.py
"""
import json
import os
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "#8b8bf0"
LIGHT = "#a5a5f5"
CARD = "#131016"
MUTED_STRIP = "#b8aeb4"
MUTED_LABEL = "#b3aab4"
FONT = "Segoe UI, -apple-system, Helvetica, Arial, sans-serif"

# zone slug: (number, title, subtitle, icon paths drawn around 0,0 in a 24x24 box)
ZONES = {
    "story":    ("01", "The story", "why it exists and how it grew",
                 '<path d="M-12 -8 C-7 -10 -3 -9 0 -6 C3 -9 7 -10 12 -8 V9 C7 7 3 8 0 10 C-3 8 -7 7 -12 9 Z"/><path d="M0 -6 V10"/>'),
    "features": ("02", "Features", "search, review, tailor, track",
                 '<rect x="-11" y="-11" width="9" height="9" rx="2"/><rect x="2" y="-11" width="9" height="9" rx="2"/>'
                 '<rect x="-11" y="2" width="9" height="9" rx="2"/><rect x="2" y="2" width="9" height="9" rx="2"/>'),
    "built":    ("03", "How it's built", "guardrails and architecture",
                 '<path d="M0 -11 L11 -5 L0 1 L-11 -5 Z"/><path d="M-11 0 L0 6 L11 0"/><path d="M-11 5 L0 11 L11 5"/>'),
    "run":      ("04", "Run it yourself", "setup guide, demo data first",
                 '<rect x="-12" y="-10" width="24" height="20" rx="3"/><path d="M-7 -3 L-3 0 L-7 3"/><path d="M0 4 H6"/>'),
    "notes":    ("05", "Honest notes", "limitations, security, license",
                 '<path d="M0 -12 L10 -8 V0 C10 6 6 10 0 12 C-6 10 -10 6 -10 0 V-8 Z"/><path d="M0 -4 V3"/><path d="M0 7 V7.5"/>'),
}

# label slug: (title, subtitle)
LABELS = {
    "story-short":     ("Why and how it grew", "the short version, then the full build story"),
    "dashboard":       ("The dashboard", "review jobs, replies and next steps on one page"),
    "search":          ("Search and scoring", "two sources, few filters, every reject logged"),
    "tailoring":       ("Tailored applications (optional)", "a CV and a cover letter per job"),
    "replies":         ("Reply tracking (optional)", "invited, waiting or rejected"),
    "guardrails":      ("Guardrails", "nothing deleted, every write checked"),
    "architecture":    ("Architecture", "routines, connectors, one data folder"),
    "setup":           ("Setup guide", "requirements, your CV, connectors, scheduled tasks"),
    "limitations":     ("Known limitations", "what it doesn't do, one line each"),
    "security":        ("Security scope", "what stays on your machine and what Claude sees"),
    "license":         ("License", "for reading only, not for reuse"),
}


def find_chrome() -> str:
    for c in (os.environ.get("CHROME"), shutil.which("chrome"), shutil.which("google-chrome"),
              shutil.which("chromium"), shutil.which("msedge")):
        if c and Path(c).exists():
            return c
    raise SystemExit("No Chrome/Edge found. Set CHROME to the browser executable.")


def measure(items):
    """items: list of (text, size_px, weight) -> list of widths (max of Segoe UI and Arial, x 1.06)."""
    page = """<!doctype html><meta charset="utf-8"><pre id="out"></pre><script>
const items = %s; const c = document.createElement('canvas').getContext('2d');
const w = items.map(([t, s, wt]) => Math.max(...['"Segoe UI"', 'Arial'].map(f => { c.font = wt + ' ' + s + 'px ' + f; return c.measureText(t).width; })) * 1.06);
document.getElementById('out').textContent = JSON.stringify(w);
</script>""" % json.dumps(items)
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "measure.html"
        html.write_text(page, encoding="utf-8")
        dom = subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--dump-dom",
                              f"--user-data-dir={Path(tmp) / 'profile'}", html.as_uri()],
                             capture_output=True, text=True, timeout=120).stdout
    return json.loads(dom.split('<pre id="out">')[1].split("</pre>")[0])


def strip_svg(nn, title, subtitle, icon):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="84" viewBox="0 0 1200 84" font-family="{FONT}">
<defs>
  <linearGradient id="g" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="{BASE}" stop-opacity=".28"/><stop offset=".55" stop-color="{BASE}" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect x="0.5" y="0.5" width="1199" height="83" rx="14" fill="{CARD}" stroke="{BASE}" stroke-opacity=".45"/>
<rect x="1" y="1" width="1198" height="82" rx="14" fill="url(#g)"/>
<rect x="0" y="16" width="6" height="52" rx="3" fill="{BASE}"/>
<circle cx="62" cy="42" r="24" fill="{BASE}" fill-opacity=".16" stroke="{BASE}" stroke-width="1.5"/>
<g transform="translate(62 42)" fill="none" stroke="{LIGHT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
<text x="106" y="33" fill="{BASE}" font-size="12" font-weight="700" letter-spacing="3">{nn}</text>
<text x="104" y="60" fill="{LIGHT}" font-size="27" font-weight="700" letter-spacing="-0.3">{escape(title)}</text>
<text x="1172" y="49" fill="{MUTED_STRIP}" font-size="15" text-anchor="end">{escape(subtitle)}</text>
</svg>
'''


def label_svg(title, subtitle, w_title, w_sub):
    # pill: 14 left pad, chevron, 10 gap, title, 16 right pad
    pill_w = round(14 + 10 + 10 + w_title + 16)
    width = round(12 + max(pill_w, w_sub + 4) + 16)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="72" viewBox="0 0 {width} 72" font-family="{FONT}">
<rect x="0.5" y="0.5" width="{width - 1}" height="71" rx="12" fill="{CARD}" stroke="{BASE}" stroke-opacity=".45"/>
<rect x="12" y="10" width="{pill_w}" height="28" rx="14" fill="{BASE}" fill-opacity=".16" stroke="{BASE}" stroke-width="1.5"/>
<path d="M27 19 L32 24 L27 29" fill="none" stroke="{LIGHT}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
<text x="46" y="29.5" fill="{LIGHT}" font-size="16" font-weight="700">{escape(title)}</text>
<text x="14" y="60" fill="{MUTED_LABEL}" font-size="14">{escape(subtitle)}</text>
</svg>
'''


def main():
    items = []
    for t, s in LABELS.values():
        items += [[t, 16, "bold"], [s, 14, "normal"]]
    for _, t, s, _ in ZONES.values():
        items += [[t, 27, "bold"], [s, 15, "normal"]]
    widths = iter(measure(items))

    (HERE / "labels").mkdir(exist_ok=True)
    (HERE / "zones").mkdir(exist_ok=True)
    for slug, (t, s) in LABELS.items():
        wt, ws = next(widths), next(widths)
        (HERE / "labels" / f"{slug}.svg").write_text(label_svg(t, s, wt, ws), encoding="utf-8", newline="\n")
    for slug, (nn, t, s, icon) in ZONES.items():
        wt, ws = next(widths), next(widths)
        if 104 + wt + 40 > 1172 - ws:
            raise SystemExit(f"zone {slug}: title and subtitle would overlap")
        (HERE / "zones" / f"{slug}.svg").write_text(strip_svg(nn, t, s, icon), encoding="utf-8", newline="\n")
    print(f"OK {len(LABELS)} labels, {len(ZONES)} zone strips")


if __name__ == "__main__":
    main()
