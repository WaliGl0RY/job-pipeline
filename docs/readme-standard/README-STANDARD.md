# README standard

How the READMEs of my repos are built. This file defines **structure**: the zone order, the components, how they're built, and how to check them. **Colours are per repo**, picked from each repo's own app (see [Palette](#6-palette-five-zone-colours-per-repo)).

The templates are in [`_readme-assets/`](_readme-assets/):

| File | What it is |
|---|---|
| `zone-strip.svg` | Zone header strip |
| `nav-pill.svg` | Nav pill for the top row |
| `phase-card.svg` | Phase card for "How it grew" |
| `label.svg` | Mini label for subsections in zones 3–5 |
| `icons.svg` | The five zone icons |
| `snippets.md` | The Markdown/HTML that places them |

In every template, `{{ZONE_BASE}}` and `{{ZONE_LIGHT}}` are the colour placeholders, and the comment block at the top lists all the others.

---

## 1. Core rules

1. **What's looked at is an image; what's used is text.**
   - Images: headers, cards, labels, screenshots.
   - Text: code, commands, settings, file trees, links, anything someone copies, searches or clicks.
2. **Every image carries its own dark card.**
   - Each SVG draws its own background (`#131016`) and a thin border.
   - It never relies on the page behind it, so it looks the same in GitHub's light and dark themes.
   - Don't use transparent backgrounds behind text.
3. **Only what GitHub renders.**
   - No CSS, no `style=` attributes, no scripts.
   - Attributes that survive: `align`, `valign`, `width`, `height`, `alt`, `name` on `<a>`.
   - SVGs are loaded as `<img>`, so they can't use web fonts or external files.
4. **Structure over decoration.** The zone strips and labels are navigation. If a component doesn't help someone find something, leave it out.
5. **The author's words stay the author's.** Drafts written for someone else are marked `[CHECK]` until the author has rewritten them (see [§ 7](#7-writing-rules)).

---

## 2. Zone order

Everything below the top block is grouped into five zones, always in this order. Each zone starts with an anchor, its header strip, and a horizontal rule before it.

| # | Zone | Anchor | Contents, in this order |
|---|---|---|---|
| — | **Top** (no strip) | — | banner (optional, per repo) · one-line pitch + `<sub>` line · shields.io badges for the real stack only · nav pills to the five zones · demo GIF or best screenshot |
| 1 | **The story** | `#story` | *Why I built it* (the author's words) · *How I built it* (honest, including AI assistance) · *How it grew*: phase cards, then a collapsed plain-text version |
| 2 | **Features** | `#features` | one intro line · screenshot grid (3×2) · one line with the remaining features · *More about each feature* as `<details>` blocks |
| 3 | **What I learned in practice** | `#learned` | one intro line · one `<details>` per concept: plain words, the smallest excerpt with one comment per line, link to the full code, *Why I did it this way* · architecture diagram in its own `<details>` |
| 4 | **Run it yourself** | `#run` | *Quick start*: at most 3 command lines, visible · then `<details>`: demo data · settings · deployment · project structure |
| 5 | **Honest notes** | `#notes` | security scope · known limitations (one line each) · license |

Headings:
- In zones 1 and 2, subsections use normal Markdown headings (`##`, `###`).
- In zones 3–5, every subsection gets a **mini label** instead: as a standalone image, or inside `<summary>`.

Adapting to a repo: a zone may shrink, but it never moves or disappears.
- **Zone 3** for a project without a course is still "what I learned": the concepts or decisions the code shows.
- **Zone 5** always exists, even if it's only the license.

---

## 3. Components

### Zone header strip · `zone-strip.svg`

- **Size:** 1200 × 84, `rx` 14. Embedded with `width="100%"`.
- **Card:** `#131016`, border `{{ZONE_BASE}}` at 45 % opacity, left-to-right gradient `{{ZONE_BASE}}` 28 % → 0 at 55 %.
- **Accent bar:** x 0, y 16, 6 × 52, `{{ZONE_BASE}}`.
- **Icon:** circle at (62, 42), r 24, fill `{{ZONE_BASE}}` 16 %, stroke 1.5. The icon strokes are `{{ZONE_LIGHT}}`, 2 px, round caps (shapes in `icons.svg`).
- **Text:**
  - zone number `01`–`05`: 12 px bold, letter-spacing 3, `{{ZONE_BASE}}`, at (106, 33)
  - title: 27 px bold, `{{ZONE_LIGHT}}`, at (104, 60)
  - subtitle: 15 px, `#b8aeb4`, right-aligned at x 1172, y 49
- **Alt text:** the zone title.

### Nav pill · `nav-pill.svg`

- **Size:** height 26, `rx` 13, card `#1c1418`, border and dot (r 4) in `{{ZONE_BASE}}`.
- **Label:** Verdana 12, `#f3e9e0`, centred.
- **Width:** `round(len(label) × 7.3 + 42)`. Verdana is wide and predictable, so a character count is enough here.
- One pill per zone, in zone order, in one centred `<p>`.

### Phase card · `phase-card.svg` (zone 1)

- **Size:** width 560, height computed, `rx` 14. Card and gradient as the strip, in the zone-1 colour.
- **Header:**
  - number pill (46 × 26, `{{ZONE_BASE}}`, white 14 px bold `01`–`08`)
  - title: 21 px bold, `#f5f0fa`
  - meta line (date · commit count): 14 px, `#a39cae`
- **Body:**
  - "what": 16 px, `#ece6f2`
  - "why": 16 px italic, `{{ZONE_LIGHT}}`, in typographic quotes
- **Wrapping:** lines are wrapped **by hand**, by measured width, max 500 px (see [§ 4](#4-fonts-and-measuring)).
- **Height:** `98 + 23 × what_lines + (12 + 23 × why_lines) + 18`, without the why part if a phase has none.
- **Equal height per row:** both cards in a table row get the taller height.
- **Placement:** a 2-column HTML table (`td width="50%" valign="top"`, image `width="100%"`), 4 rows for 8 phases. GitHub scales the cards to about 80 %, which is why the body text is 16 px.
- **Alt text:** the full card text (number, title, meta, what, why). A collapsed plain-text list of all phases follows the table.
- **Phases come from the git history.** Assign every commit to a phase. If one doesn't fit, say so instead of forcing it.

### Mini label · `label.svg` (zones 3–5)

- **Size:** height 36, `rx` 9, card `#131016`, border `{{ZONE_BASE}}` at 60 %, accent bar 4 × 20, dot r 5.
- **Text:** title 16 px bold `{{ZONE_LIGHT}}`, then subtitle 14 px `#b3aab4` as a **`<tspan dx="12">`** in the same `<text>`.
  - Never place the subtitle at a computed x. The tspan lets the browser put it right after the title, whatever font it falls back to.
- **Width:** `40 + w(title) + 12 + w("·  " + subtitle) + 20`, measured (§ 4). Title-only labels drop the subtitle part.
- **Inside `<summary>`:** add `align="absmiddle"`, so the disclosure triangle sits beside the label, not below it.
- **Alt text:** `Title · subtitle`.

### Screenshot grid (zone 2)

- **Layout:** a 3 × 2 HTML table, `td width="33%" align="center" valign="top"`. Each cell: image, `<br>`, **bold feature name**, `<br>`, `<sub>` one line (≤ about 35 characters, so it doesn't wrap).
- **Thumbnails:** all **800 × 500** (16:10), from a 1280 × 800 browser viewport. Crop close-ups to 16:10 too.
- **Six different screens:** if two thumbnails look alike, re-frame one.
- **Data:** invented only (seeded demo data), never real people.

### Top block

- **Banner (optional):** 1200 × 300, same card method, per-repo design.
- **Badges:** shields.io, the real stack only, and a license badge only if a LICENSE file exists.
- **Demo GIF:** ≤ 1 MB, 960 px wide, a caption strip per step, invented data.

---

## 4. Fonts and measuring

- **Font stack in every SVG:** `Segoe UI, -apple-system, Helvetica, Arial, sans-serif` (the nav pills use Verdana). The viewer's system picks the font, so widths differ by OS.
- **Measure every text line** with the real font files: width = the wider of Segoe UI and Arial for that size and weight, × 1.06 as a margin for Helvetica and other fallbacks. Measure bold and italic with their own font files.
- **Wrap manually** at that measured width. SVG text doesn't wrap by itself.
- **Position only the first text item** of a line at a fixed x. Anything that follows on the same line is a `<tspan>`.
- In practice this is a small script: read the texts from a JSON file, measure with Pillow's `ImageFont.getlength`, fill the templates, and apply the equal-height rule per row. Regenerating is then one command.

---

## 5. Light/dark method and checking

1. Every image has its own `#131016` card. Nothing important sits directly on the page background.
2. Text on the card:
   - titles: `{{ZONE_LIGHT}}` or near-white
   - body: `#ece6f2`
   - muted: `#a39cae` to `#b8aeb4`

   All of these are ≥ 7:1 against `#131016`.
3. **Check with GitHub's real stylesheet**, in both themes, before committing:
   - render the README with `github-markdown-css` (light **and** dark), `marked` for Markdown and Mermaid for diagrams, in a headless browser
   - screenshot the page and close-ups of the cards, labels and grid
   - check that every image's rendered aspect ratio equals its natural one (nothing clipped) and that no image is broken
4. Look at the collapsed state too. That's what GitHub shows first.

---

## 6. Palette: five zone colours per repo

The zone colours come from **the repo's own app or UI**, so the README looks like the thing it describes. Each zone needs two values:

| Value | Used for | Rule |
|---|---|---|
| `{{ZONE_BASE}}` | borders, bars, dots, number pill, zone number | saturated, contrast **≥ 4.5 : 1** against `#131016` |
| `{{ZONE_LIGHT}}` | titles, icons, "why" lines | same hue, much lighter, contrast **≥ 7 : 1** against `#131016` |

**How to pick them:**

1. **Collect the app's colours:**
   - CSS custom properties (`:root { --… }`), a Tailwind or theme config, design tokens
   - or, for an app without a theme file, the dominant colours of 3–4 screenshots
   - note the background, the primary/brand colour and any accents
2. **Anchor on the brand colour.** It goes to the zone that shows the app most directly: usually **Features**, or **The story** if the app is personal.
3. **Derive the other four hues** around the colour wheel. Either use the app's own accents, or step from the brand hue so that:
   - no two zones are closer than **25°** in hue
   - neighbouring zones are clearly different
4. **Keep the meanings where the app allows it:**
   - *Run it yourself*: green-ish (go)
   - *Honest notes*: warm, amber/orange (caution)

   These are conventions, not rules. If the brand colour already is orange, give *Honest notes* a different warm tone.
5. **Make the light tint** from each base: same hue, lightness raised to about 75–85 %, saturation kept high.
6. **Check contrast** for both values against `#131016`, and adjust lightness, not hue, until the rules in the table hold.
7. **Check in both themes** (§ 5), and write the palette into the repo, e.g. as a comment at the top of the generator script.

**Example palette (one repo, not a default).** This one was picked for a Flask tournament app whose UI is orange and gold on near-black. It isn't meant to be copied.

| Zone | Base | Light | Base contrast | Light contrast |
|---|---|---|---|---|
| 1 The story | `#8b5cf6` violet (258°) | `#c4b5fd` | 4.5 : 1 | 10.2 : 1 |
| 2 Features | `#3b82f6` blue (217°) | `#93c5fd` | 5.1 : 1 | 10.5 : 1 |
| 3 What I learned | `#06b6d4` cyan (189°) | `#67e8f9` | 7.8 : 1 | 13.0 : 1 |
| 4 Run it yourself | `#22c55e` green (142°) | `#86efac` | 8.3 : 1 | 13.4 : 1 |
| 5 Honest notes | `#f97316` orange (25°) | `#fdba74` | 6.7 : 1 | 11.2 : 1 |

---

## 7. Writing rules

- **Author texts:**
  - "Why I built it", "How I built it", every "Why I did it this way" and the security scope are in the author's own words.
  - Drafts are marked `> **[CHECK]** …`, and open `[CHECK]`s are listed in an **untracked** `TODO.md`.
  - **No merge and no push while any `[CHECK]` is left** (`git grep -n "\[CHECK\]" -- README.md`).
- **Every "why" must match the code under it.** If it doesn't, say so. Neither the text nor the code gets silently changed.
- **Concept excerpts:** the smallest real code that shows only that concept, one comment per line, then a link to the full code with line numbers.
- **Known limitations:**
  - one line each
  - security points without detail on how to exploit them
  - no promises of future work
- **Deployment:** describe what actually ran, from the repo's real config files. Don't invent settings.
- **Honest about AI assistance** in "How I built it".
- **No real people's data** anywhere: screenshots, GIFs and demo data use invented names.

---

## 8. Checklist

**Structure**
- [ ] Top block: banner (optional), pitch, real-stack badges, 5 nav pills, demo GIF
- [ ] Five zones in order, each with anchor + header strip, `---` between zones
- [ ] Zone 1: why, how, phase cards (8 or as many as the history has) + plain-text `<details>`
- [ ] Zone 2: 3×2 grid (name + one line each), remaining-features line, detail blocks
- [ ] Zone 3: concepts with excerpt, link and why; architecture in its own `<details>`
- [ ] Zone 4: quick start ≤ 3 command lines; demo data, settings, deployment, structure in `<details>`
- [ ] Zone 5: security scope, one-line limitations, license
- [ ] Zones 3–5 use mini labels, not Markdown headings; labels in `<summary>` have `align="absmiddle"`

**Build**
- [ ] Every SVG has its own `#131016` card; colours only from the repo's palette
- [ ] Text wrapped and labels sized by measured width (Segoe/Arial max × 1.06); subtitles as `<tspan>`
- [ ] Phase cards equal height per row; full alt text on every image
- [ ] Grid thumbnails all 800 × 500, six visibly different screens, invented data
- [ ] Code, commands, settings, file trees are text, never images

**Check**
- [ ] Rendered with GitHub's stylesheet in light **and** dark: no broken images, nothing clipped, labels readable
- [ ] Collapsed view looks right
- [ ] Palette contrast: base ≥ 4.5 : 1, light ≥ 7 : 1 against `#131016`
- [ ] Every "why" matches its code; deployment matches the real config
- [ ] `git grep -n "\[CHECK\]" -- README.md` returns nothing before merge or push
