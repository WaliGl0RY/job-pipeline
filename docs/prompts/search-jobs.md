# Prompt template: job search

## 1. What this prompt does

It runs one job-search pass: two job sources, a few deliberate hard filters, deduplication against the jobs you already know, and a match score for every new posting, judged against your CV by Claude itself. It returns only the jobs worth reviewing, plus a log of everything it rejected and why. [`routines/search-jobs.md`](../../routines/search-jobs.md) is the same logic wired into this repo's database and dashboard; this template works on its own in a Claude chat or scheduled task.

## 2. What you need to fill in

- $\color{orange}{\texttt{\{\{ROLE\_TYPE\}\}}}$: the kind of position you want. Example: `working student`
- $\color{orange}{\texttt{\{\{YOUR\_FIELD\}\}}}$: your subject or professional field. Example: `computer science`
- $\color{orange}{\texttt{\{\{YOUR\_CITY\}\}}}$: the city you search around. Example: `Cologne`
- $\color{orange}{\texttt{\{\{RADIUS\_KM\}\}}}$: the maximum distance from that city, in km. Example: `40`
- $\color{orange}{\texttt{\{\{COUNTRY\_CODE\}\}}}$: two-letter country code for the Indeed search. Example: `DE`
- $\color{orange}{\texttt{\{\{NEARBY\_PLACES\}\}}}$: places inside your radius that always pass (spelling variants included). Example: `Köln, Cologne, Bonn, Leverkusen, Hürth`
- $\color{orange}{\texttt{\{\{EXCLUDED\_PLACES\}\}}}$: places that never pass, even if a posting looks close. Example: `Dortmund, Aachen`
- $\color{orange}{\texttt{\{\{MAX\_DAYS\_POSTED\}\}}}$: the oldest posting you still want, in days. Example: `10`
- $\color{orange}{\texttt{\{\{BROAD\_SWEEP\_TERMS\}\}}}$: 2-4 bare employment-type terms for the broad source. Example: `"Working Student", "Werkstudent"`
- $\color{orange}{\texttt{\{\{YOUR\_KEYWORDS\}\}}}$: many narrow queries for the narrow source. Example: `"Working Student Data", "Working Student Python", "Working Student IT Support"`
- $\color{orange}{\texttt{\{\{ROLE\_MUST\_CONTAIN\}\}}}$: words of which at least one must appear in title or description. Example: `working student, werkstudent, student assistant`
- $\color{orange}{\texttt{\{\{EXCLUDE\_TERMS\}\}}}$: specific phrases that demote a posting. Example: `sales manager, recruiting, accounting`
- $\color{orange}{\texttt{\{\{OVERRIDE\_TOKENS\}\}}}$: words that cancel an exclusion because the work may still fit. Example: `data, software, python, automation, support`
- $\color{orange}{\texttt{\{\{APIFY\_ACTOR\_ID\}\}}}$: any Apify actor that returns job listings. Example: `<username>/<job-listing-actor>`
- $\color{orange}{\texttt{\{\{APIFY\_BUDGET\_USD\}\}}}$: hard spending cap per actor call, in USD. Example: `0.50`
- $\color{orange}{\texttt{\{\{YOUR\_CV\}\}}}$: your CV or a structured profile (skills, certificates, projects, experience). Example: `the attached master_cv.tex` or a pasted skills list
- $\color{orange}{\texttt{\{\{KNOWN\_JOBS\}\}}}$: the jobs you already have, for deduplication (URL, company, title). Example: `data/jobs.db` or a pasted list
- $\color{orange}{\texttt{\{\{MIN\_MATCH\_SCORE\}\}}}$: the score below which a job is dropped. Example: `50`
- $\color{orange}{\texttt{\{\{OUTPUT\_LANGUAGE\}\}}}$: the language for the reasoning, notes and report, your choice. Example: `English`

## 3. The prompt

