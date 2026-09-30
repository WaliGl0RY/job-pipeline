"""Build README.md from the content below and regenerate every SVG it uses.

Usage: python docs/readme/build_readme.py
(the GIF is recorded separately with docs/readme/record_tour.py)
"""
import json
import re
import sys
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import make_readme_assets as M  # noqa: E402

MERMAID = "```mermaid\n" + (HERE / "architecture.mmd").read_text(encoding="utf-8").rstrip() + "\n```"


def inline(t):
    t = re.sub(r"`([^`]+)`", lambda m: "<code>" + escape(m.group(1)) + "</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def bq(lines):
    return "\n".join(("> " + l) if l else ">" for l in lines)


_count = {}


def rows(zone_slug, items, first=1, check=False):
    """Level 2: one SVG card per item (deep tint, bright bar, round badge), inside a blockquote.
    item = (title, muted, detail|None, link|None, mono). Level 3 = the optional detail text."""
    hue = M.ZONE_HUE[zone_slug]
    out = []
    for i, it in enumerate(items):
        title, muted, detail = it[0], it[1], it[2]
        link = it[3] if len(it) > 3 and it[3] else "#" + ANCHOR[zone_slug]
        mono = len(it) > 4 and it[4]
        k = _count[zone_slug] = _count.get(zone_slug, 0) + 1
        num = None if check else first + i
        M.write(f"items/{zone_slug}-{k}.svg", M.item_svg(hue, num, title, muted, mono))
        alt = f"{num if num else 'check'}. {title}: {muted}"
        out.append(f'<a href="{link}"><img src="docs/readme/items/{zone_slug}-{k}.svg" alt="{escape(alt)}" width="100%"></a>')
        if detail:
            out.append("")
            out.append(f"<sub>{inline(detail)}</sub>")
        out.append("")
    return bq(out[:-1])


def plain_list(items):
    return bq([""] + [f"- <sub>{inline(t)}</sub>" for t in items])


ANCHOR = {"demo": "see-it-work", "dashboard": "dashboard", "search": "search-and-scoring", "applications": "applications",
          "replies": "replies", "routines": "routines", "guardrails": "guardrails", "architecture": "architecture",
          "use": "use-it-yourself", "notes": "honest-notes", "story": "the-story"}


def zone(slug, alt):
    a = ANCHOR[slug]
    return (f'---\n\n<a name="{a}"></a>\n<p><a href="#{a}"><img src="docs/readme/zones/{slug}.svg" '
            f'alt="{alt}" width="100%"></a></p>\n')


# ------------------------------------------------------------------ story data
def card(rows_):
    t = ["<table>"]
    for lab, txt in rows_:
        t.append(f'<tr><td width="150" valign="top"><b>{lab}</b></td><td valign="top">{inline(txt)}</td></tr>')
    t.append("</table>")
    return t


BUILT, BUG, FIX = "What I built", "The bug that shipped", "The fix"
L = lambda items: "<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>"

THREADS = [
    ("Job search", "from a paid-API script to a scheduled task and \"cast wide, then score\"", [
        ("js-v0", "v0", "10 July", "A design with a model bill", [
            (BUILT, "A scraping service for job boards, browser automation that would fill in and submit application forms, and SQLite for tracking. A Python analyzer sent every job description to a paid model API for scoring, with a table assigning a model tier to each task by cost and speed. Without an API key it fell back to counting how many known skills appeared in the text."),
            (BUG, "Every scored job cost money, the fallback was crude, and automatic submission meant no human check before an application went out."),
            (FIX, "Automatic submission was dropped, and scoring moved into the agent.")]),
        ("js-v1", "v1", "around 11–12 July", "A slash command", [
            (BUILT, "A <code>/job-search</code> command ran the scraping actor and the Indeed connector (the second one optional), with four search terms, a 30-day window, and a job-function filter set inside the scraper. The agent scored each job against a separate JSON profile file, assigned tiers, and wrote a markdown digest."),
            (BUG, "The profile file was separate from the CV and had to be kept in sync, and the scoring script with its paid API was still in the project."),
            (FIX, "See v2.")]),
        ("js-v2", "v2", "14 July", "A scheduled task and a CV snapshot", [
            (BUILT, "The search became a scheduled task. The profile file and the scoring script were retired. Claude reads the master CV once and stores a skills snapshot plus the CV's sha256 hash; every run compares the hash first and re-reads the CV only when it has changed. Scoring happens in the agent turn, with no API call. On 16 July jobs below a match-score threshold stopped being inserted; on 24 July the threshold was raised to 50 and two narrow search queries were added.")]),
        ("js-v3", "v3", "5 August", "\"Cast wide, then score\"", [
            (BUG, "One of the best-fitting postings of the whole search, an AI and data-analysis role filed under an after-sales department, was missed for a full cycle. Three things caused it at once: search terms with technology words that its title didn't contain, the job-function filter inside the scraper (the role wasn't filed under IT), and a bare \"sales\" in the exclusion list. Separately, Indeed's short links turned out to change on every request, so URL-only deduplication would have inserted six duplicates in one run, and postings found late in a 30-day window were often already closed."),
            (FIX, L(["Both sources became mandatory; a source that fails or returns nothing makes the whole run a failure, reported first.",
                     "Bare employment-type terms for the broad source, many narrow queries for Indeed.",
                     "No filters inside the scraper.",
                     "The employment type is checked in title **and** description, because titles can come back truncated.",
                     "Exclusion became a demotion: override words send a posting to scoring anyway.",
                     "Every rejected posting is logged with a reason.",
                     "Deduplication on normalised company + title as well as URL.",
                     "Scoring judges the work described, not the department.",
                     "The window went from 30 to 10 days, and the scraper's input was checked against its live schema."]))]),
    ], "**27 September.** The old slash command was archived; the scheduled task is the only way the search runs."),

    ("CV tailoring", "from one sentence in a prompt to one routine with a quality bar", [
        ("cv-v0", "v0", "10–12 July", "A sentence in a prompt", [
            (BUILT, "The first dashboard prompts described tailoring in one line: a CV built from the master, with sections emphasised per job type from a small mapping file. On 12 July the note was to agree on how tailoring should work before generating more packages.")]),
        ("cv-v1", "v1", "13 July", "Rules from reviewing drafts", [
            (BUILT, "A <code>/job-tailor</code> command set the basics: a hard two-page limit on the tailored CV, content chosen per posting as a judgment call, a rewritten intro, and one \"wildcard\" line unrelated to the job."),
            (FIX, "Reviewing the first drafts produced six corrections the same day:" + L([
                "the master CV stays complete; only the tailored copy is cut;",
                "no \"(completed)\" labels on certificates, only \"in progress\" where it applies;",
                "no \"with a focus on X\" framing in the intro;",
                "no dashes as sentence connectors and no salesy phrasing;",
                "nested items as bold name + colon instead of italics + dash;",
                "the intro as several short sentences in a fixed order: status, relevant experience, interests, languages."]))]),
        ("cv-drift", "drift", "16–17 July", "The scheduled task never got the rules", [
            (BUG, "The scheduled tailoring task had never received the 13 July rules; only the slash command had them. Its run on 16 July produced 16 packages of about four pages each (the master CV with a new intro) and cover letters as PDF instead of Word."),
            (FIX, "The full rule set was written into the task, including a compile-and-count-pages loop, and all 16 packages were redone.")]),
        ("cv-v3", "v3", "18 July", "Nine passes on one CV", [
            (BUILT, "Working through one CV pass by pass added most of today's layout and wording rules:" + L([
                "certificates and skills as separate sections, certificate details taken from the actual certificate documents;",
                "every heading + bullet list in an unbreakable block, after a block split across a page in a rendered PDF;",
                "the concrete technology in each bullet in bold;",
                "the intro as a recruiter summary: no course references, no sentences with an implied third-person subject, no parentheses;",
                "certificates in the same heading format as education;",
                "skills as a two-column grid with no orphan single-column row;",
                "no skill phrase repeated in both the skills section and a project;",
                "hyphenation off and lists ragged-right, margins 1.5 cm;",
                "full terms instead of abbreviations a non-technical reader might not know;",
                "a sweep that replaced explanatory dashes with colons."])),
            (BUG, "Every block after the first in a section had a small indent, which misaligned titles and dates. It was found by measuring a rendered PDF."),
            (FIX, "<code>\\noindent</code> in the block definition.")]),
        ("cv-v4", "v4", "19 July", "One routine with a quality bar", [
            (BUILT, "The rules were consolidated into one routine file with an explicit goal: every CV must be readable by applicant-tracking systems (real text, clean reading order, standard headings) and pass a recruiter's few-second skim. Three finished packages became the reference. New checks after compiling: extract the text to confirm the reading order, and render each page to confirm no block was cut.")]),
        ("cv-v5", "v5", "29 July", "One copy of the rules", [
            (FIX, "The scheduled task stopped carrying its own copy of the rules. It now only points to the routine file and reads it at the start of every run.")]),
        ("cv-v6", "v6", "30 July", "Naming and the template itself", [
            (BUG, "The master CV's own preamble had drifted from the 19 July typography rules (old margins, hyphenation on, no <code>\\noindent</code>). One package's intro still named courses."),
            (FIX, "The preamble was fixed at the source, the PDF is named after the company instead of a generic file name, and the intro was rewritten.")]),
        ("cv-aug", "rule", "17 August", "No claimed specialization", [
            (BUG, "A wording was rejected during an interview simulation."),
            (FIX, "Never claim a specialization, focus or qualification that isn't in the CV; describe interests as interests.")]),
        ("cv-sep", "public", "29–30 September", "The public version", [
            (BUILT, "Abbreviations changed from \"write them out\" to \"full term with the abbreviation in brackets the first time, then the abbreviation only\", and the output language became a config setting.")]),
    ], None),

    ("Motivation letter", "from half a page of LaTeX to an editable Word letter with a plain structure", [
        ("ml-v0", "v0", "10–12 July", "Half a page from the posting", [
            (BUILT, "The first prompts asked for a letter of about half a page that referred to concrete tasks from the description and mapped them to the profile, written as LaTeX and compiled to PDF.")]),
        ("ml-v1", "v1", "13 July (morning)", "Letters in a script", [
            (BUILT, "The first batch of letters was written as fixed paragraph lists per company inside a generator script and built into Word files. Each followed the same pattern: why this role, two projects as proof, a planned future course as outlook, availability plus a note that a transcript was attached.")]),
        ("ml-v2", "v2", "13 July", "Editable Word files and a four-part schema", [
            (BUILT, "The letter became a native <code>.docx</code>, because it gets edited by hand before sending. One application (CV and letter together) went through six versions that day. For the letter, the changes were: leading with the most relevant course, the Word format, rewording a start date that could be read as an end date, and finally a simpler four-part schema without the dense keyword listing. That schema became the standard: interest in the role, what was learned in a course and how it connects to a project, a broader interest tied to a future elective, availability.")]),
        ("ml-drift", "drift", "17 July", "The same drift as the CVs", [
            (BUG, "The 16 July run had shipped letters as PDF/LaTeX."),
            (FIX, "They were regenerated as Word files.")]),
        ("ml-v3", "v3", "18 July", "The schema is replaced", [
            (FIX, "The four-part schema was dropped. The new structure: an opening with concrete matching skills and no filler, a middle with one completed-course proof point and one project, an honest sentence where a required skill is missing, and a closing with availability only (no remote/on-site remarks, no transcript unless asked).")]),
        ("ml-v4", "v4", "19 July", "Simpler language and more motivation", [
            (BUG, "Feedback on the language level, and on letters that mainly talked about courses."),
            (FIX, L(["everyday language with short sentences;",
                     "research the company first and open with one specific, true connection;",
                     "a short narrative with one or two proof points instead of a list of courses;",
                     "only completed courses as proof;",
                     "the earlier reference letters were retired."]))]),
        ("ml-aug", "rule", "17 August", "No claimed specialization", [
            (FIX, "The no-specialization rule applies to letters too.")]),
        ("ml-sep", "public", "29–30 September", "The public version", [
            (BUILT, "Written down as explicit rules: name 2–3 concrete tasks from the posting, greet a named contact person by name, write start dates so they can't be read as end dates, abbreviations in full the first time, and the output language as a setting.")]),
    ], None),

    ("Dashboard", "from a data layer to a page that copies prompts instead of writing", [
        ("db-data", "v0", "10–11 July", "Data layer first", [
            (BUILT, "The v1 design defined the SQLite schema (jobs, applications, responses). A cleanup on 11 July deleted six dead scripts, moved job descriptions out of the jobs table into a separate JSON file keyed by job id, and created the database.")]),
        ("db-plan", "plan", "10–12 July", "The plan for a live bridge", [
            (BUILT, "The prompt written for building the dashboard planned a Cowork artifact that would call Cowork's tools directly: <code>callMcpTool</code> to reach a shell tool and query the database, <code>runScheduledTask</code> to start the tailoring task from a button, and <code>askClaude</code> for a quick three-sentence draft of a cover letter, labelled as a draft. As a fallback, an exporter would write the data to a JSON snapshot that the page reads.")]),
        ("db-v12", "v1/v2", "12 July", "First dashboards", [
            (BUILT, "The notes record that the first dashboard was live as an artifact on 12 July; no file of it was archived. The oldest archived template, v2, is dated the same day. It probes a list of tool names through <code>callMcpTool</code> and switches to \"live\" if one answers, otherwise to a read-only snapshot mode."),
            (BUG, "Without the bridge, its buttons only showed messages to do the step in the chat or to start the task from the sidebar, and the draft preview reported that <code>askClaude</code> wasn't available.")]),
        ("db-store", "bugs", "13–14 July", "Storage problems", [
            (BUG, "Writing to the database directly on the synced folder failed with <code>disk I/O error</code> and left a stale journal file behind; files already opened in a viewer couldn't be overwritten. On 14 July a scheduled run hit the same database error, and separately the dashboard rendered blank because its template had been cut off in the middle of a script block."),
            (FIX, "The reliability layer was added that day (<code>core/safe_io.py</code>, <code>core/job_database.py</code>, the self-verifying <code>core/build_dashboard.py</code>), and a setup script that would have overwritten the live database was deleted.")]),
        ("db-16", "change", "16 July", "Low matches hidden", [
            (FIX, "The exporter started hiding jobs below the match threshold from the dashboard.")]),
        ("db-v3", "v3", "24 July", "\"Copy for Claude\"", [
            (BUILT, "The current layout: four tabs (overview, inbox, search radar, all jobs), a slide-in detail panel and a tailoring tray. When a live action fails, the page falls back to a \"copy for Claude\" button: it copies a ready-made prompt, you paste it into the chat, and Claude does the step.")]),
        ("db-29", "design", "29 July", "Copy-paste becomes the design", [
            (BUG, "A cleanup confirmed that the bridge had never been connected: no tools were enabled for the artifact when it was published."),
            (FIX, "The copy-paste handoff was kept as the intended design, not a workaround:" + L([
                "the dashboard has no write access at all; every change goes through a chat where you see it before it happens;",
                "each copied prompt is self-contained (job, company, the exact change, the \"never delete\" rule), so it works in any Claude session;",
                "nothing on the page depends on a runtime feature being available."]))]),
        ("db-sep", "public", "27–28 September", "The public version", [
            (BUG, "Stray null bytes from a damaged write were in the master CV. In the dashboard, a hidden bar still showed as an empty box, and the empty tailoring tray peeked out at the bottom."),
            (FIX, "The null bytes were removed; for the public version the bridge code was removed from the template, the UI was translated to English, and both layout bugs were fixed.")]),
    ], None),
]

TOOLS = [
    ("Paid scoring API", "the 10 July design (`job_analyzer.py` with a model-selection module)", "automatic match scoring, with a table choosing a model tier per task by cost and speed", "retired 14 July, replaced by scoring inside the agent run"),
    ("Apify", "chosen in the 10 July design for scraping job boards", "pre-built actors, handling of bot protection, low cost per job (the design's reasons)", "earlier local scraping scripts (the v1 approach, archived 29 July). On 5 August the actor was pinned, its input checked against the live schema, filters inside the actor removed, and every call given a spending cap"),
    ("Indeed connector", "the v1 search command (around 11–12 July), as an optional second source", "a second job source with exact posting dates", "Indeed results collected into a JSON file by the earlier local scripts (archived). On 5 August it became mandatory, with many narrow queries because it returns about 10 results per query"),
    ("Gmail connector", "planned in the dashboard prompts of 10–12 July (\"no IMAP passwords in code\"); the mail-scan task was created on 14 July", "reply tracking by company name, classified as invited / waiting / rejected, without any mail credentials in the project. The same day its results were used to mark eight jobs as applied", "a `/job-track` command (12 July) that wrote replies into the database's responses table; the dashboard reads the scan's `mail_status.json` instead"),
    ("Cowork scheduled tasks", "the tailoring task on 12 July (manual trigger, no schedule), the mail scan and the search on 14 July", "running the routines on the Claude subscription, without an API key", "manual sessions and slash commands; the old search command was archived on 27 September. Since 29 July the tasks only point to the routine files"),
    ("Artifact publishing", "12 July, when the first dashboard went live as an artifact", "one page to review jobs, see replies and trigger the next step, updated in place by every routine", "before: the v1 search wrote a markdown digest after each run"),
    ("CV snapshot with hash check", "14 July", "scoring and tailoring always read the current CV, but only re-read it when its sha256 hash changes, so an unchanged CV costs nothing", "a separate JSON profile file and the script that synced it from the CV"),
    ("SQLite", "the 10 July design; the database was created on 11 July", "one queryable source of truth for jobs, applications and replies, where rows are never deleted, only their status changes", "a legacy JSON job list (archived 13 July)"),
]

BUGS = [
    ("14 July", "Blank dashboard from a truncated template", "A write \"succeeded\" but the file was cut off, and the build embedded data into it and reported success.", "Every write is checksummed and re-read, and the build verifies its own output and prints `OK` or `BUILD FAILED`; no routine reports success without `OK`."),
    ("14 July", "Stale database journal → `disk I/O error`", "An interrupted write on a synced folder left a journal file that blocked the next connection.", "The database layer cleans up known leftovers before connecting, retries once, and verifies the database after every batch of writes."),
    ("14 July", "Scoring through a paid API, with a crude fallback", "", "All judgment moved into the agent run, and the CV snapshot with a hash check keeps runs cheap without any model bill."),
    ("16–17 July", "Scheduled-task drift → 16 four-page CVs", "Rules had been added to one copy of the prompt, not the one that ran.", "Rules live in exactly one routine file, and scheduled tasks only point to it (made permanent on 29 July)."),
    ("18 July", "A heading and its list split across two pages", "", "Entries became unbreakable blocks, and the rendered PDF is checked, not just the source."),
    ("29 July", "The live bridge had never been connected", "", "The copy-to-chat handoff became the design; the dashboard has no write access."),
    ("30 July", "The master CV's own template had drifted from the rules", "", "Rules are fixed at the source file, not only in the newest output."),
    ("5 August", "Silent filters removed the best job", "A bare word in the exclusion list, a filter inside the scraper and tech-qualified search terms could each drop a good match before scoring, and nothing recorded it.", "Cast wide, then score; exclusions became a demotion; every reject is logged with a reason."),
    ("5 August", "Rotating short links would have created six duplicates", "", "Deduplication on the posting's identity (normalised company + title), not only its URL."),
]

FIXES = """1. 10 Jul – design relied on automatic form submission and paid per-task model calls – keep a human before every application; keep the model inside the run.
2. 11 Jul – six dead scripts left over from the first design – delete what isn't used.
3. 11 Jul – job descriptions stored in the jobs table – keep lists lean; load large text by id from a separate file.
4. 13 Jul – direct database writes on the synced folder failed and left a stale journal – round-trip through local disk; truncate stale journals.
5. 13 Jul – files already opened in a viewer couldn't be overwritten – write under a new name and say which file is current.
6. 13 Jul – an unrelated legacy job list sat next to the live database – archive what isn't part of the pipeline.
7. 14 Jul – a setup script would have overwritten the live database – remove destructive scripts; guard generators with `--force`.
8. 14 Jul – scoring called a paid API, with a keyword-count fallback – score in the agent run against a hash-gated CV snapshot.
9. 14 Jul – scheduled run failed with `disk I/O error` from a stale journal – clean up before connecting, retry once, verify after writing.
10. 14 Jul – dashboard rendered blank from a truncated template – checksum every write; make the build verify itself.
11. 14 Jul – jobs that had been applied to weren't marked as applied – reconcile the database with the mail record.
12. 16 Jul – low-match jobs cluttered the dashboard – filter them in the exporter as a second safety net.
13. 16–17 Jul – the scheduled task never got the new rules → 16 four-page CVs and PDF letters – one copy of the rules, and tasks that only point to it.
14. 18 Jul – a heading and its list split across pages – wrap each entry in an unbreakable block.
15. 18–19 Jul – stray indent on every block after the first – `\\noindent` in the block definition; measure rendered output.
16. 18 Jul – wide gaps after disabling hyphenation, and an orphan single-column skill row – ragged-right lists; merge categories into a full grid.
17. 24 Jul – the match threshold was too low – raise it to 50.
18. 29 Jul – two empty script files and an empty folder – delete leftovers.
19. 29 Jul – the dashboard's live bridge had never been connected – copy-to-chat is the design; the page needs no write access.
20. 29 Jul – duplicated rules could drift again – the task reads the routine file at runtime.
21. 29 Jul – a job's notes claimed a package existed when no folder did – don't trust status notes; check the files.
22. 30 Jul – the master CV's preamble had drifted from the typography rules – fix rules at the source.
23. 5 Aug – a bare "sales" exclusion discarded an after-sales AI role before scoring – exclusions must be specific; override words send jobs to scoring.
24. 5 Aug – a bare "internship" exclusion dropped combined internship/working-student postings – the same lesson, a second time.
25. 5 Aug – a job-function filter inside the scraper removed cross-functional roles – no filtering before you can see the posting.
26. 5 Aug – a title-only check missed truncated titles – check title and description.
27. 5 Aug – a 30-day window surfaced postings that were already closed – a 10-day window.
28. 5 Aug – rotating short links broke URL-only deduplication – deduplicate on normalised company + title too.
29. 5 Aug – rejected postings were discarded silently – log every reject with a reason.
30. 5 Aug – the scraper's input had never been checked against its schema – verify tool inputs against the live schema.
31. by 5 Aug – `add_job()` didn't reliably return the new row id after a retry – read the id before committing (fixed in the public version).
32. 27 Sep – null bytes at the end of the master CV from a damaged write – check files written to synced folders.
33. 28 Sep – a hidden bar rendered as an empty box, and the empty tray peeked out – CSS `display` rules can override `hidden`; test the empty states."""



# ------------------------------------------------------------------ versions json (input of the asset generator)
vj = {}
for t in THREADS:
    for slug, tag, when, title, _r in t[2]:
        vj[slug] = [tag, when, title]
(HERE / "story-versions.json").write_text(json.dumps(vj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
M.main()
pills = M.make_pills()
HUE = M.HUES
_rows = rows


def rows(zone_slug, items, **kw):      # strip Markdown markers from the text drawn inside SVGs
    items = [(re.sub(r"[`*]", "", i[0]), re.sub(r"[`*]", "", i[1])) + tuple(i[2:]) for i in items]
    return _rows(zone_slug, items, **kw)


def shield(label, value, hue):
    return (f"https://img.shields.io/static/v1?label={label.replace(' ', '%20')}&message={value}"
            f"&color={HUE[hue]['shield']}&labelColor=1b1b24")


R = []
a = R.append
a('<p align="center"><a href="#dashboard"><img src="docs/readme/banner.svg" alt="Your job pipeline: find postings, score them against my CV, prepare applications and track replies. Dashboard tiles with fictional demo data: 5 applied, 3 in the mail, 1 invitation, 8 open chances, 2 packages ready, best match 91 %" width="100%"></a></p>\n')
badges = [("routines", "3", "violet", "routines/", "routines: 3"),
          ("core Python modules", "5", "blue", "core/", "core Python modules: 5"),
          ("third-party dependencies", "0", "green", "docs/SETUP.md#2-requirements", "third-party dependencies: 0"),
          ("connectors", "3", "cyan", "docs/SETUP.md#5-connectors", "connectors: 3"),
          ("documented fixes", "33", "pink", "#all-33-fixes", "documented fixes: 33"),
          ("license", "MIT", "amber", "LICENSE", "license: MIT")]
a('<p align="center">\n' + "\n".join(f'  <a href="{lnk}"><img src="{shield(l, v, h)}" alt="{alt}"></a>' for l, v, h, lnk, alt in badges) + "\n</p>\n")
pl = [f'  <a href="{an}"><img src="docs/readme/nav/{sl}.svg" alt="{escape(lb)}" height="30"></a>' for lb, an, sl, w in pills]
a('<p align="center">\n' + "\n".join(pl[:5]) + "\n</p>\n")
a('<p align="center">\n' + "\n".join(pl[5:]) + "\n</p>\n")

a('<a name="story"></a>')
a('<p><a href="#the-story"><img src="docs/readme/short-version.svg" alt="The short version. It began on 10 July as a design where a paid model API scored every job and forms were submitted automatically. Bugs reshaped it: a blank dashboard, a stale database journal, drifting rules, silent filters. Now: agent routines around one SQLite file, no API key, a human before every application." width="100%"></a></p>\n')
a('<p align="center"><a href="#the-story"><img src="docs/readme/read-full-story.svg" alt="Read the full story" height="40"></a></p>\n')

# --- see it work
a(zone("demo", "01 See it work: a short tour of the dashboard, demo data only"))
a('<p align="center"><a href="#dashboard"><img src="docs/images/dashboard-tour.gif" alt="Animated tour of the dashboard with fictional demo data: the overview with stat tiles, a search filter, a job detail panel with the invitation and mail history, copying the interview-prep prompt, and back to the overview" width="960"></a></p>\n')
a('<p align="center"><sub>1 Overview · 2 Filter · 3 Job detail · 4 Copy the prompt · 5 Back to the overview. Fictional demo data.</sub></p>\n')

# --- dashboard
a(zone("dashboard", "02 The dashboard: review jobs, replies and next steps on one page"))
a(rows("dashboard", [
    ("Four tabs, one HTML file", "overview, inbox, search radar and all jobs; no libraries, no network calls", None),
    ("Every action copies a prompt", "approve, discard, tailor, search, interview prep: paste it into the Claude chat",
     "The page itself has no write access, so a human stays in the loop and nothing changes without you seeing it."),
]) + "\n")
a('<p><a href="docs/SETUP.md#3-install-and-run-the-demo"><img src="docs/readme/dashboard-main.png" alt="Dashboard overview with application counters, search radar, inbox and top matches (demo data)" width="100%"></a></p>\n')
a('<p><a href="core/dashboard_template.html"><img src="docs/readme/dashboard-job-detail.png" alt="Job detail panel with the invitation, mail history, skill match and copy-to-chat buttons (demo data)" width="100%"></a></p>\n')
a("<sub>The job detail panel: match and freshness, the invitation and mail history from the reply scan, the skill match, and the next step as a prompt to copy. Both screenshots use the included demo data. All companies are fictional.</sub>\n")

# --- search
a(zone("search", "03 Search and scoring: two sources, few filters, every reject logged"))
a(rows("search", [
    ("Two job sources, one pass", "an Apify job-listing actor does a few broad sweeps; Indeed runs many narrow queries",
     "Results are deduplicated on URL **and** on normalised company + title, because some short links change between requests."),
    ("\"Cast wide, then score\"", "pre-scoring filters are few and specific, and exclusions only demote",
     "Every rejected posting is written to a log with a reason."),
    ("Scoring by the agent, not a script", "a 0–100 match score, matching and missing skills and a one-line reason",
     "Each new job is judged against a snapshot of your CV. Jobs under the threshold are never stored."),
    ("Cheap by design", "the CV is only re-read when its sha256 hash changes; no script calls a model",
     "The one paid source gets a spending cap on every call."),
]) + "\n")

# --- applications
a(zone("applications", "04 Applications: optional, a CV and a cover letter per job"))
a(rows("applications", [
    ("A package per queued job", "a LaTeX CV cut to a hard page limit and an editable .docx cover letter",
     "Both are written in the language you set in the config."),
    ("One rule file", "the rules for both live in routines/process-tailor-queue.md",
     "Truthful to your CV, no claimed specialization, content chosen per posting, a layout that survives applicant-tracking systems, and a letter that tells a short story instead of listing courses.",
     "routines/process-tailor-queue.md"),
]) + "\n")

# --- replies
a(zone("replies", "05 Replies: optional, invited, waiting or rejected"))
a(rows("replies", [
    ("Scan by company name", "each application is classified as invited, waiting or rejected", "The result is shown in the dashboard's inbox."),
    ("Follow-up reminder", "shown after 14 days without an answer", None),
    ("Never touches the database", "it only writes its own status file", None),
]) + "\n")

# --- routines
a(zone("routines", "06 How it runs in Claude: three routines, as scheduled tasks"))
a("<sub>The three routines as they look in Claude's scheduled tasks. Each card links to the section that describes it. The grey bars stand where the folder and the project name would be.</sub>\n")
for slug, anchor, alt in [
    ("search-jobs", "search-and-scoring", "Routine card: Search jobs. Search new Werkstudent jobs via BOTH Apify LinkedIn + Indeed MCP (10-day window, wide sweep), score vs CV snapshot, insert >=50% into jobs.db, rebuild dashboard. Badge: Only on this computer."),
    ("process-tailor-queue", "applications", "Routine card: Process tailor queue. Generate tailored German CV + Motivationsschreiben packages for queued jobs, apply queued status changes, refresh dashboard data. Badge: Only on this computer."),
    ("scan-mail-status", "replies", "Routine card: Scan mail status. You maintain the job-application mail status for the project at (hidden). Do exactly this, self-contained: 1. Read the job list from the SQLite DB… Badges: Paused, Requires your computer."),
]:
    a(f'<p><a href="#{anchor}"><img src="docs/readme/routines/{slug}.svg" alt="{escape(alt)}" width="100%"></a></p>\n')
a("<sub>None of the routines runs on a timer, I start them myself (frequency: manual). Search jobs and Process tailor queue show \"Only on this computer\" because they use local files, so they run only while Claude Desktop is open on my computer. Scan mail status is paused at the moment.</sub>\n")

# --- guardrails
a(zone("guardrails", "07 Guardrails: nothing deleted, every write checked"))
a(rows("guardrails", [
    ("Nothing is deleted", "rows in jobs.db are never deleted; only their status changes", None),
    ("Every write is checked", "each file write is checksummed and read back", "Stale SQLite journals are cleaned up before connecting."),
    ("The build verifies itself", "it refuses a truncated template and prints OK or BUILD FAILED", "No routine reports success without `OK`."),
    ("You apply yourself", "nothing is ever submitted automatically", None),
], check=True) + "\n")

# --- architecture
a(zone("architecture", "08 Architecture: routines, connectors, one data folder"))
a(MERMAID + "\n")
M.write("chips.svg", M.chips_svg(["Python, standard library only", "SQLite", "LaTeX", "MCP connectors", "one HTML file"]))
a('<p><a href="#architecture"><img src="docs/readme/chips.svg" alt="Stack: Python (standard library only), SQLite, LaTeX, MCP connectors, one HTML file" height="28"></a></p>\n')
a("<sub>The Python side is small on purpose: five standard-library modules. The \"program\" is the three routine files in [`routines/`](routines/), which a Claude agent follows step by step.</sub>\n")
parts = [
    ("routines/search-jobs.md", "search both sources, filter, dedupe, score, insert, rebuild"),
    ("routines/process-tailor-queue.md", "optional: tailored CV + cover letter per queued job"),
    ("routines/scan-mail-status.md", "optional: classify replies from the mailbox"),
    ("core/job_database.py", "SQLite schema + CRUD, stale-journal cleanup, verify()"),
    ("core/safe_io.py", "write → fsync → checksum → re-read → retry"),
    ("core/export_dashboard_data.py", "read-only export of the data layer to JSON"),
    ("core/build_dashboard.py", "embed the data into the template and verify the result"),
    ("core/dashboard_template.html", "the dashboard: one file, no libraries, no network calls"),
    ("demo/generate_demo_data.py", "a complete fictional data layer for trying it out"),
]
a(rows("architecture", [(f, d, None, f, True) for f, d in parts]) + "\n")

# --- use it yourself
a(zone("use", "09 Use it yourself: setup guide, demo data first"))
a(rows("use", [
    ("Try the demo data first", "a complete fictional data layer; no CV and no connectors needed",
     "`python demo/generate_demo_data.py`, then `python core/build_dashboard.py`"),
    ("Then make it yours", "your CV, search settings, connectors and scheduled tasks",
     "Follow **[docs/SETUP.md](docs/SETUP.md)**.", "docs/SETUP.md"),
]) + "\n")

# --- notes
a(zone("notes", "10 Honest notes: limitations, security, AI, license"))
blocks = []
blocks.append(rows("notes", [("Known limitations", "what it doesn't do, one line each", None)], first=1))
blocks.append(plain_list([
    "It needs a Claude plan with scheduled tasks and connectors, and the Claude desktop app with access to this folder; nothing runs on its own.",
    "Not every connector and scheduled-task step in the setup guide has been checked click by click in the app yet.",
    "Both job sources are mandatory: if Apify or Indeed fails, the whole search run counts as failed.",
    "The Apify job-listing actor you choose may charge per result; every call has a spending cap, but the cost depends on that actor.",
    "Whether the Indeed connector costs anything isn't documented here.",
    "Match scores are Claude's judgment in each run, not a formula, so the same posting isn't guaranteed the same score twice.",
    "There are no automated tests, and the company + title deduplication lives in the routine text, not in code.",
    "The dashboard is a snapshot: changes only show after a rebuild and republish.",
    "The dashboard's layout overflows sideways at phone width.",
    "In light mode, a faint shadow strip shows at the right edge of the dashboard.",
    "Without a LaTeX engine, tailored CVs stay as `.tex` source; no PDF is made.",
    "The dashboard's interface is English only; the documents follow `output_language` in the config.",
]))
blocks.append(">")
blocks.append(rows("notes", [("Security scope", "what stays on your machine and what Claude sees", None)], first=2))
blocks.append(">")
blocks.append("> <sub>The routines read job postings through the Apify and Indeed connectors and, for the optional reply scan, the mails that match your companies' names through the Gmail connector. They write only to local files in this repository (the SQLite file, JSON files, the application packages and the exported dashboard page) and republish that page as a Claude artifact. The dashboard has no write access, nothing is submitted automatically (you apply yourself), and the routines never delete rows in the database, only change their status. Every file write is checksummed and read back. No model API key is stored anywhere: the logins for Apify, Indeed and Gmail live in Claude's connector settings, not in this repository.</sub>")
blocks.append(">")
blocks.append(rows("notes", [("Built with AI", "I decided and tested; Claude was the coding assistant", None)], first=3))
blocks.append(">")
blocks.append("> <sub>I decided what to build and how it should behave, and I tested the result. Claude was the coding assistant. At runtime the pipeline is Claude routines too, on a Claude subscription, with no model API key.</sub>")
blocks.append(">")
blocks.append(rows("notes", [("License", "MIT, see the LICENSE file", None, "LICENSE")], first=4))
a("\n".join(blocks) + "\n")

# --- full story
a(zone("story", "11 The full story: version by version, with the bugs that shaped it"))
a("<sub>How this pipeline got from a per-token API script to agent routines around one SQLite file, reconstructed from dated notes, change logs and archived files. Facts only; all dates are 2026. Where something wasn't recorded, it's left out.</sub>\n")
a(rows("story", [("Origin", "why I started building this", "I was looking for a Werkstudent job, and every application meant the same steps: find postings, check them against my CV, write a CV and cover letter, keep track of replies. I built one place to do that, with Claude as the agent.")], first=1) + "\n")
n = 1
for title, muted, versions, footer in THREADS:
    n += 1
    body = [rows("story", [(title, muted, None)], first=n)]
    for slug, tag, when, vt, rws in versions:
        body.append(">")
        body.append(f'> <a href="#the-story"><img src="docs/readme/story/{slug}.svg" alt="{escape(tag)} · {escape(when)} · {escape(vt)}" width="100%"></a>')
        body.append(">")
        body.extend("> " + l for l in card(rws))
    if footer:
        body.append(">")
        body.append("> " + footer)
    a("\n".join(body) + "\n")


def tbl(head, rows_):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows_:
        out.append("| " + " | ".join((c or "—").replace("|", "\\|") for c in r) + " |")
    return out


n += 1
a(rows("story", [("Tools and connectors", "what came in, what it solved, what it replaced", None)], first=n))
a(">")
a(bq(tbl(["Tool", "Came in", "Solved", "Replaced"], TOOLS)) + "\n")
n += 1
a(rows("story", [("The bugs that changed the design", "nine of them, each with what it changed", None)], first=n))
a(">")
a(bq(tbl(["When", "Bug", "What went wrong", "What changed"], [(d, "**" + t + "**", w, c) for d, t, w, c in BUGS])) + "\n")
n += 1
a('<a name="all-33-fixes"></a>')
a(rows("story", [("All 33 fixes", "date, what broke, what it taught", None, "#all-33-fixes")], first=n))
a(">")
a("> <details>\n> <summary>Show the full list (date – what broke – what it taught)</summary>\n>\n" + "\n".join("> " + l for l in FIXES.split("\n")) + "\n>\n> </details>\n")

(ROOT / "README.md").write_text("\n".join(R), encoding="utf-8", newline="\n")
print("README OK")
