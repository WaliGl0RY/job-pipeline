---
name: process-tailor-queue
description: OPTIONAL. Apply queued status changes, write one tailored CV (LaTeX) and one editable cover letter (.docx) per queued job, archive packages of jobs already applied to, rebuild and republish the dashboard
---

Optional routine. Keep this file as the single copy of the tailoring rules: your scheduled task should only point here and read it at runtime (see the README). A copy pasted into the task prompt drifts out of date and then silently ignores the rules you change here.

You are processing the tailoring queue for this job pipeline. Work inside the repository root (call it BASE). Never delete rows from any table: status/notes updates only. Every document must be **strictly truthful to the profile**: never invent skills, experience, grades or certificate content.

## Inputs (read these first)
- `data/tailor_queue.json`: JSON array of `{"job_id": <int>, "requested_at": <iso>}`. May be missing or empty.
- `data/status_changes.json`: OPTIONAL JSON array of `{"job_id": <int>, "new_status": <str>, "changed_at": <iso>}`.
- `data/jobs.db`: use `core/job_database.py`'s `JobDatabase` (`db.cursor.execute(...)` then `db.commit()`) for every write.
- `data/descriptions.json`: `{"<job_id>": {"company", "title", "description"}}`.
- `data/cv_profile/cv_skills_snapshot.json` + `cv_snapshot_meta.json`: the profile. If the sha256 of `profile/master_cv.tex` differs from the stored hash, regenerate the snapshot first (same gate as in `routines/search-jobs.md`).
- `profile/master_cv.tex`: the master CV. It stays **complete and uncut**: only the tailored per-job output gets cut. Its preamble is the canonical LaTeX template (start from `templates/master_cv.example.tex`).
- `config/cv_emphasis.json`: job type → sections/skills to emphasise. A starting hint only.
- `config/search_keywords.json` → `target.output_language`: the language of every document you write (CV and cover letter). If the field is missing, use the language of the posting.

## Reliability
Writes on synced/network folders can silently truncate, and a stale SQLite `-journal` can make later connects fail with `disk I/O error`. Use `JobDatabase` for all jobs.db writes and `core/safe_io.py`'s `safe_write_text()` for every JSON/text file (status_changes.json, tailor_queue.json, meta.json). If a PDF/DOCX in a package is locked by an open viewer, retry once, then write under a new name (`..._NEW.pdf`) and say clearly in the report which file is current.

## Step A: apply queued status changes
If status_changes.json is non-empty: for each entry, check that `new_status` is one of `discovered`, `approved_for_application`, `applied`, `skip`, `archived`, then `UPDATE jobs SET status=? WHERE id=?`. If the new status is `applied` and no applications row exists, `INSERT INTO applications (job_id, status) VALUES (?, 'submitted')`. Never DELETE. Overwrite status_changes.json with `[]`.

