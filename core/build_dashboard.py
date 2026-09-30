"""Build the dashboard HTML.

Runs the exporter, then injects dashboard_data.json + descriptions.json into
core/dashboard_template.html (placeholder /*__DATA__*/null) and writes
<data>/dashboard.html -- the file that gets published as the dashboard
artifact. Every routine runs this before republishing so the artifact always
carries fresh embedded data.

Incident note: the published dashboard once rendered blank because the
template had been silently truncated mid-<script> by an unverified write, and
this script happily embedded data into the broken template and reported
success. It now refuses to build from a structurally broken template, and
verifies the file it just wrote actually round-trips before declaring
success -- treat any non-zero exit / "BUILD FAILED" output as blocking: do
NOT report the dashboard as rebuilt/republished if this script did not
print "OK".

Usage: python core/build_dashboard.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_io import safe_write_text  # noqa: E402
from settings import BASE, DATA_DIR  # noqa: E402

APPS = DATA_DIR
TEMPLATE = BASE / "core" / "dashboard_template.html"
OUT = APPS / "dashboard.html"
PLACEHOLDER = "/*__DATA__*/null"


def _check_script_balance(html: str, label: str) -> None:
    """A truncated write tends to cut the file off mid <script> block.
    Cheap guard: opening/closing script tags must balance and the last
    non-whitespace content must be a real closing tag."""
    opens = len(re.findall(r"<script[ >]", html))
    closes = html.count("</script>")
    if opens == 0:
        raise SystemExit(f"{label}: no <script> block found -- file looks empty/wrong")
    if opens != closes:
        raise SystemExit(
            f"{label}: unbalanced <script> tags ({opens} open vs {closes} close) -- "
            f"file is truncated. Do not publish this as the dashboard."
        )
    tail = html.rstrip()[-20:]
    if "</script>" not in tail:
        raise SystemExit(
            f"{label}: file does not end with a closed </script> tag "
            f"(tail: {tail!r}) -- looks truncated."
        )


def build():
    subprocess.run(
        [sys.executable, str(BASE / "core" / "export_dashboard_data.py")],
        check=True,
    )
    dashboard = json.loads(
        (APPS / "dashboard_data.json").read_text(encoding="utf-8")
    )
    desc_file = APPS / "descriptions.json"
    descriptions = (
        json.loads(desc_file.read_text(encoding="utf-8"))
        if desc_file.exists()
        else {}
    )
    payload = json.dumps(
        {"dashboard": dashboard, "descriptions": descriptions},
        ensure_ascii=False,
    )
    # keep the embedded JSON safe inside a <script> block
    payload = (
        payload.replace("</", "<\\/")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise SystemExit(f"placeholder {PLACEHOLDER!r} not found in template")
    _check_script_balance(template.replace(PLACEHOLDER, "null"), "TEMPLATE")

    rendered = template.replace(PLACEHOLDER, payload)
    _check_script_balance(rendered, "RENDERED (pre-write)")

    safe_write_text(OUT, rendered)  # writes + verifies checksum, retries on mismatch

    # re-read what actually landed on disk and re-verify -- catches the
    # failure mode where a write "succeeded" per the OS but the content that
    # later reads back was stale/short
    on_disk = OUT.read_text(encoding="utf-8")
    if on_disk != rendered:
        raise SystemExit(
            "BUILD FAILED: dashboard.html on disk does not match what was "
            "just written (mount desync). Do not report this as published."
        )
    _check_script_balance(on_disk, "ON-DISK")
    m = re.search(r"const EMBED = (\{.*?\});\n", on_disk, re.DOTALL)
    if not m:
        raise SystemExit("BUILD FAILED: could not find/parse embedded EMBED data block on disk.")
    embedded = json.loads(m.group(1).replace("<\\/", "</"))
    n_jobs = len(embedded.get("dashboard", {}).get("jobs", []))
    if n_jobs != len(dashboard.get("jobs", [])):
        raise SystemExit(
            f"BUILD FAILED: embedded job count ({n_jobs}) != source job count "
            f"({len(dashboard.get('jobs', []))}) -- data got mangled on write."
        )
    rel = str(OUT.relative_to(BASE)).replace("\\", "/") if OUT.is_relative_to(BASE) else str(OUT)
    print(f"OK {rel} ({OUT.stat().st_size} bytes, {n_jobs} jobs verified on disk)")


if __name__ == "__main__":
    build()
