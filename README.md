<!-- BANNER: pending my approval -->

<!-- HOOK: 2–4 sentences, WALID writes -->

An agent-run job search: Claude routines find postings through MCP connectors, score them against your CV, prepare tailored applications and track replies, all around one SQLite file and one dashboard, with no model API key.

<!-- Stat badges: every number is counted from the repo -->
<p>
  <a href="routines/"><img src="https://img.shields.io/static/v1?label=routines&message=3" alt="routines: 3"></a>
  <a href="core/"><img src="https://img.shields.io/static/v1?label=core%20Python%20modules&message=5" alt="core Python modules: 5"></a>
  <a href="docs/SETUP.md#2-requirements"><img src="https://img.shields.io/static/v1?label=third-party%20dependencies&message=0" alt="third-party dependencies: 0"></a>
  <a href="docs/SETUP.md#5-connectors"><img src="https://img.shields.io/static/v1?label=connectors&message=3" alt="connectors: 3"></a>
  <a href="docs/STORY.md#all-33-fixes"><img src="https://img.shields.io/static/v1?label=documented%20fixes&message=33" alt="documented fixes: 33"></a>
</p>

<p>
  <a href="docs/SETUP.md"><img src="https://img.shields.io/static/v1?label=Use%20it&message=docs%2FSETUP.md" alt="Use it: docs/SETUP.md"></a>
  <a href="docs/STORY.md"><img src="https://img.shields.io/static/v1?label=The%20story&message=docs%2FSTORY.md" alt="The story: docs/STORY.md"></a>
</p>

---

<a name="story"></a>
<p><a href="#story"><img src="docs/readme/zones/story.svg" alt="01 The story: why it exists and how it grew" width="100%"></a></p>

<a name="story-short"></a>
<p><a href="docs/STORY.md"><img src="docs/readme/labels/story-short.svg" alt="Why and how it grew · the short version, then the full build story"></a></p>

<details>
<summary>Read the short version</summary>

<br>

<!-- WALID: short origin story, 5–8 sentences -->

The full build story, version by version, with the bugs that shaped it: **[docs/STORY.md](docs/STORY.md)**.

</details>

---

<a name="features"></a>
<p><a href="#features"><img src="docs/readme/zones/features.svg" alt="02 Features: search, review, tailor, track" width="100%"></a></p>

<a name="dashboard"></a>
<p><a href="#dashboard"><img src="docs/readme/labels/dashboard.svg" alt="The dashboard · review jobs, replies and next steps on one page"></a></p>

<details>
<summary>More about the dashboard</summary>

<br>

<a href="docs/SETUP.md#3-install-and-run-the-demo"><img src="docs/readme/dashboard-main.png" alt="Dashboard overview with application counters, search radar, inbox and top matches (demo data)" width="100%"></a>

One HTML file with four tabs: overview, inbox, search radar and all jobs. Every action (approve, discard, tailor, search, interview prep) copies a ready-made prompt for the Claude chat. The page itself has no write access, so a human stays in the loop and nothing changes without you seeing it.

<a href="core/dashboard_template.html"><img src="docs/readme/dashboard-job-detail.png" alt="Job detail panel with the invitation, mail history, skill match and copy-to-chat buttons (demo data)" width="100%"></a>

The job detail panel: match and freshness, the invitation and mail history from the reply scan, the skill match, and the next step as a prompt to copy.

<sub>Both screenshots use the included demo data. All companies are fictional.</sub>

</details>

<a name="search"></a>
<p><a href="#search"><img src="docs/readme/labels/search.svg" alt="Search and scoring · two sources, few filters, every reject logged"></a></p>

<details>
<summary>More about search and scoring</summary>

<br>

- **Two job sources, one pass.** An Apify job-listing actor does a few broad sweeps; the Indeed connector runs many narrow queries. Results are deduplicated on URL **and** on normalised company + title, because some short links change between requests.
- **"Cast wide, then score."** Pre-scoring filters are few and specific, exclusions only demote, and every rejected posting is written to a log with a reason.
- **Scoring by the agent, not a script.** Each new job gets a 0–100 match score, matching and missing skills and a one-line reason, judged against a snapshot of your CV. Jobs under the threshold are never stored.
- **Cheap by design.** The CV is only re-read when its sha256 hash changes, no script calls a model, and the one paid source gets a spending cap on every call.

