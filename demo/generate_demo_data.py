"""Generate a complete demo data layer so the dashboard can be built without
any real jobs, mails or CVs.

Writes into the data folder (default: data/, or JOB_PIPELINE_DATA_DIR):
  jobs.db, descriptions.json, mail_status.json, tailor_queue.json,
  status_changes.json, skipped_log.json, cv_profile/*, packages/*/meta.json

All companies are well-known fictional sample names, all people and
addresses are made up, and every URL/mail domain is under example.com.
Dates are relative to "now", so the demo always looks fresh.

Usage:
  python demo/generate_demo_data.py           # refuses if data/jobs.db exists
  python demo/generate_demo_data.py --force   # replaces jobs.db and the demo files
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))
from job_database import JobDatabase  # noqa: E402
from safe_io import safe_write_text  # noqa: E402
from settings import BASE, DATA_DIR, DB_PATH  # noqa: E402

NOW = datetime.now(timezone.utc).replace(microsecond=0)

# Search runs, as offsets from now. The dashboard groups jobs into runs by discovered_at.
RUN_OLD, RUN_MID, RUN_NEW = timedelta(days=20), timedelta(days=9), timedelta(days=1)

# (title, company, location, source, days_posted, match, matching, missing, status, run)
JOBS = [
    ("Working Student Data Analytics (m/f/d)", "Contoso GmbH", "Cologne", "Apify", 3, 88,
     ["Python", "SQL", "Data visualisation", "English C1"], ["Power BI"], "applied", RUN_MID),
    ("Working Student Backend Development (Python)", "Fabrikam AG", "Cologne", "Indeed", 2, 84,
     ["Python", "REST APIs", "SQL", "Git"], ["Kubernetes"], "approved_for_application", RUN_NEW),
    ("Working Student IT Support", "Northwind Traders", "Bonn", "Indeed", 5, 72,
     ["Windows clients", "Networking basics", "Customer communication"], ["ITIL"], "discovered", RUN_MID),
    ("Working Student DevOps & Cloud", "Relecloud", "Düsseldorf", "Apify", 4, 79,
     ["Linux", "Docker", "Git", "Python"], ["Terraform", "Azure"], "discovered", RUN_NEW),
    ("Working Student AI Automation in After Sales", "Tailspin Toys", "Leverkusen", "Apify", 1, 91,
     ["Python", "Prompt engineering", "Automation", "Data analysis"], [], "approved_for_application", RUN_NEW),
    ("Working Student Software Testing", "Litware Inc.", "Cologne", "Indeed", 6, 66,
     ["Java", "JUnit", "Agile"], ["Selenium", "ISTQB"], "discovered", RUN_MID),
    ("Working Student Network Administration", "Woodgrove Bank", "Cologne", "Apify", 7, 70,
     ["Networking", "Linux", "Troubleshooting"], ["Cisco IOS", "Firewalls"], "applied", RUN_OLD),
    ("Working Student Business Intelligence", "Adventure Works", "Hürth", "Indeed", 3, 81,
     ["SQL", "Data modelling", "Python"], ["SAP BW"], "applied", RUN_MID),
    ("Working Student Web Development (JavaScript)", "Proseware", "Cologne", "Apify", 2, 63,
     ["JavaScript", "HTML/CSS", "Git"], ["React", "TypeScript"], "discovered", RUN_NEW),
    ("Working Student Data Engineering", "Trey Research", "Bonn", "Apify", 8, 76,
     ["Python", "SQL", "Docker"], ["Airflow", "Spark"], "applied", RUN_OLD),
    ("Working Student IT Security", "Humongous Insurance", "Cologne", "Indeed", 4, 58,
     ["Networking", "Linux"], ["SIEM", "ISO 27001"], "discovered", RUN_MID),
    ("Working Student Process Automation", "Wide World Importers", "Frechen", "Apify", 5, 69,
     ["Python", "Automation", "Excel"], ["UiPath"], "discovered", RUN_NEW),
    ("Working Student Java Development", "Lucerne Publishing", "Cologne", "Indeed", 9, 74,
     ["Java", "Spring Boot", "SQL", "Scrum"], ["Microservices"], "applied", RUN_OLD),
    ("Working Student Digital Marketing Analytics", "Fourth Coffee", "Cologne", "Apify", 6, 52,
     ["Data analysis", "Excel"], ["Google Analytics", "SEO"], "skip", RUN_OLD),
    ("Working Student Cloud Support", "Alpine Ski House", "Düsseldorf", "Indeed", 3, 61,
     ["Linux", "Customer communication"], ["AWS"], "archived", RUN_OLD),
    # Below the 50 % gate: stays in jobs.db (audit trail) but the exporter hides it.
    ("Working Student Data Quality", "Coho Winery", "Bergisch Gladbach", "Apify", 10, 45,
     ["Excel"], ["SAP", "Data governance"], "discovered", RUN_OLD),
]

# job index (1-based) -> (days since applying, mail state)
APPLIED = {1: (7, "invited"), 7: (10, "waiting"), 8: (6, "waiting"), 10: (16, "rejected"), 13: (17, "waiting")}

DEMO_PROFILE = {
    "generated_from": "templates/master_cv.example.tex",
    "generated_at": NOW.isoformat(),
    "personal": {
        "name": "Alex Example",
        "location": "Example City",
        "phone": "+00 000 0000000",
        "email": "alex.example@example.com",
        "profile_url": "https://alex-example.example.com",
        "languages": {"English": "C1", "German": "C1"},
        "profile_summary": "Computer science student (3rd semester) with Java and Python team-project experience; likes dashboards and automation.",
    },
    "education": [{"degree": "B.Sc. Computer Science", "school": "University of Example Sciences", "from": "10/2025", "to": "09/2028"}],
    "certifications": [{"name": "Example Cloud Fundamentals", "date": "03/2026", "status": "completed"}],
    "skills": {
        "programming": ["Java", "Python", "SQL", "JavaScript"],
        "tools": ["Git", "Docker", "Linux", "REST APIs"],
        "methods": ["Scrum", "Unit testing"],
    },
    "projects": [
        {"name": "Library Booking Service", "stack": ["Java", "Spring Boot", "PostgreSQL"], "type": "team"},
        {"name": "Weather Dashboard", "stack": ["Python", "FastAPI", "SQLite"], "type": "personal"},
    ],
    "work_experience": [{"role": "IT Support (part-time)", "company": "Example Services Ltd.", "from": "01/2025", "to": "12/2025"}],
    "interests": ["bouldering", "home automation"],
}


def slug(s: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in s)
    return "-".join(p for p in out.split("-") if p)


def domain(company: str) -> str:
    return slug(company.split()[0]) + ".example.com"


def description(title, company, location, matching, missing) -> str:
    skills = ", ".join(matching + missing)
    return (
        f"{company} is looking for a {title} in {location} (15-20 hours per week, flexible around your studies).\n\n"
        f"Your tasks:\n"
        f"- Support the team in day-to-day work around {title.replace('Working Student ', '').split(' (')[0]}\n"
        f"- Build small tools and scripts that save the team time\n"
        f"- Document results and present them in team meetings\n\n"
        f"Your profile:\n"
        f"- Enrolled student in computer science or a related field\n"
        f"- First experience with {skills}\n"
        f"- Good English; German is a plus\n\n"
        f"This is a fictional demo posting generated by demo/generate_demo_data.py."
    )


def ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="replace an existing jobs.db")
    args = ap.parse_args()

    if DB_PATH.exists():
        if not args.force:
            raise SystemExit(f"{DB_PATH} already exists. Use --force to replace it with demo data.")
        DB_PATH.unlink()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    db = JobDatabase(str(DB_PATH))
    db.create_schema()
    descriptions, mail_jobs = {}, {}

    for i, (title, company, loc, board, days, match, have, miss, status, run) in enumerate(JOBS, start=1):
        discovered = NOW - run + timedelta(minutes=3 * i)
        tier = "tier1" if match >= 80 else "tier2" if match >= 60 else "tier3"
        job_id = db.add_job(
            title=title, company=company, url=f"https://jobs.example.com/postings/{1000 + i}",
            location=loc, job_board=board,
            posted_date=(discovered - timedelta(days=days)).date().isoformat(), days_posted=days,
            freshness_score=max(0.0, round(100 - days * (100 / 30), 1)), match_score=match,
            required_skills=have + miss, matching_skills=have, missing_skills=miss,
            priority_tier=tier, status=status,
            notes=f"Demo: {match} % match. " + (f"Gap: {', '.join(miss)}." if miss else "No critical gaps."),
        )
        db.cursor.execute("UPDATE jobs SET discovered_at = ? WHERE id = ?", (ts(discovered), job_id))
        descriptions[str(job_id)] = {"company": company, "title": title,
                                     "description": description(title, company, loc, have, miss)}

        if i in APPLIED:
            days_ago, state = APPLIED[i]
            applied_at = NOW - timedelta(days=days_ago)
            db.add_application(job_id=job_id, cv_variant=f"CV_{company.split()[0]}.pdf", status="submitted")
            db.cursor.execute("UPDATE applications SET submitted_at = ? WHERE job_id = ?", (ts(applied_at), job_id))
            mails = [{"date": applied_at.isoformat(), "from": f"careers@{domain(company)}",
                      "subject": f"We received your application: {title}",
                      "snippet": "Thank you for your application. We will review your documents and get back to you.",
                      "thread_id": f"demo-{job_id}-1"}]
            invitation = None
            if state == "invited":
                when = NOW - timedelta(days=2)
                mails.append({"date": when.isoformat(), "from": f"hr@{domain(company)}",
                              "subject": "Invitation to a first interview",
                              "snippet": "We would like to get to know you in a 30-minute video call.",
                              "thread_id": f"demo-{job_id}-2"})
                invitation = {"subject": "Invitation to a first interview", "date": when.isoformat(),
                              "body": "Hello Alex,\n\nthank you for your application. We would like to get to know you "
                                      "in a 30-minute video call next week. Please pick a slot that suits you.\n\n"
                                      "Best regards\nThe recruiting team"}
            elif state == "rejected":
                when = NOW - timedelta(days=4)
                mails.append({"date": when.isoformat(), "from": f"careers@{domain(company)}",
                              "subject": f"Your application: {title}",
                              "snippet": "Unfortunately we have decided to continue with other candidates.",
                              "thread_id": f"demo-{job_id}-2"})
            mail_jobs[str(job_id)] = {"state": state, "company": company, "applied_at": applied_at.isoformat(),
                                      "mails": mails, "invitation": invitation}
    db.commit()
    ok = db.verify()
    db.close()
    if not ok:
        raise SystemExit("demo jobs.db failed the integrity check")

    safe_write_text(DATA_DIR / "descriptions.json", json.dumps(descriptions, ensure_ascii=False, indent=1))
    safe_write_text(DATA_DIR / "mail_status.json", json.dumps({
        "scanned_at": (NOW - timedelta(hours=5)).isoformat(),
        "mailbox": "alex.example@example.com",
        "convention": "jobs.<id> = {state, company, applied_at, mails[], invitation}",
        "jobs": mail_jobs,
    }, ensure_ascii=False, indent=1))
    safe_write_text(DATA_DIR / "tailor_queue.json", json.dumps(
        [{"job_id": 4, "requested_at": (NOW - timedelta(hours=2)).isoformat()}], indent=1))
    safe_write_text(DATA_DIR / "status_changes.json", "[]")
    safe_write_text(DATA_DIR / "skipped_log.json", json.dumps([
        {"run": (NOW - RUN_NEW).date().isoformat(), "title": "Working Student Recruiting", "company": "Graphic Design Institute",
         "location": "Cologne", "url": "https://jobs.example.com/postings/2001", "posted_date": None, "reason": "title_exclude"},
        {"run": (NOW - RUN_NEW).date().isoformat(), "title": "Working Student IT", "company": "School of Fine Art",
         "location": "Faraway City", "url": "https://jobs.example.com/postings/2002", "posted_date": None, "reason": "location"},
        {"run": (NOW - RUN_NEW).date().isoformat(), "title": "Working Student Office Assistance", "company": "Margie's Travel",
         "location": "Cologne", "url": "https://jobs.example.com/postings/2003", "posted_date": None, "reason": "score_31"},
    ], ensure_ascii=False, indent=1))

    cv_template = BASE / "templates" / "master_cv.example.tex"
    profile_dir = DATA_DIR / "cv_profile"
    safe_write_text(profile_dir / "cv_skills_snapshot.json", json.dumps(DEMO_PROFILE, ensure_ascii=False, indent=1))
    safe_write_text(profile_dir / "cv_snapshot_meta.json", json.dumps({
        "convention": "master_cv_sha256 gates regeneration of cv_skills_snapshot.json",
        "master_cv_sha256": hashlib.sha256(cv_template.read_bytes()).hexdigest(),
        "snapshot_generated_at": NOW.isoformat(),
        "note": "Demo snapshot, hashed against templates/master_cv.example.tex.",
    }, indent=1))

    # Packages: the exporter only reads meta.json, so the demo ships no CV/letter files.
    for job_id in (2, 5):
        title, company = JOBS[job_id - 1][0], JOBS[job_id - 1][1]
        pkg = DATA_DIR / "packages" / f"{job_id}_{slug(company)}"
        safe_write_text(pkg / "meta.json", json.dumps({
            "job_id": job_id, "company": company, "title": title,
            "generated_at": (NOW - timedelta(hours=20, minutes=job_id)).isoformat(),
            "files": ["cv_tailored.tex", f"CV_{company.split()[0]}.pdf", "cover_letter.docx"],
            "pdf_compiled": False, "cv_pages": None,
            "notes": "Demo package: meta.json only, no documents.",
        }, ensure_ascii=False, indent=1))

    print(f"OK demo data written to {DATA_DIR} ({len(JOBS)} jobs, {len(APPLIED)} applied)")


if __name__ == "__main__":
    main()
