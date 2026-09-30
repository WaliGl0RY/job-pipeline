---
name: search-jobs
description: Search new jobs via BOTH the Apify actor and the Indeed MCP, apply the hard filters, dedupe, score against the CV snapshot, insert jobs scoring >= 50 into jobs.db, rebuild and republish the dashboard
---

You are running a job-discovery pass for this job pipeline. Work entirely inside the repository root (call it BASE). Never delete or overwrite existing rows in jobs.db: only INSERT new ones. No paid APIs beyond the Apify actor configured below, no ANTHROPIC_API_KEY: all reasoning (search-term judgment, filtering, scoring) happens in this agent turn, not in a script or an external model call.

**Operating principle: cast wide, then score.** Search broadly and let `match_score` do the narrowing. Every pre-scoring filter is a place where a good job disappears without anyone noticing, so the pre-scoring filters are deliberately few, deliberately specific, and everything they reject gets logged. Do not add cleverness to the search stage.

## Inputs (read these first)
- `BASE/config/search_keywords.json`: the ONLY source of search terms and hard filters. `broad_sweeps.apify` are the Apify queries, `priority_searches.indeed` are the Indeed queries, `target` says who and where, and every field under `hard_filters` applies literally. Read the `_comment` / `_note` fields too: they record why each value is what it is. Do not paraphrase or shortcut these filters.
- `BASE/data/jobs.db`: SQLite (tables `jobs`, `applications`, `responses`). Read all existing `url`, `company` and `title` values first: you need all three to dedupe (Step C).
- `BASE/data/descriptions.json`: existing job descriptions keyed by job id.
- `BASE/data/cv_profile/cv_skills_snapshot.json`: applicant profile (skills, certifications, projects, work experience) used for scoring. Regenerated from the master CV whenever the stored hash no longer matches; never hand-edit it.
- `BASE/data/cv_profile/cv_snapshot_meta.json`: `{"master_cv_sha256": <str>, "snapshot_generated_at": <iso>}`.
- `BASE/profile/master_cv.tex`: the master CV (source of truth the snapshot is derived from).

## Step A: CV snapshot gate (keeps the run cheap)
Compute the sha256 of `profile/master_cv.tex` and compare it to `master_cv_sha256` in cv_snapshot_meta.json.
- If it matches: go straight to Step B. Do NOT read master_cv.tex or touch the snapshot.
- If it differs: read master_cv.tex fully, re-extract personal / education / certifications / skills / projects / work_experience / interests into cv_skills_snapshot.json (keep the existing schema), then overwrite cv_snapshot_meta.json with the new hash and the current UTC timestamp. Only then proceed.

## Step B: search BOTH sources (both are mandatory)
Query **both** the Apify actor **and** the Indeed MCP on every run. They are not alternatives. If a source errors or returns nothing, that is a **failed run**: say so in the first line of the report, state which source failed and the exact error, and do not present the other source's output as a complete pass.

**B1: Apify (primary source, run it first).**
Call the actor in `apify.actor_id` through the Apify MCP `call-actor` tool, once per entry in `broad_sweeps.apify`, passing `apify.actor_input` as the base input plus the sweep term in the actor's keyword field. Read the results with `get-dataset-items` using the returned `datasetId`.
- The sweep terms are intentionally bare. Do **not** append tech qualifiers.
- Do not add actor-level category/function filters: they filter before you ever see a posting, which silently removes cross-functional roles.
- Cost control: set `apify.max_total_charge_usd` on every call as a hard cap. Do not raise the item count without a reason.

**B2: Indeed MCP.**
Run every entry in `priority_searches.indeed` via `search_jobs(search=<term>, location=indeed.location, country_code=indeed.country_code)`. Indeed returns about 10 results per query with no pagination, which is why that list is long and narrow. Expect heavy overlap between queries; that is fine.

**B3: apply the hard filters.** For each candidate from either source, in this order:
1. **Date.** `days_posted <= max_days_posted`. Discard anything older. Compute it from the posted date, not from a relative string.
2. **Location.** Must be in `location_include` (or within `target.location_radius_km` of `target.home_location`) and not in `location_exclude`.
3. **Employment type.** Title **or description** must contain one of `must_contain_one_of`. Check both, not just the title.
4. **Exclusion, softly.** If title or description contains any `title_exclude_override.tokens` entry, **skip the exclusion check entirely** and send the job to scoring. Otherwise apply `title_exclude`. This ordering is deliberate: `match_score` reads the whole description and is a far better judge than a substring match on a title.

