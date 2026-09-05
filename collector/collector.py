"""
Sentinel — main entry point ("sentinel scan")

Runs all six ISM control checks against every host in HOSTS below and prints
one structured report per host: control ID, pass/fail, and plain-English
findings for each.

As of v1.1, this scans both sentinel-server and sentinel-endpoint in one
run — this is the "same scanner works across two machines" requirement from
the build plan. Each host gets its own printed report.

As of this session, each host's results are also written to a local
SQLite database (record/db.py) on ArtX, and the finished database file is
then copied to sentinel-server over SCP — this is the "central record of
results on sentinel-server" piece from the build plan. The record lives on
sentinel-server; it's just built on ArtX first, in the same place the
collector already runs.

Run from the repo root as: python3 -m collector.collector
(Must use -m, not a direct path — see runbook for why.)
"""

from collector.ssh_utils import load_env, run_remote_command, copy_file_to_remote
from policy.engine import run_all_checks
from record.db import get_connection, record_scan, DB_PATH

REMOTE_RECORD_DIR = "sentinel-record"
REMOTE_DB_PATH = f"{REMOTE_RECORD_DIR}/results.db"


def print_report(host_label, results):
    print("=" * 60)
    print(f"Sentinel — ISM Compliance Scan — {host_label}")
    print("=" * 60)

    for result in results:
        status = "PASS" if result["pass"] else "FAIL"
        print(f"\n[{status}] {result['control']} — {result['description']}")
        for finding in result.get("findings", []):
            print(f"  - {finding}")

    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    print("\n" + "-" * 60)
    print(f"Summary: {passed}/{total} controls passed")
    print("-" * 60)
    print()


def get_hosts(env):
    """Build the list of hosts to scan from .env. Add future hosts here."""
    return [
        {
            "label": "sentinel-server",
            "host": env["SENTINEL_SERVER_HOST"],
            "user": env["SENTINEL_SERVER_USER"],
            "ssh_key": env["SENTINEL_SERVER_SSH_KEY"],
        },
        {
            "label": "sentinel-endpoint",
            "host": env["SENTINEL_ENDPOINT_HOST"],
            "user": env["SENTINEL_ENDPOINT_USER"],
            "ssh_key": env["SENTINEL_ENDPOINT_SSH_KEY"],
        },
    ]


def push_record_to_server(server_entry):
    """Copy the local results database to sentinel-server so the scan
    history is held centrally there, not just on ArtX. Creates the
    remote directory first (SCP won't do this itself); mkdir -p is safe
    to run every time, it does nothing if the directory already exists."""
    run_remote_command(
        server_entry["host"], server_entry["user"], server_entry["ssh_key"],
        f"mkdir -p {REMOTE_RECORD_DIR}",
    )
    copy_file_to_remote(
        DB_PATH,
        server_entry["host"], server_entry["user"], server_entry["ssh_key"],
        REMOTE_DB_PATH,
    )


if __name__ == "__main__":
    env = load_env()
    hosts = get_hosts(env)
    conn = get_connection()

    for entry in hosts:
        results = run_all_checks(entry["host"], entry["user"], entry["ssh_key"], entry["label"])
        print_report(entry["label"], results)
        record_scan(conn, entry["label"], results)

    conn.close()

    server_entry = next(h for h in hosts if h["label"] == "sentinel-server")
    push_record_to_server(server_entry)
