#!/usr/bin/env python3
"""
Job Database Interface
Manages the SQLite database for job tracking, applications, and responses.

Incident note: a scheduled run once hit `disk I/O error` on this file because
a stale -journal was left behind by a prior interrupted write on a flaky
synced folder. connect() now clears that class of stale journal defensively
before opening, and commit() retries once through the same cleanup if it
still hits a disk I/O error. Call .verify() after a batch of writes before
reporting success.

Rule: rows are never deleted. Jobs only change status
(discovered -> approved_for_application -> applied / skip / archived).
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_io import clear_stale_sqlite_journal, verify_sqlite_ok
from settings import DB_PATH

class JobDatabase:
    """SQLite database interface for job automation."""

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Connect to database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        clear_stale_sqlite_journal(Path(self.db_path))
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.conn.cursor()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def commit(self):
        """Commit with one retry: clear a stale journal and reconnect if the
        first attempt hits a disk I/O error (seen on a flaky synced folder)."""
        try:
            self.conn.commit()
        except sqlite3.OperationalError as e:
            if "disk I/O error" not in str(e):
                raise
            self.close()
            self.connect()
            self.conn.commit()

    def verify(self) -> bool:
        """Read-only integrity check (bypasses any journal). Call this after
        a batch of inserts before reporting success to the user."""
        self.conn.commit()
        return verify_sqlite_ok(Path(self.db_path))

    def create_schema(self):
        """Create database schema (tables)."""
        self.cursor.executescript("""
        -- Jobs table
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            location TEXT,
            job_board TEXT,
            job_description TEXT,
            posted_date TEXT,
            days_posted INTEGER,
            freshness_score REAL,
            match_score REAL,
            is_reposted BOOLEAN,
            required_skills TEXT,
            matching_skills TEXT,
            missing_skills TEXT,
            priority_tier TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'discovered',
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_freshness ON jobs(freshness_score DESC);

        -- Applications table
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            cv_variant TEXT,
            cover_letter_generated BOOLEAN,
            form_fields TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            submission_url TEXT,
            confirmation_screenshot TEXT,
            confirmation_id TEXT,
            status TEXT DEFAULT 'submitted',
            error_message TEXT,
            agent_browser_log TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        );

        CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
        CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
        CREATE INDEX IF NOT EXISTS idx_applications_submitted_at ON applications(submitted_at DESC);

        -- Responses table
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            response_type TEXT,
            response_date TIMESTAMP,
            response_subject TEXT,
            response_body TEXT,
            action_required TEXT,
            notes TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(application_id) REFERENCES applications(id)
        );

        CREATE INDEX IF NOT EXISTS idx_responses_application_id ON responses(application_id);
        CREATE INDEX IF NOT EXISTS idx_responses_response_type ON responses(response_type);
        """)
        self.commit()
        print("Database schema created")

    def add_job(
        self,
        title: str,
        company: str,
        url: str,
        location: Optional[str] = None,
        job_board: Optional[str] = None,
        job_description: Optional[str] = None,
        posted_date: Optional[str] = None,
        days_posted: Optional[int] = None,
        freshness_score: Optional[float] = None,
        match_score: Optional[float] = None,
        is_reposted: bool = False,
        required_skills: Optional[List[str]] = None,
        matching_skills: Optional[List[str]] = None,
        missing_skills: Optional[List[str]] = None,
        priority_tier: str = "tier3",
        status: str = "discovered",
        notes: Optional[str] = None,
    ) -> int:
        """Add a job to database. Returns job_id."""
        self.cursor.execute("""
        INSERT INTO jobs (
            title, company, url, location, job_board, job_description,
            posted_date, days_posted, freshness_score, match_score,
            is_reposted, required_skills, matching_skills, missing_skills,
            priority_tier, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, company, url, location, job_board, job_description,
            posted_date, days_posted, freshness_score, match_score,
            is_reposted,
            json.dumps(required_skills or []),
            json.dumps(matching_skills or []),
            json.dumps(missing_skills or []),
            priority_tier, status, notes
        ))
        row_id = self.cursor.lastrowid  # read before commit(): its retry path reconnects
        self.commit()
        return row_id

    def get_jobs_by_status(self, status: str) -> List[Dict]:
        """Get all jobs with given status."""
        self.cursor.execute("""
        SELECT * FROM jobs WHERE status = ? ORDER BY match_score DESC, freshness_score DESC
        """, (status,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_top_matches(self, match_min: float = 70, freshness_min: float = 70) -> List[Dict]:
        """Get top matching jobs (for review)."""
        self.cursor.execute("""
        SELECT * FROM jobs
        WHERE match_score >= ? AND freshness_score >= ?
        ORDER BY match_score DESC, freshness_score DESC
        """, (match_min, freshness_min))
        return [dict(row) for row in self.cursor.fetchall()]

    def update_job_status(self, job_id: int, status: str, notes: Optional[str] = None):
        """Update job status."""
        if notes:
            self.cursor.execute("""
            UPDATE jobs SET status = ?, notes = ? WHERE id = ?
            """, (status, notes, job_id))
        else:
            self.cursor.execute("""
            UPDATE jobs SET status = ? WHERE id = ?
            """, (status, job_id))
        self.commit()

    def add_application(
        self,
        job_id: int,
        cv_variant: Optional[str] = None,
        form_fields: Optional[Dict] = None,
        status: str = "submitted",
        confirmation_id: Optional[str] = None,
        confirmation_screenshot: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> int:
        """Add application record. Returns application_id."""
        self.cursor.execute("""
        INSERT INTO applications (
            job_id, cv_variant, form_fields, status,
            confirmation_id, confirmation_screenshot, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            cv_variant,
            json.dumps(form_fields or {}),
            status,
            confirmation_id,
            confirmation_screenshot,
            error_message,
        ))
        row_id = self.cursor.lastrowid  # read before commit(): its retry path reconnects
        self.commit()
        return row_id

    def add_response(
        self,
        application_id: int,
        response_type: str,
        response_date: Optional[str] = None,
        response_subject: Optional[str] = None,
        response_body: Optional[str] = None,
        action_required: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Add response record. Returns response_id."""
        self.cursor.execute("""
        INSERT INTO responses (
            application_id, response_type, response_date,
            response_subject, response_body, action_required, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            application_id,
            response_type,
            response_date or datetime.now().isoformat(),
            response_subject,
            response_body,
            action_required,
            notes,
        ))
        row_id = self.cursor.lastrowid  # read before commit(): its retry path reconnects
        self.commit()
        return row_id

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Get job by ID."""
        self.cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def count_by_status(self, status: str) -> int:
        """Count jobs by status."""
        self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = ?", (status,))
        return self.cursor.fetchone()[0]

    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs."""
        self.cursor.execute("SELECT * FROM jobs ORDER BY discovered_at DESC")
        return [dict(row) for row in self.cursor.fetchall()]

if __name__ == "__main__":
    # Test database
    db = JobDatabase()
    db.create_schema()
    print("Database initialized and schema created:", db.verify())
    db.close()