**B4: log every reject.** Append each discarded candidate to `BASE/data/skipped_log.json` as `{"run": <iso date>, "title", "company", "location", "url", "posted_date", "reason"}`, where reason is one of `too_old`, `location`, `not_target_role`, `title_exclude`, `dup_url`, `dup_company_title`, `score_<n>`. Write it with `core/safe_io.py`'s `safe_write_text()`. This log is the only way to audit what the filters are eating: a filter that discards silently is how good jobs go missing for a whole cycle. Keep the last 3 runs and drop older entries so the file stays small.

## Step C: dedupe on URL *and* on company+title
1. **URL match** against every existing `url` in jobs.db → skip.
2. **Normalised company + title match** against every existing row → skip. This check is not optional: some short links rotate on every request, so the same posting comes back with a fresh URL each run and URL-only dedupe lets it through. Normalise by lowercasing, stripping gender markers such as `(m/f/d)` / `(m/w/d)` / `(all genders)` and punctuation, and collapsing whitespace.
3. Also dedupe **within** the batch: the same job legitimately arrives from both sources and from several Indeed queries. When both exist, keep the more stable URL.

## Step D: score, then write only if match_score >= min_match_score
For each new job:
1. Read its full description (fetch it if the search result was truncated).
2. Score it yourself, in this turn, against cv_skills_snapshot.json: no script, no API call. Produce `match_score` (0-100, your judgment), `matching_skills` (list), `missing_skills` (list), and one short sentence of reasoning. Write the reasoning and any notes in `target.output_language` from the config (if missing, English).
3. Score the **work described**, not the department it sits in. A role filed under a non-technical department that actually consists of data analysis, dashboards, scripting, automation or IT support is a strong match if the profile fits the tasks.
4. If there's a clear, actionable gap (e.g. the job wants a certification that the profile lists as in progress), put a concrete suggestion into the notes, not a generic "skills don't fully match".
5. **Match-score gate:** if match_score < `min_match_score` (default 50), do NOT insert the job. Count it for the report and log it to skipped_log.json with reason `score_<n>`. No row, no description entry.
6. If match_score >= the gate: insert via `core/job_database.py`'s `JobDatabase.add_job()` with title, company, url, location, job_board, posted_date, days_posted, freshness_score (`100 - days_posted*(100/30)`, floor 0), match_score, required_skills, matching_skills, missing_skills, priority_tier (`tier1` if match_score >= 80, `tier2` if >= 60, `tier3` otherwise), status `discovered`, notes = your reasoning + any gap suggestion. `add_job()` returns the new row id. Never touch existing rows. If you connect with raw sqlite3 instead, call `core/safe_io.py`'s `clear_stale_sqlite_journal(db_path)` first. After the batch, call `db.verify()` and only proceed to Step E if it returns True; otherwise stop and report the DB issue.
7. Add the description to descriptions.json (only for jobs that passed the gate) keyed by the new job id: `{"company", "title", "description"}`. Write it with `safe_write_text()`, not a bare write. Re-read the file afterwards and confirm the new ids are present and no `"None"` key was created.

Note: `core/export_dashboard_data.py` also hides any `discovered` job below the threshold as a second safety net, but the primary mechanism is never inserting such jobs in Step D.5.

## Step E: rebuild and republish
Run `python core/build_dashboard.py` (with `PYTHONIOENCODING=utf-8`). The script verifies its own output (checksums the write, re-reads it, checks the embedded `<script>` block is balanced and the job count round-trips) and exits non-zero with `BUILD FAILED` if anything looks truncated or mismatched. Treat that as blocking: do NOT publish, and do NOT report the dashboard as rebuilt, unless the script printed a line starting with `OK`. If it fails, report the exact error instead of retrying blindly more than once.

Then read `BASE/config/dashboard_artifact.json` (`{"url", "build", "html"}`) and republish the file in `html` to the artifact in `url`, with the tool your Claude surface provides for artifacts. Never create a second artifact. After publishing, spot-check the published file for a closed `</script>` tag near the end.

## Report
Lead with any failure: a source that errored in Step B, a false `db.verify()` in Step D, or a failed build check in Step E goes in the first line, not at the end.

Then: candidates found **per source** (Apify vs Indeed, stated separately, so a silently dead source gets noticed), how many passed the hard filters, how many were new after dedupe, how many were dropped below the match gate, and the top 3 matches by score (title, company, score, one-line reasoning).

Finish with skill gaps worth attention: recurring missing skills across several jobs matter more than one-offs. If skipped_log.json shows a filter rejecting an unusual number of candidates, flag that too: it usually means the filter needs tuning, not that the market is empty.
