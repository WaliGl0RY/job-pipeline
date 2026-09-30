"""Export dashboard_data.json for the dashboard.

Reads jobs.db (never writes it), scans <data>/packages/ and tailor_queue.json,
and writes <data>/dashboard_data.json. The dashboard embeds this file; every
routine re-runs this exporter (through build_dashboard.py) at the end of a run.

Descriptions stay in descriptions.json and are referenced by job id only
(described_job_ids) -- they never go into the jobs table.

Usage: python core/export_dashboard_data.py
"""
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_io import clear_stale_sqlite_journal, safe_write_text  # noqa: E402
from settings import BASE, DATA_DIR, DB_PATH  # noqa: E402

APPS = DATA_DIR
DB = DB_PATH
OUT = APPS / "dashboard_data.json"


def parse_json_field(value, default):
    if not value:
        return default
    try:
        parsed = json.loads(value)
        return parsed if parsed is not None else default
    except (json.JSONDecodeError, TypeError):
        return default


MIN_MATCH_SCORE = 50  # jobs scoring below this never reach the dashboard


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(BASE)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def export():
    if not DB.exists():
        raise SystemExit(f"no database at {DB} -- run `python demo/generate_demo_data.py` or `python core/job_database.py` first")
    clear_stale_sqlite_journal(DB)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    jobs = []
    dropped_low_match = 0
    for r in con.execute(
        """SELECT id, title, company, url, location, job_board, posted_date,
                  days_posted, freshness_score, match_score, is_reposted,
                  required_skills, matching_skills, missing_skills,
                  priority_tier, discovered_at, status, notes
           FROM jobs ORDER BY id"""
    ):
        d = dict(r)
        # Below-threshold jobs stay in jobs.db (audit trail, never delete rows)
        # but are excluded from the exported/embedded data so they never reach
        # the dashboard. Exception: if the job has progressed past plain
        # "discovered" (applied/skip/archived/etc.), keep it visible -- a human
        # decision was already made on it.
        if (d["match_score"] is None or d["match_score"] < MIN_MATCH_SCORE) and d["status"] == "discovered":
            dropped_low_match += 1
            continue
        d["required_skills"] = parse_json_field(d["required_skills"], [])
        d["matching_skills"] = parse_json_field(d["matching_skills"], [])
        d["missing_skills"] = parse_json_field(d["missing_skills"], [])
        jobs.append(d)

    applications = [
        dict(r)
        for r in con.execute(
            """SELECT id, job_id, cv_variant, cover_letter_generated,
                      submitted_at, submission_url, confirmation_id, status,
                      error_message
               FROM applications ORDER BY id"""
        )
    ]

    responses = [
        dict(r)
        for r in con.execute(
            """SELECT id, application_id, response_type, response_date,
                      response_subject, response_body, action_required, notes,
                      received_at
               FROM responses ORDER BY id"""
        )
    ]
    con.close()

    descriptions_file = APPS / "descriptions.json"
    described_ids = []
    if descriptions_file.exists():
        descs = json.loads(descriptions_file.read_text(encoding="utf-8"))
        described_ids = sorted(int(k) for k in descs.keys())

    packages = {}
    pkg_root = APPS / "packages"
    if pkg_root.is_dir():
        for pkg_dir in sorted(pkg_root.iterdir()):
            meta_file = pkg_dir / "meta.json"
            if not pkg_dir.is_dir() or not meta_file.exists():
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            job_id = meta.get("job_id")
            if job_id is None:
                continue
            packages[str(job_id)] = {
                "dir": _rel(pkg_dir),
                "generated_at": meta.get("generated_at"),
                "files": meta.get("files", []),
                "pdf_compiled": meta.get("pdf_compiled"),
                "notes": meta.get("notes"),
            }

    queue_file = APPS / "tailor_queue.json"
    queue = []
    if queue_file.exists():
        try:
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            queue = []

    # mail_status.json is written by the optional scan-mail-status routine
    # (company-name mailbox search); keyed by job id. Absent file => empty dict.
    mail_file = APPS / "mail_status.json"
    mail_status = {}
    if mail_file.exists():
        try:
            mail_status = json.loads(mail_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            mail_status = {}

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jobs": jobs,
        "described_job_ids": described_ids,
        "applications": applications,
        "responses": responses,
        "packages": packages,
        "tailor_queue": queue,
        "mail_status": mail_status,
    }
    safe_write_text(OUT, json.dumps(data, ensure_ascii=False, indent=1))
    print(
        f"OK {_rel(OUT)} -- {len(jobs)} jobs, {len(applications)} applications, "
        f"{len(responses)} responses, {len(packages)} packages, "
        f"{len(queue)} queued, {dropped_low_match} dropped (<{MIN_MATCH_SCORE}% match)"
    )


if __name__ == "__main__":
    sys.exit(export())
