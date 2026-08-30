"""
ISM-0988 — An accurate and consistent time source is used (data collection only)

Reads real timedatectl output from sentinel-server. Returns raw data only —
the pass/fail judgment happens in policy/engine.py.
"""

from collector.ssh_utils import run_remote_command


def parse_timedatectl(raw):
    values = {}
    for line in raw.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip()
    return values


def collect(host, user, ssh_key):
    result = run_remote_command(host, user, ssh_key, "timedatectl")
    if result.returncode != 0:
        raise RuntimeError(f"timedatectl failed: {result.stderr.strip()}")
    return parse_timedatectl(result.stdout)
