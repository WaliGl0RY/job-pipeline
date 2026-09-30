# README snippets

Copy-ready Markdown/HTML for the components in `README-STANDARD.md`. Paths are relative to the repo root, and all images live under `docs/`. `{{…}}` marks what you fill in.

## Nav row (top, after the badges)

```html
<p align="center">
  <a href="#story"><img src="docs/badges/zone-story.svg" alt="The story"></a>
  <a href="#features"><img src="docs/badges/zone-features.svg" alt="Features"></a>
  <a href="#learned"><img src="docs/badges/zone-learned.svg" alt="What I learned in practice"></a>
  <a href="#run"><img src="docs/badges/zone-run.svg" alt="Run it yourself"></a>
  <a href="#notes"><img src="docs/badges/zone-notes.svg" alt="Honest notes"></a>
</p>
```

## Start of a zone (anchor + header strip), and the rule between zones

```html
<a name="features"></a>
<p><img src="docs/zones/features.svg" alt="Features" width="100%"></p>
```

Between two zones, a blank line, `---`, and a blank line. The blank line before `---` matters: without it, Markdown turns the paragraph above into a heading.

## Phase cards (zone 1, "How it grew"): 2 columns, 4 rows

```html
<table>
  <tr>
    <td width="50%" valign="top"><img src="docs/story/phase-01.svg" alt="Phase 01: {{TITLE}}. {{META}}. {{WHAT}} Why: “{{WHY}}”" width="100%"></td>
    <td width="50%" valign="top"><img src="docs/story/phase-02.svg" alt="Phase 02: …" width="100%"></td>
  </tr>
  <!-- three more rows -->
</table>

<details>
<summary>The 8 phases as plain text</summary>

- **01 · {{TITLE}}** ({{META}}). {{WHAT}} *“{{WHY}}”*
- …

</details>
```

## Screenshot grid (zone 2): 3 columns, 2 rows

```html
<table>
  <tr>
    <td width="33%" align="center" valign="top"><img src="docs/screenshots/grid/{{slug}}.png" alt="{{Feature name}}"><br><b>{{Feature name}}</b><br><sub>{{one short line}}</sub></td>
    <!-- two more cells -->
  </tr>
  <tr>
    <!-- three cells -->
  </tr>
</table>
```

## Mini label as a subsection heading (zones 3–5)

```html
<a name="{{anchor}}"></a>
<p><img src="docs/labels/{{slug}}.svg" alt="{{Title}}"></p>
```

## Mini label inside a collapsible section (zones 3–5)

```html
<details>
<summary><img src="docs/labels/{{slug}}.svg" align="absmiddle" alt="{{Title}} · {{subtitle}}"></summary>
<br>

Content. Leave the blank line above, or Markdown inside <details> isn't rendered.

</details>
```

## Author-text marker

```markdown
> **[CHECK]** *Draft, rewrite in your own words:* …
```
