"""
Sentinel — main entry point ("sentinel scan")

Runs all six ISM control checks against every host in HOSTS below and prints
one structured report per host: control ID, pass/fail, and plain-English
findings for each.

As of v1.1, this scans both sentinel-server and sentinel-endpoint in one
run — this is the "same scanner works across two machines" requirement from
the build plan. Each host gets its own report; there is no combined/central
record yet (that's policy/record/db.py, a separate not-yet-built piece).

Run from the repo root as: python3 -m collector.collector
(Must use -m, not a direct path — see runbook for why.)
"""

from collector.ssh_utils import load_env
from policy.engine import run_all_checks


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


if __name__ == "__main__":
    env = load_env()
    hosts = get_hosts(env)

    for entry in hosts:
        results = run_all_checks(entry["host"], entry["user"], entry["ssh_key"], entry["label"])
        print_report(entry["label"], results)
