# The build story

How this pipeline got from a per-token API script to agent routines around one SQLite file, reconstructed from dated notes, change logs and archived files. Facts only; all dates are 2026. Where something wasn't recorded, it's left out.

Contents: [Origin](#origin) · [Job search](#job-search) · [CV tailoring](#cv-tailoring) · [Motivation letter](#motivation-letter) · [Dashboard](#dashboard) · [Tools and connectors](#tools-and-connectors) · [The bugs that changed the design](#the-bugs-that-changed-the-design) · [All 33 fixes](#all-33-fixes)

---

## Origin

<!-- WALID: why I started building this — my own words -->

---

## Job search

**v0, 10 July: a design with a model bill.**
The first design combined a scraping service for job boards, browser automation that would fill in and submit application forms, and SQLite for tracking. A Python analyzer sent every job description to a paid model API for scoring, with a table assigning a different model tier to each task by cost and speed. Without an API key it fell back to counting how many known skills appeared in the text.
*What went wrong:* every scored job cost money, the fallback was crude, and automatic submission meant no human check before an application went out.
*What changed:* automatic submission was dropped, and scoring moved into the agent.

**v1, around 11–12 July: a slash command.**
A `/job-search` command ran the scraping actor and the Indeed connector (the second one optional), with four search terms, a 30-day window, and a job-function filter set inside the scraper. The agent scored each job against a separate JSON profile file, assigned tiers, and wrote a markdown digest.
*What went wrong:* the profile file was separate from the CV and had to be kept in sync, and the scoring script with its paid API was still in the project.
*What changed:* see v2.

**v2, 14 July: a scheduled task and a CV snapshot.**
The search became a scheduled task. The profile file and the scoring script were retired. Instead, Claude reads the master CV once and stores a skills snapshot plus the CV's sha256 hash; every run compares the hash first and re-reads the CV only when it has changed. Scoring happens in the agent turn, with no API call.
On 16 July jobs below a match-score threshold stopped being inserted; on 24 July the threshold was raised to 50 and two narrow search queries were added.

**v3, 5 August: "cast wide, then score".**
*What went wrong:* one of the best-fitting postings of the whole search, an AI and data-analysis role filed under an after-sales department, was missed for a full cycle. Three things caused it at once: search terms with technology words that its title didn't contain, the job-function filter inside the scraper (the role wasn't filed under IT), and a bare "sales" in the exclusion list. Separately, Indeed's short links turned out to change on every request, so URL-only deduplication would have inserted six duplicates in one run, and postings found late in a 30-day window were often already closed.
*What changed:*
- Both sources became mandatory; a source that fails or returns nothing makes the whole run a failure, reported first.
- Bare employment-type terms for the broad source, many narrow queries for Indeed.
- No filters inside the scraper.
- The employment type is checked in title **and** description, because titles can come back truncated.
- Exclusion became a demotion: override words send a posting to scoring anyway.
- Every rejected posting is logged with a reason.
- Deduplication on normalised company + title as well as URL.
- Scoring judges the work described, not the department.
- The window went from 30 to 10 days, and the scraper's input was checked against its live schema.

**27 September.** The old slash command was archived; the scheduled task is the only way the search runs.

<!-- WALID: what annoyed me, what I changed, how I knew it was good -->

---

## CV tailoring

**v0, 10–12 July: a sentence in a prompt.**
The first dashboard prompts described tailoring in one line: a CV built from the master, with sections emphasised per job type from a small mapping file. On 12 July the note was to agree on how tailoring should work before generating more packages.

**v1, 13 July: rules from reviewing drafts.**
A `/job-tailor` command set the basics: a hard two-page limit on the tailored CV, content chosen per posting as a judgment call, a rewritten intro, and one "wildcard" line unrelated to the job. Reviewing the first drafts produced six corrections the same day:
- the master CV stays complete; only the tailored copy is cut;
- no "(completed)" labels on certificates, only "in progress" where it applies;
- no "with a focus on X" framing in the intro;
- no dashes as sentence connectors and no salesy phrasing;
- nested items as bold name + colon instead of italics + dash;
- the intro as several short sentences in a fixed order: status, relevant experience, interests, languages.

