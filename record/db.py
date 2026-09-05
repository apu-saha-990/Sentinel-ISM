"""
Sentinel — Central Record of Results (record/db.py)

Builds a local SQLite database on ArtX from each scan run, so results are
kept as real history instead of only being printed to the terminal and
lost when it closes. collector.py then copies the finished file to
sentinel-server after each run (see push_record_to_server() in
collector.py) — that's what makes this the "central record ... on
sentinel-server" the build plan asks for, even though the writing happens
on ArtX where the collector already runs.

Schema (three tables, one scan run fans out into many rows):
  scan_runs        one row per host per scan run — timestamp, host_label
  control_results  one row per control checked in that run (control ID,
                    description, pass/fail) — linked to scan_runs.id
  findings         one row per individual finding text — linked to
                    control_results.id (a control can have zero, one, or
                    many findings)

This is a local file (SQLite), not a database server — no port is opened,
no service runs in the background. Matches the build plan's note that
"a local database or even a structured file is enough — no need for a
networked service" for this piece.

Called from collector.py after each host's run_all_checks() results come
back. Does not run standalone.
"""

import sqlite3
from datetime import datetime, timezone

DB_PATH = "record/sentinel_results.db"


def get_connection(db_path=DB_PATH):
    """Open the local SQLite file (creating it if it doesn't exist yet)
    and make sure the schema is there. Safe to call on every run —
    CREATE TABLE IF NOT EXISTS only does anything the first time."""
    conn = sqlite3.connect(db_path)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            host_label TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS control_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL REFERENCES scan_runs(id),
            control TEXT NOT NULL,
            description TEXT NOT NULL,
            passed INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            control_result_id INTEGER NOT NULL REFERENCES control_results(id),
            finding_text TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


def record_scan(conn, host_label, results):
    """Write one host's scan results (the list run_all_checks() returns)
    into the database as one new scan run. Returns the new run's id."""
    timestamp = datetime.now(timezone.utc).isoformat()

    cursor = conn.execute(
        "INSERT INTO scan_runs (timestamp, host_label) VALUES (?, ?)",
        (timestamp, host_label),
    )
    run_id = cursor.lastrowid

    for result in results:
        cursor = conn.execute(
            "INSERT INTO control_results (run_id, control, description, passed) "
            "VALUES (?, ?, ?, ?)",
            (run_id, result["control"], result["description"], int(result["pass"])),
        )
        control_result_id = cursor.lastrowid

        for finding_text in result.get("findings", []):
            conn.execute(
                "INSERT INTO findings (control_result_id, finding_text) VALUES (?, ?)",
                (control_result_id, finding_text),
            )

    conn.commit()
    return run_id