## Step B: one application package per queued job
For each queue entry, in order:
1. Load the job row and its description. If there is no description, try to fetch the real posting (web search/fetch, or the Indeed MCP's `get_job_details`). If nothing is available, leave the entry in the queue with `"error": "no description"` and move on.
2. Pick the best-fitting job type from cv_emphasis.json by reading the description.
3. Create `data/packages/<job_id>_<company-slug>/` and write:

**`cv_tailored.tex`: actually tailor it, don't just relabel the intro.** Write it in `target.output_language`.
- **No claimed specialization.** Never claim a specialization, focus or qualification that isn't in the CV. Describe interests as interests.
- **Abbreviations:** the first time, write the full term with the abbreviation in brackets (e.g. "Test-Driven Development (TDD)"); after that, use only the abbreviation. In the intro paragraph, which has no parentheses, write the full term only.
- **Content selection is a judgment call per posting.** Decide which projects, skills and certifications earn a place for *this* job. Cut the least relevant bullets first.
- **Max 2 pages, hard limit, on the tailored output only.** A tailored CV as long as the master is a bug, not a pass.
- **Never let a heading+list block split across a page.** Wrap every entry (heading plus its bullet list) in the `cvblock` environment from the template. A minipage is an atomic box: if it doesn't fit, TeX moves the whole block to the next page. The environment MUST start with `\noindent` (`\newenvironment{cvblock}{\noindent\begin{minipage}{\linewidth}}{\end{minipage}}`): without it, every block except the one right after a `\section` picks up a stray paragraph indent, which misaligns the title and, through `\hfill`, the date on the same line.
- **Typography:** 1.5 cm margins, `ragged2e`, `\hyphenpenalty=10000` and `\exhyphenpenalty=10000` (words wrap whole instead of breaking), itemize set `\RaggedRight` so disabling hyphenation doesn't create stretched gaps. The template already does all of this.
- **Intro paragraph:** several short, plain sentences: (1) who you are / status, (2) the relevant experience for this posting, (3) interests or soft skills, (4) languages. No parentheses, no course-catalogue references, no claims of a "specialisation" or "focus" that the profile doesn't state.
- **Certifications and skills are separate sections.** Certificate details come from the actual certificate, never invented. Don't annotate completed certificates with "(completed)"; only mark things still in progress.
- **Tone:** write like a person. No rhetorical dashes as sentence connectors (a well-known AI-writing tell; dashes stay only for date ranges), no salesy phrasing. Bold the concrete technology or deliverable in each bullet, not whole clauses, so the page scans in a few seconds.
- **One wildcard line:** keep one authentic detail unrelated to the job's core requirements (an interest, a language, a side project) so the CV doesn't read like a template.

**`cover_letter.docx`: native Word file, not PDF, not LaTeX** (you will edit it by hand before sending; use Claude's docx skill).
- Write it in `target.output_language`. Max one page.
- Sender block from the snapshot's `personal` fields; recipient; date; bold subject line "Application for <job title>"; salutation; 3 short paragraphs; closing; name. Same order every time.
- **Salutation:** if the posting names a contact person, greet them by name; otherwise use a general greeting.
- **Research the company first** (its posting and its own site) and open with one specific, true connection between the profile and this company. No generic praise.
- **Name 2–3 concrete tasks from the posting** and connect them to real items in the profile.
- **Narrative, not enumeration:** weave 1-2 concrete proof points from the profile into a short story about what you enjoy or why it matters. If the posting asks for something the profile doesn't have, one honest sentence about wanting to learn it is fine.
- **Only completed work as proof points:** completed courses, projects or jobs, never planned ones.
- **No claimed specialization.** Never claim a specialization, focus or qualification that isn't in the CV. Describe interests as interests.
- **Abbreviations:** the first time, write the full term with the abbreviation in brackets; after that, use only the abbreviation.
- **Simple language:** short sentences, everyday vocabulary.
- **Closing:** availability and wanting to talk. Write start dates so they can't be read as end dates (e.g. "from 01.10." not "to 01.10."). Don't mention documents the posting didn't ask for.
- ATS-safe: plain paragraphs, no text boxes, tables or content in headers/footers, standard fonts.

4. **Compile only if a LaTeX engine is available** (`tectonic`, or `pdflatex` run twice). Put by-products in `build/` inside the package, never next to the PDF. Name the deliverable `CV_<Company>.pdf`. Check the page count (`pdfinfo`), and check reading order with `pdftotext -layout` (a garbled two-column block gets simplified to one column). If no engine is installed, ship the `.tex` and set `pdf_compiled: false`.
5. Write `meta.json` via `safe_write_text`: `{"job_id", "company", "title", "generated_at", "files", "pdf_compiled", "cv_pages", "notes"}`. `notes` is an append-only log of what changed and why.
6. Append ` | package created <YYYY-MM-DD>: data/packages/<folder>` to `jobs.notes`.

## Step C: clear the queue
Rewrite tailor_queue.json keeping only failed entries with their `error` field.

## Step C2: archive packages of jobs already sent
For every job with status `applied` whose package isn't under `data/packages/_archived/` yet: move the folder there (move, never delete) and append ` | package archived <YYYY-MM-DD>` to `jobs.notes`.

## Step D: rebuild and republish
Run `python core/build_dashboard.py`. Only if it prints `OK`: republish the artifact from `config/dashboard_artifact.json` (never create a second one) and spot-check the published file for a closed `</script>` tag.

## Report
Lead with any Step D failure. Then: packages generated (job id, company, PDF yes/no, CV page count), status changes applied, packages archived, queue entries left. Flag as an error, not a silent pass: a CV over 2 pages, a cover letter that isn't a .docx or runs over one page, a missing `\noindent` in `cvblock`, a heading+list block split across a page, mixed certification/skill sections, a cover letter without a company-specific opening, any locked or stale file.