```text
You are running a job-discovery pass for a {{ROLE_TYPE}} position in {{YOUR_FIELD}}, within {{RADIUS_KM}} km of {{YOUR_CITY}}. Never delete or overwrite jobs that are already known: only add new ones. Do all reasoning (search-term judgment, filtering, scoring) yourself in this turn. Do not call any other model or scoring script.

Operating principle: cast wide, then score. Search broadly and let the match score do the narrowing. Every filter before scoring is a place where a good job disappears without anyone noticing, so the filters are deliberately few, deliberately specific, and everything they reject gets logged. Do not add cleverness to the search stage.

INPUTS
- My profile: {{YOUR_CV}}
- Jobs I already know: {{KNOWN_JOBS}}. Read every URL, company and title; you need all three to deduplicate.

STEP A: SEARCH BOTH SOURCES (both are mandatory)
Query both sources on every run. They are not alternatives. If a source errors or returns nothing, the run has failed: say so in the first line of your report, name the source and the exact error, and do not present the other source's results as a complete pass.

A1. Apify (primary source, run it first). Call the actor {{APIFY_ACTOR_ID}} once per term in: {{BROAD_SWEEP_TERMS}}. Map location {{YOUR_CITY}}, the radius and the recency window onto the actor's own input fields (check its input schema). Set a hard spending cap of {{APIFY_BUDGET_USD}} USD on every call and do not raise the item count without a reason. Keep the terms bare: do not append technology words, and do not use the actor's category or job-function filters. Those filter before you ever see a posting and silently remove roles filed under an unexpected department.

A2. Indeed MCP. Run search_jobs once per query in: {{YOUR_KEYWORDS}}, with location {{YOUR_CITY}} and country code {{COUNTRY_CODE}}. Indeed returns about 10 results per query without pagination, which is why this list is long and narrow: the opposite of the broad sweeps. Heavy overlap between queries is expected.

STEP B: HARD FILTERS, in this order
1. Date: keep only postings at most {{MAX_DAYS_POSTED}} days old. Compute the age from the posting date, not from a relative string.
2. Location: the place must be in {{NEARBY_PLACES}} or within {{RADIUS_KM}} km of {{YOUR_CITY}}, and must not be in {{EXCLUDED_PLACES}}.
3. Employment type: the title OR the description must contain one of {{ROLE_MUST_CONTAIN}}. Check both: some sources return truncated titles, and the real title only appears in the description.
4. Exclusion, softly: if the title or description contains any of {{OVERRIDE_TOKENS}}, skip the exclusion check and send the job to scoring. Otherwise drop jobs whose title contains any of {{EXCLUDE_TERMS}}. The match score reads the whole description and is a far better judge than a word in a title.

Log every rejected posting with: title, company, location, url, posting date, and a reason (too_old, location, wrong_role_type, excluded_term, duplicate_url, duplicate_company_title, score_<n>). This log is the only way to see what the filters are eating.

STEP C: DEDUPLICATE ON URL AND ON COMPANY + TITLE
1. Same URL as a known job: skip.
2. Same normalised company + title as a known job: skip. Some short links change on every request, so URL-only deduplication lets the same posting through again. Normalise by lowercasing, removing gender markers such as (m/f/d) or (all genders), removing punctuation and collapsing whitespace.
3. Also deduplicate within this batch: the same job often arrives from both sources and from several queries. Keep the more stable URL.

STEP D: SCORE EACH NEW JOB
1. Read the full description (fetch it if the search result was truncated).
2. Score it against my profile: match_score 0-100 (your judgment), matching_skills, missing_skills, and one short sentence of reasoning. Write the reasoning, the notes and the report in {{OUTPUT_LANGUAGE}}.
3. Score the work described, not the department it sits in. A role filed under a non-technical department that actually consists of data analysis, scripting, automation or IT support is a strong match if my profile fits the tasks.
4. If there is a clear, actionable gap (a named tool or certificate I don't have), add one concrete suggestion to the reasoning instead of "skills don't fully match".
5. Drop jobs with match_score below {{MIN_MATCH_SCORE}}; log them with reason score_<n>.
6. For each remaining job, record: title, company, url, location, source, posting date, days posted, freshness (100 - days_posted * 100/30, minimum 0), match_score, matching and missing skills, priority tier (tier1 if score >= 80, tier2 if >= 60, otherwise tier3), and your reasoning.

REPORT
Lead with any failure (a source that errored or returned nothing). Then: candidates found per source, stated separately; how many passed the hard filters; how many were new after deduplication; how many were dropped below {{MIN_MATCH_SCORE}}; the top 3 new jobs (title, company, score, one-line reasoning); then the full list of new jobs and the reject log. Finish with skill gaps that recur across several jobs, and flag any filter that rejected an unusual number of candidates: that usually means the filter needs tuning, not that the market is empty.
```

## 4. Why it's written this way

- **"Cast wide, then score."** An early version used tech-qualified search terms, a job-function filter inside the scraper, and a bare word in the exclusion list. Together they silently dropped one of the best-fitting postings: a data/AI role filed under a customer-service department, whose title contained the excluded word. The fix was bare search terms, no source-side category filters, and scoring the whole description instead of guessing from the title.
- **Exclusion is a demotion, not a kill switch.** Substring exclusions match more than you think (a short word also matches inside longer job titles). The override tokens send anything that might contain real technical work to scoring, where the full description is read.
- **Every reject is logged.** A filter that discards silently can lose good jobs for a whole cycle before anyone notices. The log makes the filters auditable.
- **Both sources are mandatory, and a dead source is a failed run.** Otherwise one source can stop returning results without anyone noticing, and every run quietly searches only part of the market. Reporting counts per source makes that visible.
- **Broad sweeps for one source, narrow queries for the other.** The broad source matches keywords against the description too, so bare terms find roles with unpredictable titles. Indeed caps each query at about 10 results, so it needs many specific queries instead.
- **Deduplicate on company + title, not just URL.** Rotating short links let the same posting through with a new URL on each run; one test run would have added six duplicates.
- **Check title and description for the role type.** Some sources return truncated titles; a title-only check misses real matches.
- **A short recency window.** Casting wide multiplies the candidates, so the window keeps each run reviewable, and postings found late were often already closed.
- **Score the work, not the department.** Many good-fit roles sit in departments whose names suggest nothing technical.
- **A score gate, not a manual cull.** Jobs below the threshold are never stored, so the review list only holds jobs worth reading.
- **No external model calls, and a spending cap.** An earlier version paid per request for scoring. Doing the judgment inside the agent run removes that cost; the only paid part (the scraper) gets a hard cap on every call.
- **Freshness in the ranking.** Replies are more likely when you apply early, so recent postings rank higher at equal match.