**16–17 July: the drift.**
*What went wrong:* the scheduled tailoring task had never received the 13 July rules; only the slash command had them. Its run on 16 July produced 16 packages of about four pages each (the master CV with a new intro) and cover letters as PDF instead of Word.
*What changed:* the full rule set was written into the task, including a compile-and-count-pages loop, and all 16 packages were redone.

**v3, 18 July: nine passes on one CV.**
Working through one CV pass by pass added most of today's layout and wording rules:
- certificates and skills as separate sections, certificate details taken from the actual certificate documents;
- every heading + bullet list in an unbreakable block, after a block split across a page in a rendered PDF;
- the concrete technology in each bullet in bold;
- the intro as a recruiter summary: no course references, no sentences with an implied third-person subject, no parentheses;
- certificates in the same heading format as education;
- skills as a two-column grid with no orphan single-column row;
- no skill phrase repeated in both the skills section and a project;
- hyphenation off and lists ragged-right, margins 1.5 cm;
- full terms instead of abbreviations a non-technical reader might not know;
- a sweep that replaced explanatory dashes with colons.

The last pass fixed a template bug: every block after the first in a section had a small indent, which misaligned titles and dates. It was found by measuring a rendered PDF, and fixed with `\noindent` in the block definition.

**v4, 19 July: one routine with a quality bar.**
The rules were consolidated into one routine file with an explicit goal: every CV must be readable by applicant-tracking systems (real text, clean reading order, standard headings) and pass a recruiter's few-second skim. Three finished packages became the reference. New checks after compiling: extract the text to confirm the reading order, and render each page to confirm no block was cut.

**v5, 29 July: one copy of the rules.**
The scheduled task stopped carrying its own copy of the rules. It now only points to the routine file and reads it at the start of every run.

**v6, 30 July: naming and the template itself.**
The PDF is named after the company instead of a generic file name. The master CV's own preamble had drifted from the 19 July typography rules (old margins, hyphenation on, no `\noindent`) and was fixed at the source. One package's intro still named courses and was rewritten.

**17 August: no claimed specialization.**
After a wording was rejected during an interview simulation: never claim a specialization, focus or qualification that isn't in the CV; describe interests as interests.

**29–30 September (public version).** Abbreviations changed from "write them out" to "full term with the abbreviation in brackets the first time, then the abbreviation only", and the output language became a config setting.

<!-- WALID: what annoyed me, what I changed, how I knew it was good -->

---

## Motivation letter

**v0, 10–12 July: half a page from the posting.**
The first prompts asked for a letter of about half a page that referred to concrete tasks from the description and mapped them to the profile, written as LaTeX and compiled to PDF.

**v1, 13 July (morning): letters in a script.**
The first batch of letters was written as fixed paragraph lists per company inside a generator script and built into Word files. Each followed the same pattern: why this role, two projects as proof, a planned future course as outlook, availability plus a note that a transcript was attached.

**v2, 13 July: editable Word files and a four-part schema.**
The letter became a native `.docx`, because it gets edited by hand before sending. One application (CV and letter together) went through six versions that day. For the letter, the changes were: leading with the most relevant course, the Word format, rewording a start date that could be read as an end date, and finally a simpler four-part schema without the dense keyword listing. That schema became the standard: interest in the role, what was learned in a course and how it connects to a project, a broader interest tied to a future elective, availability.

**17 July: the drift.**
The same scheduled-task drift as for the CVs: the 16 July run had shipped letters as PDF/LaTeX. They were regenerated as Word files.

**v3, 18 July: the schema is replaced.**
The four-part schema was dropped. The new structure: an opening with concrete matching skills and no filler, a middle with one completed-course proof point and one project, an honest sentence where a required skill is missing, and a closing with availability only (no remote/on-site remarks, no transcript unless asked).

