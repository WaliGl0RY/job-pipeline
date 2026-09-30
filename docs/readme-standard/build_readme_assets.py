"""Generate the README images (zone strips, nav pills, labels, phase cards).

Run from the repo root:  python docs/readme-standard/build_readme_assets.py
Needs Pillow (only for measuring text) and the Liberation Sans fonts (Arial metrics).

Palette: taken from the dashboard's own dark theme (core/dashboard_template.html,
`:root[data-theme="dark"]`). Every image draws its own card in the dashboard's dark
background, so it reads the same in GitHub's light and dark themes.

    card / dashboard --bg  #13141c   raised card  #1c1d29 (--surface)
    text  #e6e6f0 (--ink)   muted  #b0b1c8 (--dim #9a9bb4, lifted to reach 7:1)

    zone         hue   base (borders, bars, dots)   light (titles, icons, "why")
    1 story      331   #e85d9e  --g-coral start      #f5a3ca
    2 features   240   #8b8bf0  --accent (brand)     #c2c2fa
    3 learned    277   #b16cea  --g-violet end       #d9b6f6
    4 run        155   #5fce9b  --invite (go)        #a9ecce
    5 notes       39   #e0a94f  --wait (caution)     #f2d08e

Contrast against #13141c is asserted at the bottom of the palette section:
base >= 4.5:1, light and text >= 7:1. Change a colour and the script tells you.
"""
import re
import sys
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
CARD, SURFACE, INK, MUTED = "#13141c", "#1c1d29", "#e6e6f0", "#b0b1c8"

ZONES = {
    "story":    dict(nn="01", base="#e85d9e", light="#f5a3ca", title="The story",
                     nav="The story", sub="why I built it, how it grew"),
    "features": dict(nn="02", base="#8b8bf0", light="#c2c2fa", title="Features",
                     nav="Features", sub="what the pipeline does for a job search"),
    "learned":  dict(nn="03", base="#b16cea", light="#d9b6f6", title="What I learned in practice",
                     nav="What I learned", sub="the ideas the code shows"),
    "run":      dict(nn="04", base="#5fce9b", light="#a9ecce", title="Run it yourself",
                     nav="Run it yourself", sub="demo data in three commands"),
    "notes":    dict(nn="05", base="#e0a94f", light="#f2d08e", title="Honest notes",
                     nav="Honest notes", sub="scope, limits, license"),
}

ICONS = {
    "story": '<path d="M-12 -8 C-7 -10 -3 -9 0 -6 C3 -9 7 -10 12 -8 V9 C7 7 3 8 0 10 C-3 8 -7 7 -12 9 Z"/><path d="M0 -6 V10"/>',
    "features": '<rect x="-11" y="-11" width="9" height="9" rx="2"/><rect x="2" y="-11" width="9" height="9" rx="2"/><rect x="-11" y="2" width="9" height="9" rx="2"/><rect x="2" y="2" width="9" height="9" rx="2"/>',
    "learned": '<path d="M-5 5 C-5 1 -9 -1 -9 -5 A9 9 0 0 1 9 -5 C9 -1 5 1 5 5 Z"/><path d="M-4 9 H4"/><path d="M-2 12 H2"/>',
    "run": '<rect x="-12" y="-10" width="24" height="20" rx="3"/><path d="M-7 -3 L-3 0 L-7 3"/><path d="M0 4 H6"/>',
    "notes": '<path d="M0 -12 L10 -8 V0 C10 6 6 10 0 12 C-6 10 -10 6 -10 0 V-8 Z"/><path d="M0 -4 V3"/><path d="M0 7 V7.5"/>',
}

# Labels for zones 3-5: (file slug, zone, title, subtitle)
LABELS = [
    ("hash-gate", "learned", "Hash-gated CV snapshot", "read the CV only when it changes"),
    ("verified-writes", "learned", "Verified writes", "write, checksum, re-read"),
    ("self-checking-build", "learned", "A build that checks itself", "prints OK or BUILD FAILED"),
    ("copy-to-chat", "learned", "Copy to chat", "the dashboard can't write"),
    ("dedupe", "learned", "Dedupe on identity", "company + title, not the URL"),
    ("architecture", "learned", "Architecture", "routines, connectors, one data folder"),
    ("demo-data", "run", "Demo data", "15 fictional jobs"),
    ("settings", "run", "Settings", "search terms, filters, threshold"),
    ("deployment", "run", "Deployment", "three scheduled tasks and one artifact"),
    ("structure", "run", "Project structure", "where everything lives"),
    ("scope", "notes", "Security scope", "what it protects and what it doesn't"),
    ("limitations", "notes", "Known limitations", "one line each"),
    ("license", "notes", "License", ""),
]

