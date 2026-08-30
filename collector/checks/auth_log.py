"""
ISM-0584 — Logon, failed logon, and logoff events are logged (data collection only)

This system has no rsyslog and no /var/log/auth.log — login/logoff/sudo
activity is recorded only via systemd-journald. Collects whether journald
is active, and a sample of recent pam_unix journal entries (covers SSH
logins, sudo sessions, and console logins in one broad net).

Returns raw data only — the pass/fail judgment happens in policy/engine.py.
"""

from collector.ssh_utils import run_remote_command


def is_journald_active(host, user, ssh_key):
    result = run_remote_command(host, user, ssh_key, "systemctl is-active systemd-journald")
    return result.stdout.strip()


def get_recent_login_events(host, user, ssh_key, lines=5):
    result = run_remote_command(
        host, user, ssh_key,
        f"journalctl --no-pager -q -g pam_unix -n {lines}"
    )
    if result.returncode != 0:
        raise RuntimeError(f"journalctl query failed: {result.stderr.strip()}")
    return [line for line in result.stdout.strip().splitlines() if line]


def collect(host, user, ssh_key):
    return {
        "journald_status": is_journald_active(host, user, ssh_key),
        "recent_pam_events": get_recent_login_events(host, user, ssh_key),
    }