**v4, 19 July: simpler language and more motivation.**
After feedback on the language level and on letters that mainly talked about courses, the rules changed again:
- everyday language with short sentences;
- research the company first and open with one specific, true connection;
- a short narrative with one or two proof points instead of a list of courses;
- only completed courses as proof;
- the earlier reference letters were retired.

**17 August.** The no-specialization rule applies to letters too.

**29–30 September (public version).** Written down as explicit rules: name 2–3 concrete tasks from the posting, greet a named contact person by name, write start dates so they can't be read as end dates, abbreviations in full the first time, and the output language as a setting.

<!-- WALID: what annoyed me, what I changed, how I knew it was good -->

---

## Dashboard

**10–11 July: data layer first.**
The v1 design defined the SQLite schema (jobs, applications, responses). A cleanup on 11 July deleted six dead scripts, moved job descriptions out of the jobs table into a separate JSON file keyed by job id, and created the database.

**10–12 July: the plan for a live bridge.**
The prompt written for building the dashboard planned a Cowork artifact that would call Cowork's tools directly: `callMcpTool` to reach a shell tool and query the database, `runScheduledTask` to start the tailoring task from a button, and `askClaude` for a quick three-sentence draft of a cover letter, labelled as a draft. As a fallback, an exporter would write the data to a JSON snapshot that the page reads.

**12 July: v1 and v2.**
The notes record that the first dashboard was live as an artifact on 12 July; no file of it was archived. The oldest archived template, v2, is dated the same day. It probes a list of tool names through `callMcpTool` and switches to "live" if one answers, otherwise to a read-only snapshot mode. Without the bridge, its buttons only showed messages to do the step in the chat or to start the task from the sidebar, and the draft preview reported that `askClaude` wasn't available.

**13–14 July: storage problems.**
Writing to the database directly on the synced folder failed with `disk I/O error` and left a stale journal file behind; files that had already been opened in a viewer couldn't be overwritten. On 14 July a scheduled run hit the same database error, and separately the dashboard rendered blank because its template had been cut off in the middle of a script block. That day the reliability layer was added (`core/safe_io.py`, `core/job_database.py`, the self-verifying `core/build_dashboard.py`), and a setup script that would have overwritten the live database was deleted.

**16 July.** The exporter started hiding jobs below the match threshold from the dashboard.

**24 July: v3 and "copy for Claude".**
The current layout: four tabs (overview, inbox, search radar, all jobs), a slide-in detail panel and a tailoring tray. When a live action fails, the page now falls back to a "copy for Claude" button: it copies a ready-made prompt, you paste it into the chat, and Claude does the step.

**29 July: copy-paste becomes the design.**
A cleanup confirmed that the bridge had never been connected: no tools were enabled for the artifact when it was published. The copy-paste handoff was kept as the intended design, not a workaround. What it does now:
- the dashboard has no write access at all; every change goes through a chat where you see it before it happens;
- each copied prompt is self-contained (job, company, the exact change, the "never delete" rule), so it works in any Claude session;
- nothing on the page depends on a runtime feature being available.

**27–28 September.** Stray null bytes from a damaged write were removed from the master CV. For the public version the bridge code was removed from the template, the UI was translated to English, and two layout bugs were fixed (a hidden bar still showing as an empty box, and the empty tailoring tray peeking out at the bottom).

<!-- WALID: what annoyed me, what I changed, how I knew it was good -->

---

## Tools and connectors

**Paid scoring API.** *Came in:* the 10 July design (`job_analyzer.py` with a model-selection module). *Solved:* automatic match scoring, with a table choosing a model tier per task by cost and speed. *Retired:* 14 July, replaced by scoring inside the agent run.

