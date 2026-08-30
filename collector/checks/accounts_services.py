"""
ISM-0383 — Unneeded accounts/services disabled (data collection only)

Pulls the real account list (/etc/passwd) and real currently-RUNNING
systemd services from sentinel-server. Returns raw collected data only —
comparison against policy/baseline.yml's allow-lists happens in
policy/engine.py, not here.

Filters services on 'running' rather than 'active' deliberately: 'active'
also includes one-shot boot units that ran once and exited, which are not
what ISM-0383 is asking about.

No simulated or placeholder data — every value reflects the actual state
of sentinel-server at the moment collect() runs.
"""

from collector.ssh_utils import run_remote_command


def get_accounts(host, user, ssh_key):
    result = run_remote_command(host, user, ssh_key, "cat /etc/passwd")
    if result.returncode != 0:
        raise RuntimeError(f"Failed to read /etc/passwd: {result.stderr.strip()}")
    accounts = []
    for line in result.stdout.strip().splitlines():
        fields = line.split(":")
        if len(fields) < 7:
            continue
        accounts.append((fields[0], fields[6]))
    return accounts


def get_running_services(host, user, ssh_key):
    result = run_remote_command(
        host, user, ssh_key,
        "systemctl list-units --type=service --state=running --no-legend --plain"
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to list services: {result.stderr.strip()}")
    return [line.split()[0] for line in result.stdout.strip().splitlines() if line.strip()]


def collect(host, user, ssh_key):
    """Return raw collected state — no baseline comparison happens here."""
    return {
        "accounts": get_accounts(host, user, ssh_key),
        "running_services": get_running_services(host, user, ssh_key),
    }
