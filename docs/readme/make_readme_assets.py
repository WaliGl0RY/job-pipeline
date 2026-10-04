"""Generate every SVG the README uses (docs/readme/).

Palette: six hues (violet, blue, cyan, green, pink, amber). Each zone owns one hue and uses a
ramp of it on three clearly different levels:
    level 1  zone strip   solid bright band (HUES[h]["band"]), white text, icon
    level 2  sub-item     deep dark-tinted card (HUES[h]["deep"]) + 4px bright left bar and a round
                          numbered badge (HUES[h]["bright"]); lives inside a blockquote in the README
    level 3  detail       plain Markdown text (no SVG)
The banner and the routine cards keep their own looks (dashboard violet, Claude's dark cards).
Every SVG draws its own fixed dark card and light text, so it reads the same in GitHub's light
and dark mode. System font stack only, no web fonts, no external files.

Levels used in the README:
    level 1  zone strip      (zones/)      full width, dark card with a saturated violet gradient
    level 2  sub-item badge  (badges/)     small, lighter violet tint; placed inside a blockquote
    level 3  plain Markdown text

Text widths are estimated with a deliberately wide per-character factor, so lines wrap early
rather than overflow. Check the result in a browser after changing text.

Privacy: the routine cards show NO folder path and NO project name. Where they would be, a plain
solid grey bar is drawn; the real text is not in this file or anywhere else in the repo.

Usage: python docs/readme/make_readme_assets.py
"""
import json
import shutil
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE, LIGHT = "#8b8bf0", "#a5a5f5"     # the banner's violet (dashboard look)
HUES = {   # band: white text >= 4.5:1, deep: card fill, bright: bar + badge, light: title tint, soft: muted text
    "violet": dict(band="#6d28d9", deep="#2e1065", bright="#a78bfa", light="#c4b5fd", soft="#ddd6fe", shield="7c3aed"),
    "blue":   dict(band="#2563eb", deep="#1e3a8a", bright="#60a5fa", light="#93c5fd", soft="#bfdbfe", shield="2563eb"),
    "cyan":   dict(band="#0e7490", deep="#164e63", bright="#22d3ee", light="#67e8f9", soft="#a5f3fc", shield="0e7490"),
    "green":  dict(band="#15803d", deep="#14532d", bright="#4ade80", light="#86efac", soft="#bbf7d0", shield="15803d"),
    "pink":   dict(band="#be185d", deep="#831843", bright="#f472b6", light="#f9a8d4", soft="#fbcfe8", shield="be185d"),
    "amber":  dict(band="#b45309", deep="#78350f", bright="#fbbf24", light="#fcd34d", soft="#fde68a", shield="b45309"),
}
ZONE_HUE = {"dashboard": "violet", "demo": "pink", "search": "blue", "applications": "cyan", "replies": "green",
            "routines": "pink", "guardrails": "amber", "architecture": "violet", "use": "blue",
            "notes": "cyan", "story": "violet"}
CARD = "#131016"
FONT = "Segoe UI, -apple-system, Helvetica, Arial, sans-serif"


def tw(text, size, bold=False):
    """Conservative text width in px."""
    return len(text) * size * (0.60 if bold else 0.55)


def wrap(text, size, max_w, bold=False):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if tw(trial, size, bold) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def write(rel, content):
    p = HERE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8", newline="\n")


def svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}">\n{("<defs>" + defs + "</defs>") if defs else ""}\n{body}\n</svg>\n')


