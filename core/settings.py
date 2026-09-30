"""Shared paths for the pipeline.

The data layer lives in one folder (default: `data/` next to `core/`).
Override it with the JOB_PIPELINE_DATA_DIR environment variable, either as an
absolute path or relative to the repository root.
"""
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

_data_env = os.environ.get("JOB_PIPELINE_DATA_DIR", "").strip()
DATA_DIR = (BASE / _data_env).resolve() if _data_env else BASE / "data"

DB_PATH = DATA_DIR / "jobs.db"