**Apify.** *Came in:* chosen in the 10 July design for scraping job boards. *Solved (the design's reasons):* pre-built actors, handling of bot protection, low cost per job. *Replaced:* earlier local scraping scripts (the v1 approach, archived on 29 July). On 5 August the actor was pinned, its input checked against the live schema, filters inside the actor removed, and every call given a spending cap.

**Indeed connector.** *Came in:* the v1 search command (around 11–12 July), as an optional second source. *Solved:* a second job source with exact posting dates. *Replaced:* Indeed results collected into a JSON file by the earlier local scripts (archived). On 5 August it became mandatory, with many narrow queries because it returns about 10 results per query.

**Gmail connector.** *Came in:* planned in the dashboard prompts of 10–12 July ("no IMAP passwords in code"); the mail-scan task was created on 14 July. *Solved:* reply tracking by company name, classified as invited / waiting / rejected, without any mail credentials in the project. The same day its results were used to mark eight jobs as applied. *Replaced:* a `/job-track` command (12 July) that wrote replies into the database's responses table; the dashboard reads the scan's `mail_status.json` instead.

**Cowork scheduled tasks.** *Came in:* the tailoring task on 12 July (manual trigger, no schedule), the mail scan and the search on 14 July. *Solved:* running the routines on the Claude subscription, without an API key. *Replaced:* manual sessions and slash commands; the old search command was archived on 27 September. Since 29 July the tasks only point to the routine files.

**Artifact publishing.** *Came in:* 12 July, when the first dashboard went live as an artifact. *Solved:* one page to review jobs, see replies and trigger the next step, updated in place by every routine. *Before:* the v1 search wrote a markdown digest after each run.

**CV snapshot with hash check.** *Came in:* 14 July. *Solved:* scoring and tailoring always read the current CV, but only re-read it when its sha256 hash changes, so an unchanged CV costs nothing. *Replaced:* a separate JSON profile file and the script that synced it from the CV.

**SQLite.** *Came in:* the 10 July design; the database was created on 11 July. *Solved:* one queryable source of truth for jobs, applications and replies, where rows are never deleted, only their status changes. *Replaced:* a legacy JSON job list (archived on 13 July).

---

## The bugs that changed the design

1. **14 July: blank dashboard from a truncated template.** A write "succeeded" but the file was cut off, and the build embedded data into it and reported success. *Changed:* every write is checksummed and re-read, and the build verifies its own output and prints `OK` or `BUILD FAILED`; no routine reports success without `OK`.
2. **14 July: stale database journal → `disk I/O error`.** An interrupted write on a synced folder left a journal file that blocked the next connection. *Changed:* the database layer cleans up known leftovers before connecting, retries once, and verifies the database after every batch of writes.
3. **14 July: scoring through a paid API, with a crude fallback.** *Changed:* all judgment moved into the agent run, and the CV snapshot with a hash check keeps runs cheap without any model bill.
4. **16–17 July: scheduled-task drift → 16 four-page CVs.** Rules had been added to one copy of the prompt, not the one that ran. *Changed:* rules live in exactly one routine file, and scheduled tasks only point to it (made permanent on 29 July).
5. **18 July: a heading and its list split across two pages.** *Changed:* entries became unbreakable blocks, and the rendered PDF is checked, not just the source.
6. **29 July: the live bridge had never been connected.** *Changed:* the copy-to-chat handoff became the design; the dashboard has no write access.
7. **30 July: the master CV's own template had drifted from the rules.** *Changed:* rules are fixed at the source file, not only in the newest output.
8. **5 August: silent filters removed the best job.** A bare word in the exclusion list, a filter inside the scraper and tech-qualified search terms could each drop a good match before scoring, and nothing recorded it. *Changed:* cast wide, then score; exclusions became a demotion; every reject is logged with a reason.
9. **5 August: rotating short links would have created six duplicates.** *Changed:* deduplication on the posting's identity (normalised company + title), not only its URL.

---

## All 33 fixes

<details>
<summary>Show the full list (date – what broke – what it taught)</summary>

1. 10 Jul – design relied on automatic form submission and paid per-task model calls – keep a human before every application; keep the model inside the run.
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
15. 18–19 Jul – stray indent on every block after the first – `\noindent` in the block definition; measure rendered output.
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
33. 28 Sep – a hidden bar rendered as an empty box, and the empty tray peeked out – CSS `display` rules can override `hidden`; test the empty states.

</details>
