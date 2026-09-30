---
name: scan-mail-status
description: OPTIONAL. Scan the mailbox for company replies, classify each application as invited / waiting / rejected, update mail_status.json, rebuild and republish the dashboard
---

Optional routine. The pipeline works without it; the dashboard's Inbox tab simply stays empty. Run it manually, or give it any schedule you like.

You maintain the application mail status for this job pipeline. Work inside the repository root (call it BASE). Do exactly this:

1. Read the job list from `BASE/data/jobs.db` (**read-only: never write to this DB**): `SELECT id, company, title, status FROM jobs`. Also read the current `BASE/data/mail_status.json` if it exists (schema below).

2. Using the Gmail connector, search **by company name only** (for example `newer_than:45d {"Company A" "Company B" ...}`, batched into a few queries). Do NOT run generic keyword searches, and ignore job-alert newsletters from job boards. Automatic "application received" receipts count as submission confirmations. Cover every company that already has an entry in mail_status.json plus every job whose status is not `skip`/`archived`.

3. Classify per job id:
   - `invited`: an invitation to an interview or intro call from the company;
   - `rejected`: a rejection;
   - otherwise `waiting` (confirmations only).

   Update mail_status.json in place, keeping this schema:
   ```json
   {
     "scanned_at": "<UTC ISO>",
     "mailbox": "<address that was scanned>",
     "convention": "jobs.<id> = {state, company, applied_at, mails[], invitation}",
     "jobs": {
       "<job id>": {
         "state": "invited | waiting | rejected",
         "company": "...",
         "applied_at": "<date of the first confirmation>",
         "mails": [{"date", "from", "subject", "snippet", "thread_id"}],
         "invitation": null
       }
     }
   }
   ```
   For invitations, fetch the full mail body and store it in `invitation.body`; for waiting/rejected keep only subject + snippet. Set `scanned_at` to now (UTC ISO). Write the file with `core/safe_io.py`'s `safe_write_text()`, not a bare file write: it checksums the write and retries on mismatch.

4. Run `python core/build_dashboard.py` (with `PYTHONIOENCODING=utf-8`). The script verifies its own output and exits non-zero with `BUILD FAILED` if anything looks truncated. Treat that as blocking: do NOT go to step 5, and do NOT report the dashboard as refreshed, unless it printed a line starting with `OK`. If it fails, report the exact error.

5. Republish the built dashboard to the artifact in `BASE/config/dashboard_artifact.json` (`html` = file to publish, `url` = target). Never create a second artifact. After publishing, spot-check the published file for a closed `</script>` tag near the end.

6. Report a short summary: how many jobs were scanned, any NEW invitations (name them prominently), new rejections, still waiting. If an invitation was found, suggest running interview prep. If step 4's build check failed, lead the report with that.

Hard rules: never DELETE or UPDATE rows in jobs.db from this routine; mail_status.json is the only file you write besides the rebuilt dashboard outputs; no paid APIs.