# Phases come from STORY.md: the public git history is three commits, so the private
# build history (dated notes) is the only record of how it grew.
PHASES = [
    ("The design with a model bill", "10–13 Jul 2026 · fixes 1–6",
     "SQLite for tracking, a scraper for job boards and a paid model API scoring every posting, with automatic form submission.",
     "Every score cost money and nothing checked an application before it left."),
    ("Scoring moves into the agent", "14–16 Jul 2026 · fixes 7–12",
     "A scheduled task, a CV snapshot gated by a sha256 hash, and a reliability layer of checksummed writes and a self-checking build.",
     "Two failures on one day, a stale journal and a truncated template, taught that a write is not done until it is read back."),
    ("One file holds the rules", "16–19 Jul 2026 · fixes 13–16",
     "The tailoring rules moved into a single routine file after a scheduled task ran on an outdated copy and produced 16 four-page CVs.",
     "Rules that live in two places drift; the task now only points to the file."),
    ("Dashboard v3, copy to chat", "24–30 Jul 2026 · fixes 17–22",
     "Four tabs and a detail panel. The live bridge to Claude had never been connected, so copying a prompt became the design.",
     "A page with no write access is one you can trust, and nothing on it depends on a runtime feature."),
    ("Cast wide, then score", "5 Aug 2026 · fixes 23–31",
     "The best-fitting posting of the search was dropped by silent filters. Exclusions became demotions and every reject is logged.",
     "You can't judge a posting you never see."),
    ("The public version", "27–28 Sep 2026 · fixes 32–33",
     "The bridge code came out, the interface went English, and the output language became a setting.",
     "What ships should be what actually runs."),
]

# ---------------------------------------------------------------- measuring
_FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
_FILES = {("n", False): "LiberationSans-Regular.ttf", ("b", False): "LiberationSans-Bold.ttf",
          ("n", True): "LiberationSans-Italic.ttf", ("b", True): "LiberationSans-BoldItalic.ttf"}
_cache = {}


def width(text, size, bold=False, italic=False):
    """Arial-metric width x 1.06 margin (Segoe UI is narrower, Helvetica about equal)."""
    key = ("b" if bold else "n", italic, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(str(_FONT_DIR / _FILES[key[:2]]), size * 10)
    return _cache[key].getlength(text) / 10 * 1.06


def wrap(text, size, max_w, **kw):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and width(trial, size, **kw) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- contrast
def _lum(hex_):
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b=CARD):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_palette():
    bad = []
    for name, z in ZONES.items():
        if contrast(z["base"]) < 4.5:
            bad.append(f"{name} base {z['base']} {contrast(z['base']):.1f}:1 < 4.5")
        if contrast(z["light"]) < 7:
            bad.append(f"{name} light {z['light']} {contrast(z['light']):.1f}:1 < 7")
    for c in (INK, MUTED):
        if contrast(c) < 7:
            bad.append(f"text {c} {contrast(c):.1f}:1 < 7")
    if bad:
        sys.exit("palette fails contrast:\n  " + "\n  ".join(bad))
    print("palette OK:", ", ".join(f"{n} {contrast(z['base']):.1f}/{contrast(z['light']):.1f}" for n, z in ZONES.items()))


# ---------------------------------------------------------------- templates
FONT = "Segoe UI, -apple-system, Helvetica, Arial, sans-serif"


