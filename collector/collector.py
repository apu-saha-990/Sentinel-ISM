"""
Sentinel — main entry point ("sentinel scan")

Runs all six ISM control checks against sentinel-server and prints one
structured report: control ID, pass/fail, and plain-English findings for
each. This satisfies the build plan's v1.0 "complete when" bar: a single
command producing one real, accurate report against all six controls.

Run from the repo root as: python3 -m collector.collector
(Must use -m, not a direct path — see runbook for why.)
"""

from policy.engine import run_all_checks


def print_report(results):
    print("=" * 60)
    print("Sentinel — ISM Compliance Scan")
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


if __name__ == "__main__":
    results = run_all_checks()
    print_report(results)