</details>

<a name="tailoring"></a>
<p><a href="#tailoring"><img src="docs/readme/labels/tailoring.svg" alt="Tailored applications (optional) · a CV and a cover letter per job"></a></p>

<details>
<summary>More about tailored applications</summary>

<br>

A queued job becomes a package: a LaTeX CV cut to a hard page limit and an editable `.docx` cover letter, in the language you set in the config. The rules for both live in one routine file: truthful to your CV, no claimed specialization, content chosen per posting, layout that survives applicant-tracking systems, and a letter that tells a short story instead of listing courses.

</details>

<a name="replies"></a>
<p><a href="#replies"><img src="docs/readme/labels/replies.svg" alt="Reply tracking (optional) · invited, waiting or rejected"></a></p>

<details>
<summary>More about reply tracking</summary>

<br>

A mailbox scan by company name classifies each application as *invited*, *waiting* or *rejected* and shows it in the dashboard's inbox, with a follow-up reminder after 14 days. It only writes its own status file, never the database.

</details>

---

<a name="built"></a>
<p><a href="#built"><img src="docs/readme/zones/built.svg" alt="03 How it's built: guardrails and architecture" width="100%"></a></p>

<a name="guardrails"></a>
<p><a href="#guardrails"><img src="docs/readme/labels/guardrails.svg" alt="Guardrails · nothing deleted, every write checked"></a></p>

<details>
<summary>More about the guardrails</summary>

<br>

- Rows in `jobs.db` are never deleted; only their status changes.
- Every file write is checksummed and read back; stale SQLite journals are cleaned up before connecting.
- The dashboard build refuses a truncated template, verifies its own output and prints `OK` or `BUILD FAILED`. No routine reports success without `OK`.
- Nothing is ever submitted automatically: you apply yourself.

</details>

<a name="architecture"></a>
<p><a href="#architecture"><img src="docs/readme/labels/architecture.svg" alt="Architecture · routines, connectors, one data folder"></a></p>

<details>
<summary>More about the architecture</summary>

<br>

```mermaid
flowchart LR
    subgraph Claude["Claude (subscription): scheduled tasks / chat"]
        S["search-jobs"]
        T["process-tailor-queue<br/>(optional)"]
        M["scan-mail-status<br/>(optional)"]
    end

    subgraph MCP["MCP connectors"]
        A["Apify<br/>job-listing actor"]
        I["Indeed"]
        G["Gmail"]
    end

    subgraph Data["data/ (single source of truth)"]
        DB[("jobs.db<br/>jobs · applications · responses")]
        DESC["descriptions.json"]
        CV["cv_profile/<br/>snapshot + sha256 gate"]
        Q["tailor_queue.json"]
        MS["mail_status.json"]
        PK["packages/&lt;job&gt;/<br/>CV .tex/.pdf · cover letter .docx"]
        LOG["skipped_log.json"]
    end

    CFG["config/<br/>search_keywords.json<br/>cv_emphasis.json"] --> S
    A --> S
    I --> S
    S -- "INSERT if score ≥ 50" --> DB
    S --> DESC
    S --> LOG
    CV --> S
    CV --> T
    Q --> T
    T -- "status UPDATE only" --> DB
    T --> PK
    G --> M
    DB -. "read-only" .-> M
    M --> MS

    DB --> EX["core/export_dashboard_data.py"]
    DESC --> EX
    PK --> EX
    Q --> EX
    MS --> EX
    EX --> BD["core/build_dashboard.py<br/>self-verifying, prints OK"]
    BD --> HTML["data/dashboard.html<br/>published as an artifact"]
    HTML -. "copy a prompt,<br/>paste into chat" .-> Claude
```

The Python side is small on purpose: five standard-library modules. The "program" is the three routine files in [`routines/`](routines/), which a Claude agent follows step by step.