# ---------------------------------------------------------------- zone strips (level 1)
ZONES = {
    "demo":         ("01", "See it work", "a short tour of the dashboard, demo data only",
                     '<rect x="-12" y="-9" width="24" height="18" rx="3"/><path d="M-3 -4 L5 0 L-3 4 Z"/>'),
    "dashboard":    ("02", "The dashboard", "review jobs, replies and next steps on one page",
                     '<rect x="-11" y="-11" width="9" height="9" rx="2"/><rect x="2" y="-11" width="9" height="9" rx="2"/>'
                     '<rect x="-11" y="2" width="9" height="9" rx="2"/><rect x="2" y="2" width="9" height="9" rx="2"/>'),
    "search":       ("03", "Search and scoring", "two sources, few filters, every reject logged",
                     '<circle cx="-2" cy="-2" r="8"/><path d="M4 4 L11 11"/>'),
    "applications": ("04", "Applications", "optional: a CV and a cover letter per job",
                     '<path d="M-8 -11 H4 L9 -6 V11 H-8 Z"/><path d="M4 -11 V-6 H9"/><path d="M-4 0 H5"/><path d="M-4 5 H5"/>'),
    "replies":      ("05", "Replies", "optional: invited, waiting or rejected",
                     '<rect x="-12" y="-8" width="24" height="17" rx="3"/><path d="M-12 -7 L0 3 L12 -7"/>'),
    "routines":     ("06", "How it runs in Claude", "three routines, as scheduled tasks",
                     '<circle cx="0" cy="0" r="11"/><path d="M0 -6 V0 L5 3"/>'),
    "guardrails":   ("07", "Guardrails", "nothing deleted, every write checked",
                     '<path d="M0 -12 L10 -8 V0 C10 6 6 10 0 12 C-6 10 -10 6 -10 0 V-8 Z"/><path d="M-4 0 L-1 3 L4 -3"/>'),
    "architecture": ("08", "Architecture", "routines, connectors, one data folder",
                     '<path d="M0 -11 L11 -5 L0 1 L-11 -5 Z"/><path d="M-11 0 L0 6 L11 0"/><path d="M-11 5 L0 11 L11 5"/>'),
    "use":          ("09", "Use it yourself", "setup guide, demo data first",
                     '<rect x="-12" y="-10" width="24" height="20" rx="3"/><path d="M-7 -3 L-3 0 L-7 3"/><path d="M0 4 H6"/>'),
    "notes":        ("10", "Honest notes", "limitations, security, AI, license",
                     '<path d="M0 -12 L11 10 H-11 Z"/><path d="M0 -4 V2"/><path d="M0 6 V6.5"/>'),
    "story":        ("11", "The full story", "version by version, with the bugs that shaped it",
                     '<path d="M-12 -8 C-7 -10 -3 -9 0 -6 C3 -9 7 -10 12 -8 V9 C7 7 3 8 0 10 C-3 8 -7 7 -12 9 Z"/><path d="M0 -6 V10"/>'),
}


def zone_svg(slug):
    nn, title, subtitle, icon = ZONES[slug]
    h = HUES[ZONE_HUE[slug]]
    assert 104 + tw(title, 27, True) + 40 < 1172 - tw(subtitle, 15), title
    return svg(1200, 84, f'''<rect width="1200" height="84" rx="14" fill="{h["band"]}"/>
<circle cx="62" cy="42" r="24" fill="#ffffff" fill-opacity=".18"/>
<g transform="translate(62 42)" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
<text x="106" y="33" fill="#ffffff" fill-opacity=".8" font-size="12" font-weight="700" letter-spacing="3">{nn}</text>
<text x="104" y="60" fill="#ffffff" font-size="27" font-weight="700" letter-spacing="-0.3">{escape(title)}</text>
<text x="1172" y="49" fill="#ffffff" fill-opacity=".9" font-size="15" text-anchor="end">{escape(subtitle)}</text>''')


