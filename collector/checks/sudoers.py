"""
ISM-1508 — Privileged access limited to what's required (data collection only)

Pulls real sudo group membership from sentinel-server. Returns raw data
only — comparison against policy/baseline.yml's allow-list happens in
policy/engine.py.

Only checks group membership, per the build plan's scope for this control.
"""

from collector.ssh_utils import run_remote_command


def collect(host, user, ssh_key):
    result = run_remote_command(host, user, ssh_key, "getent group sudo")
    if result.returncode != 0:
        raise RuntimeError(f"Failed to read sudo group: {result.stderr.strip()}")
    fields = result.stdout.strip().split(":")
    members = []
    if len(fields) >= 4 and fields[3]:
        members = [name.strip() for name in fields[3].split(",")]
    return {"sudo_group_members": members}