| Piece | Role |
|---|---|
| [`routines/search-jobs.md`](routines/search-jobs.md) | Search both sources, filter, dedupe, score, insert, rebuild |
| [`routines/process-tailor-queue.md`](routines/process-tailor-queue.md) | *Optional.* Tailored CV + cover letter per queued job |
| [`routines/scan-mail-status.md`](routines/scan-mail-status.md) | *Optional.* Classify replies from the mailbox |
| [`core/job_database.py`](core/job_database.py) | SQLite schema + CRUD, stale-journal cleanup, `verify()` |
| [`core/safe_io.py`](core/safe_io.py) | Write → fsync → checksum → re-read → retry |
| [`core/export_dashboard_data.py`](core/export_dashboard_data.py) | Read-only export of the data layer to JSON |
| [`core/build_dashboard.py`](core/build_dashboard.py) | Embed the data into the template and verify the result |
| [`core/dashboard_template.html`](core/dashboard_template.html) | The dashboard: one file, no libraries, no network calls |
| [`demo/generate_demo_data.py`](demo/generate_demo_data.py) | A complete fictional data layer for trying it out |

</details>

---

<a name="run"></a>
<p><a href="#run"><img src="docs/readme/zones/run.svg" alt="04 Run it yourself: setup guide, demo data first" width="100%"></a></p>

<a name="setup"></a>
<p><a href="docs/SETUP.md"><img src="docs/readme/labels/setup.svg" alt="Setup guide · requirements, your CV, connectors, scheduled tasks"></a></p>

Start with the demo data, then follow **[docs/SETUP.md](docs/SETUP.md)** to connect your own CV, search settings, connectors and scheduled tasks.

Standalone prompts, to paste into any Claude chat without the pipeline: [set up your profile](docs/prompts/set-profile.md), [job search](docs/prompts/search-jobs.md), [CV tailoring](docs/prompts/cv-tailoring.md), [motivation letter](docs/prompts/motivation-letter.md).

---

<a name="notes"></a>
<p><a href="#notes"><img src="docs/readme/zones/notes.svg" alt="05 Honest notes: limitations, security, license" width="100%"></a></p>

<a name="limitations"></a>
<p><a href="#limitations"><img src="docs/readme/labels/limitations.svg" alt="Known limitations · what it doesn't do, one line each"></a></p>

<details>
<summary>Show the known limitations</summary>

<br>

- It needs a Claude plan with scheduled tasks and connectors, and the Claude desktop app with access to this folder; nothing runs on its own.
- Not every connector and scheduled-task step in the setup guide has been checked click by click in the app yet.
- Both job sources are mandatory: if Apify or Indeed fails, the whole search run counts as failed.
- The Apify job-listing actor you choose may charge per result; every call has a spending cap, but the cost depends on that actor.
- The Indeed connector was free on my plan; check yours.
- Match scores are Claude's judgment in each run, not a formula, so the same posting isn't guaranteed the same score twice.
- There are no automated tests, and the company + title deduplication lives in the routine text, not in code.
- The dashboard is a snapshot: changes only show after a rebuild and republish.
- The dashboard's layout overflows sideways at phone width.
- In light mode, a faint shadow strip shows at the right edge of the dashboard.
- Without a LaTeX engine, tailored CVs stay as `.tex` source; no PDF is made.
- The dashboard's interface is English only; the documents follow `output_language` in the config.

</details>

<a name="security"></a>
<p><a href="#security"><img src="docs/readme/labels/security.svg" alt="Security scope · what stays on your machine and what Claude sees"></a></p>

<details>
<summary>Show the security scope</summary>

<br>

Everything runs on your machine, inside your Claude app. Your CV and job data stay in `profile/` and `data/`, which are gitignored, so nothing from them is uploaded to this repository. Claude reads them while a run is going. The job postings come from scraping, you never type them in.

</details>

<a name="license"></a>
<p><a href="#license"><img src="docs/readme/labels/license.svg" alt="License · for reading only, not for reuse"></a></p>

No license file on purpose: this repo is for reading only, not for reuse.