# ---------------------------------------------------------------- sub-item cards (level 2)
def item_svg(hue, n, title, muted, mono=False):
    """n = int for a numbered badge, None for a check mark."""
    h = HUES[hue]
    w = 1000
    assert tw(title, 17, True) < w - 100, title
    assert tw(muted, 14) < w - 100, muted
    badge = (f'<text x="38" y="38" text-anchor="middle" fill="{h["deep"]}" font-size="15" font-weight="700">{n}</text>' if n is not None else
             f'<path d="M30.5 32 L36 37.5 L46 26" fill="none" stroke="{h["deep"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    fam = ' font-family="Consolas, Menlo, monospace"' if mono else ""
    return svg(w, 64, f'''<rect width="{w}" height="64" rx="10" fill="{h["deep"]}"/>
<rect width="4" height="64" rx="2" fill="{h["bright"]}"/>
<circle cx="38" cy="32" r="14" fill="{h["bright"]}"/>
{badge}
<text x="68" y="29" fill="#ffffff" font-size="17" font-weight="700"{fam}>{escape(title)}</text>
<text x="68" y="50" fill="{h["soft"]}" font-size="14">{escape(muted)}</text>''')


def chips_svg(labels):
    x, parts = 2, []
    for lab in labels:
        w = round(tw(lab, 13) + 24)
        parts.append(f'<rect x="{x + .5}" y="1.5" width="{w}" height="25" rx="12.5" fill="#16161d" stroke="#6b7280"/>'
                     f'<text x="{x + w / 2 + .5}" y="18.5" text-anchor="middle" fill="#d1d5db" font-size="13">{escape(lab)}</text>')
        x += w + 8
    return svg(x, 28, "\n".join(parts))


# ---------------------------------------------------------------- banner = the dashboard
TILES = [
    ("APPLIED", "5", "each one is working for you", True),
    ("IN THE MAIL", "3", "waiting for a reply", False),
    ("INVITATIONS", "1", "start preparing!", False),
    ("OPEN CHANCES", "8", "not applied yet", False),
    ("PACKAGES READY", "2", "CV + cover letter", False),
    ("BEST MATCH", "91 %", "your strongest fit", False),
]


def banner():
    tiles = []
    tw_, th, gap, x0, y0 = 208, 100, 12, 512, 56
    for i, (lab, val, desc, hot) in enumerate(TILES):
        x, y = x0 + (i % 3) * (tw_ + gap), y0 + (i // 3) * (th + gap)
        fill = 'url(#hot)' if hot else "#26233f"
        stroke = "none" if hot else "#3d3a66"
        tl, tv, td = ("#ffffff", "#ffffff", "#f0e9ff") if hot else ("#a9a6d0", "#f2f0ff", "#a9a6d0")
        assert tw(desc, 12) < tw_ - 28, desc
        tiles.append(f'''<rect x="{x}" y="{y}" width="{tw_}" height="{th}" rx="14" fill="{fill}" stroke="{stroke}"/>
<text x="{x + 16}" y="{y + 26}" fill="{tl}" font-size="11" font-weight="700" letter-spacing="1.6">{lab}</text>
<text x="{x + 16}" y="{y + 62}" fill="{tv}" font-size="32" font-weight="700">{val}</text>
<text x="{x + 16}" y="{y + 84}" fill="{td}" font-size="12">{escape(desc)}</text>''')
    pitch = ["Find postings, score them against", "my CV, prepare applications and", "track replies. One dashboard."]
    for ln in pitch:
        assert tw(ln, 19) < 450, ln
    assert tw("Your job pipeline", 42, True) < 450
    body = f'''<rect x="0.5" y="0.5" width="1199" height="299" rx="20" fill="url(#bg)" stroke="#5a55b8" stroke-opacity=".7"/>
<circle cx="1120" cy="20" r="150" fill="#8b8bf0" fill-opacity=".07"/>
<rect x="0" y="40" width="7" height="220" rx="3.5" fill="{BASE}"/>
<text x="44" y="64" fill="{BASE}" font-size="13" font-weight="700" letter-spacing="3.5">JOB-PIPELINE</text>
<text x="42" y="124" fill="#f4f2ff" font-size="42" font-weight="700" letter-spacing="-0.5">Your job pipeline</text>
<text x="44" y="166" fill="#cdc9f0" font-size="19">{pitch[0]}</text>
<text x="44" y="192" fill="#cdc9f0" font-size="19">{pitch[1]}</text>
<text x="44" y="218" fill="#cdc9f0" font-size="19">{pitch[2]}</text>
<rect x="44" y="244" width="190" height="28" rx="14" fill="#2b2852" stroke="#6f6fd0"/>
<circle cx="62" cy="258" r="4" fill="{LIGHT}"/>
<text x="74" y="263" fill="#dcdcff" font-size="13">fictional demo data</text>
{chr(10).join(tiles)}'''
    defs = ('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#241f52"/><stop offset="1" stop-color="#14112b"/></linearGradient>'
            '<linearGradient id="hot" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5ce0"/><stop offset="1" stop-color="#b16cea"/></linearGradient>')
    write("banner.svg", svg(1200, 300, body, defs))


# ---------------------------------------------------------------- nav pills (coloured by zone hue)
PILLS = [("Story ↓", "#story", "violet", True), ("Search & scoring", "#search-and-scoring", "blue", False),
         ("Applications", "#applications", "cyan", False), ("Replies", "#replies", "green", False),
         ("Routines", "#routines", "pink", False), ("Guardrails", "#guardrails", "amber", False),
         ("Architecture", "#architecture", "violet", False), ("Use it yourself", "#use-it-yourself", "blue", False),
         ("Honest notes", "#honest-notes", "cyan", False)]


def make_pills():
    out = []
    for label, anchor, hue, filled in PILLS:
        h = HUES[hue]
        w = round(len(label) * 7.6 + 50)
        fill, stroke, col, dot = (h["band"], h["bright"], "#ffffff", "#ffffff") if filled else ("#1b1b24", h["bright"], "#f3f4f6", h["bright"])
        slug = "nav-" + label.lower().replace(" & ", "-").replace(" ↓", "").replace(" ", "-")
        write(f"nav/{slug}.svg", svg(w, 30, f'''<rect x="0.5" y="0.5" width="{w - 1}" height="29" rx="15" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
<circle cx="16" cy="15" r="4.5" fill="{dot}"/>
<text x="{26 + (w - 26) / 2}" y="20" text-anchor="middle" fill="{col}" font-size="13" font-weight="700" font-family="Verdana, {FONT}">{escape(label)}</text>'''))
        out.append((label, anchor, slug, w))
    return out


# ---------------------------------------------------------------- short version card + button
SHORT = [
    "It began on 10 July as a design where a paid model API scored every job",
    "and forms were submitted automatically. Bugs reshaped it: a blank dashboard,",
    "a stale database journal, drifting rules, silent filters.",
    "Now: agent routines around one SQLite file, no API key, a human before every application.",
]


def make_short():
    h = 66 + 28 * len(SHORT) + 18
    lines = "\n".join(f'<text x="34" y="{74 + 28 * i}" fill="#e9e7ff" font-size="18">{escape(s)}</text>' for i, s in enumerate(SHORT))
    for s in SHORT:
        assert tw(s, 18) < 1130, s
    write("short-version.svg", svg(1200, h, f'''<rect x="0.5" y="0.5" width="1199" height="{h - 1}" rx="16" fill="url(#c)" stroke="#6f6fd0"/>
<rect x="0" y="18" width="7" height="{h - 36}" rx="3.5" fill="{BASE}"/>
<text x="34" y="40" fill="{BASE}" font-size="13" font-weight="700" letter-spacing="3.5">THE SHORT VERSION</text>
{lines}''', '<linearGradient id="c" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#241f52"/><stop offset="1" stop-color="#16132e"/></linearGradient>'))
    label = "Read the full story ↓"
    w = round(len(label) * 8.6 + 48)
    write("read-full-story.svg", svg(w, 40, f'''<rect x="0.5" y="0.5" width="{w - 1}" height="39" rx="20" fill="{BASE}"/>
<text x="{w / 2}" y="26" text-anchor="middle" fill="#131016" font-size="16" font-weight="700">{label}</text>'''))


# ---------------------------------------------------------------- routine cards (Claude scheduled-tasks look)
GREY = "#6b6b68"   # the solid grey bar that stands where a path / project name would be
CLAUDE = {"bg": "#2b2a28", "border": "#3f3e3a", "title": "#f5f4ef", "desc": "#b9b7af"}


def badge_pill(x, y, text, fill, col, dot=None, border=None):
    w = round(tw(text, 13) + 26 + (16 if dot else 0))
    s = f'<rect x="{x}" y="{y}" width="{w}" height="26" rx="13" fill="{fill}"' + (f' stroke="{border}"' if border else "") + "/>"
    tx = x + 13
    if dot:
        s += f'<circle cx="{x + 15}" cy="{y + 13}" r="4" fill="{dot}"/>'
        tx += 16
    s += f'<text x="{tx}" y="{y + 18}" fill="{col}" font-size="13" font-weight="600">{escape(text)}</text>'
    return s, w


def folder_bar(right, y):
    bar_w = 130
    x = right - bar_w
    return (f'<path d="M{x - 26} {y + 4} h7 l2 3 h9 a2 2 0 0 1 2 2 v10 a2 2 0 0 1 -2 2 h-18 a2 2 0 0 1 -2 -2 z" fill="{GREY}"/>'
            f'<rect x="{x}" y="{y + 5}" width="{bar_w}" height="16" rx="8" fill="{GREY}"/>')


def routine_card(slug, title, desc_lines, badges, path_bar_in_desc=None):
    """desc_lines: list of str. If path_bar_in_desc is an index, that line is drawn as
    'text before' + grey bar + 'text after' (the tuple form) instead of plain text."""
    w, h = 1000, 64 + 24 * len(desc_lines) + 64
    parts = [f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="{CLAUDE["bg"]}" stroke="{CLAUDE["border"]}"/>',
             f'<text x="28" y="44" fill="{CLAUDE["title"]}" font-size="21" font-weight="700">{escape(title)}</text>']
    y = 78
    for ln in desc_lines:
        if isinstance(ln, tuple):      # (text, grey_bar_width, text_after)
            before, bw, after = ln
            parts.append(f'<text x="28" y="{y}" fill="{CLAUDE["desc"]}" font-size="15">{escape(before)}</text>')
            x = 28 + tw(before, 15) + 8
            parts.append(f'<rect x="{x:.0f}" y="{y - 13}" width="{bw}" height="16" rx="8" fill="{GREY}"/>')
            parts.append(f'<text x="{x + bw + 6:.0f}" y="{y}" fill="{CLAUDE["desc"]}" font-size="15">{escape(after)}</text>')
            assert x + bw + 6 + tw(after, 15) < w - 30
        else:
            assert tw(ln, 15) < w - 60, ln
            parts.append(f'<text x="28" y="{y}" fill="{CLAUDE["desc"]}" font-size="15">{escape(ln)}</text>')
        y += 24
    bx, by = 28, h - 46
    for spec in badges:
        s, bw_ = badge_pill(bx, by, **spec)
        parts.append(s)
        bx += bw_ + 10
    parts.append(folder_bar(w - 28, by))
    write(f"routines/{slug}.svg", svg(w, h, "\n".join(parts)))


AMBER = dict(text="Only on this computer", fill="#4a3514", col="#f0b954", border="#7a5a1f")


def make_routines():
    routine_card("search-jobs", "Search jobs",
                 ["Search new Werkstudent jobs via BOTH Apify LinkedIn + Indeed MCP (10-day window,",
                  "wide sweep), score vs CV snapshot, insert >=50% into jobs.db, rebuild dashboard"],
                 [AMBER])
    routine_card("process-tailor-queue", "Process tailor queue",
                 ["Generate tailored German CV + Motivationsschreiben packages for queued jobs,",
                  "apply queued status changes, refresh dashboard data"],
                 [AMBER])
    routine_card("scan-mail-status", "Scan mail status",
                 ["You maintain the job-application mail status for the project at",
                  ("", 150, ". Do exactly this, self-contained: 1. Read the job list from the SQLite DB…")],
                 [dict(text="Paused", fill="#3a3936", col="#c9c7bf", border="#55534e"),
                  dict(text="Requires your computer", fill="#34332f", col="#d6d4cc", dot="#4ade80", border="#55534e")])


# ---------------------------------------------------------------- story version headings
def make_versions():
    h = HUES["violet"]
    data = json.loads((HERE / "story-versions.json").read_text(encoding="utf-8"))
    for slug, (tag, when, title) in data.items():
        tagw = round(tw(tag, 13, True) + 22)
        w = 1000
        assert 14 + tagw + 12 + tw(when, 13) + 18 + tw(title, 16, True) < w - 20, slug
        body = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="35" rx="10" fill="#1a1a22" stroke="{h["bright"]}" stroke-opacity=".7"/>'
                f'<rect x="10" y="6" width="{tagw}" height="24" rx="12" fill="{h["bright"]}"/>'
                f'<text x="{10 + tagw / 2}" y="23" text-anchor="middle" fill="{h["deep"]}" font-size="13" font-weight="700">{escape(tag)}</text>'
                f'<text x="{10 + tagw + 14}" y="23" fill="#9ca3af" font-size="13">{escape(when)}</text>'
                f'<text x="{10 + tagw + 14 + tw(when, 13) + 16:.0f}" y="23" fill="#f3f4f6" font-size="16" font-weight="700">{escape(title)}</text>')
        write(f"story/{slug}.svg", svg(w, 36, body))


def clean():
    for d in ("zones", "badges", "nav", "story", "routines", "labels", "items"):
        shutil.rmtree(HERE / d, ignore_errors=True)


def main():
    clean()
    for slug in ZONES:
        write(f"zones/{slug}.svg", zone_svg(slug))
    banner()
    make_pills()
    make_short()
    make_routines()
    if (HERE / "story-versions.json").exists():
        make_versions()
    print("OK")


if __name__ == "__main__":
    main()