def zone_strip(key):
    z = ZONES[key]
    b, l = z["base"], z["light"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="84" viewBox="0 0 1200 84" font-family="{FONT}">
<title>{esc(z["title"])}</title>
<defs>
  <linearGradient id="g" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="{b}" stop-opacity=".28"/><stop offset=".55" stop-color="{b}" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect x="0.5" y="0.5" width="1199" height="83" rx="14" fill="{CARD}" stroke="{b}" stroke-opacity=".45"/>
<rect x="1" y="1" width="1198" height="82" rx="14" fill="url(#g)"/>
<rect x="0" y="16" width="6" height="52" rx="3" fill="{b}"/>
<circle cx="62" cy="42" r="24" fill="{b}" fill-opacity=".16" stroke="{b}" stroke-width="1.5"/>
<g transform="translate(62 42)" fill="none" stroke="{l}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[key]}</g>
<text x="106" y="33" fill="{b}" font-size="12" font-weight="700" letter-spacing="3">{z["nn"]}</text>
<text x="104" y="60" fill="{l}" font-size="27" font-weight="700" letter-spacing="-0.3">{esc(z["title"])}</text>
<text x="1172" y="49" fill="{MUTED}" font-size="15" text-anchor="end">{esc(z["sub"])}</text>
</svg>
'''


def nav_pill(key):
    z = ZONES[key]
    label = z["nav"]
    w = round(len(label) * 7.3 + 42)
    tx = 26 + (len(label) * 7.3 + 2) / 2
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="26" viewBox="0 0 {w} 26" font-family="Verdana, DejaVu Sans, sans-serif" font-size="12">
<title>{esc(label)}</title>
<rect x=".5" y=".5" width="{w - 1}" height="25" rx="13" fill="{SURFACE}" stroke="{z["base"]}"/>
<circle cx="15" cy="13" r="4" fill="{z["base"]}"/><text x="{tx:.1f}" y="17.5" fill="{INK}" text-anchor="middle">{esc(label)}</text></svg>
'''


def mini_label(key, title, sub):
    z = ZONES[key]
    w = 40 + width(title, 16, bold=True) + (12 + width("·  " + sub, 14) if sub else 0) + 20
    w = round(w)
    subtspan = (f'<tspan dx="12" fill="{MUTED}" font-size="14" font-weight="400">·  {esc(sub)}</tspan>' if sub else "")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="36" viewBox="0 0 {w} 36" font-family="{FONT}">
<title>{esc(title + (" · " + sub if sub else ""))}</title>
<rect x="0.5" y="0.5" width="{w - 1}" height="35" rx="9" fill="{CARD}" stroke="{z["base"]}" stroke-opacity=".6"/>
<rect x="0" y="8" width="4" height="20" rx="2" fill="{z["base"]}"/>
<circle cx="24" cy="18" r="5" fill="{z["base"]}"/>
<text x="40" y="24"><tspan fill="{z["light"]}" font-size="16" font-weight="700">{esc(title)}</tspan>{subtspan}</text>
</svg>
'''


def phase_lines(i):
    title, meta, what, why = PHASES[i]
    return wrap(what, 16, 500), wrap("“" + why + "”", 16, 500, italic=True)


def phase_height(i):
    what, why = phase_lines(i)
    return 98 + 23 * len(what) + (12 + 23 * len(why)) + 18


def phase_card(i, h):
    z = ZONES["story"]
    b, l = z["base"], z["light"]
    title, meta, _, _ = PHASES[i]
    what, why = phase_lines(i)
    assert width(title, 21, bold=True) <= 440, f"phase title too wide: {title}"
    y = 104
    out = []
    for line in what:
        out.append(f'<text x="30" y="{y}" fill="{INK}" font-size="16">{esc(line)}</text>')
        y += 23
    y += 12  # gap after the last what line; y is now the first why baseline
    for line in why:
        out.append(f'<text x="30" y="{y}" fill="{l}" font-size="16" font-style="italic">{esc(line)}</text>')
        y += 23
    alt = f"Phase {i + 1:02d}: {title}. {meta}. " + " ".join(what) + " Why: " + " ".join(why)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="{h}" viewBox="0 0 560 {h}" font-family="{FONT}">
<title>{esc(alt)}</title>
<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="{b}" stop-opacity=".22"/><stop offset=".6" stop-color="{b}" stop-opacity="0"/></linearGradient></defs>
<rect x="0.5" y="0.5" width="559" height="{h - 1}" rx="14" fill="{CARD}" stroke="{b}" stroke-opacity=".45"/>
<rect x="1" y="1" width="558" height="{h - 2}" rx="14" fill="url(#g)"/>
<rect x="0" y="18" width="5" height="{min(52, h - 36)}" rx="2.5" fill="{b}"/>
<rect x="30" y="24" width="46" height="26" rx="13" fill="{b}"/>
<text x="53" y="42" fill="{CARD}" font-size="14" font-weight="700" text-anchor="middle" letter-spacing="1">{i + 1:02d}</text>
<text x="90" y="44" fill="{INK}" font-size="21" font-weight="700">{esc(title)}</text>
<text x="30" y="74" fill="{MUTED}" font-size="14">{esc(meta)}</text>
{chr(10).join(out)}
</svg>
'''


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == text


def main():
    check_palette()
    for key in ZONES:
        write(DOCS / "zones" / f"{key}.svg", zone_strip(key))
        write(DOCS / "badges" / f"zone-{key}.svg", nav_pill(key))
    for slug, key, title, sub in LABELS:
        write(DOCS / "labels" / f"{slug}.svg", mini_label(key, title, sub))
    heights = [phase_height(i) for i in range(len(PHASES))]
    for row in range(0, len(PHASES), 2):
        h = max(heights[row:row + 2])
        for i in range(row, min(row + 2, len(PHASES))):
            write(DOCS / "story" / f"phase-{i + 1:02d}.svg", phase_card(i, h))
    print("wrote", len(ZONES) * 2 + len(LABELS) + len(PHASES), "SVGs")


if __name__ == "__main__":
    main()
