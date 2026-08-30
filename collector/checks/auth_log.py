"""
ISM-0584 — Logon, failed logon, and logoff events are logged

Originally specified in the build plan as checking for /var/log/auth.log
(exists, is written to, is not empty). Real inspection of sentinel-server
showed this VM has no rsyslog installed and no /var/log/auth.log at all —
a minimized install choice, not a bug. Login/logoff/sudo activity is still
genuinely recorded, but only via systemd-journald.

This check reflects that reality: it queries journalctl directly for
pam_unix entries (a broad net covering SSH logins, sudo sessions, and
console logins — the closest real equivalent to what auth.log used to
capture) rather than checking for a file that does not exist on this
system. Confirms two things: systemd-journald itself is running, and the
journal actually contains recent, real login-related entries — the
journald-native equivalent of "exists, is written to, is not empty."

No simulated or placeholder data — every result reflects the actual
journal contents on sentinel-server at the moment the check runs.
"""

import subprocess
import yaml


def load_env(env_path=".env"):
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def run_remote_command(host, user, ssh_key, command):
    ssh_cmd = [
        "ssh",
        "-i", ssh_key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        f"{user}@{host}",
        command,
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
    return result  # caller checks returncode — journalctl with no matches still exits 0


def check_journald_running(host, user, ssh_key):
    """Confirm systemd-journald itself is active."""
    result = run_remote_command(
        host, user, ssh_key,
        "systemctl is-active systemd-journald"
    )
    return result.stdout.strip() == "active"


def get_recent_login_events(host, user, ssh_key, lines=5):
    """
    Query the journal for recent pam_unix entries — covers SSH logins,
    sudo sessions, and console logins in one broad, auth.log-equivalent net.
    """
    result = run_remote_command(
        host, user, ssh_key,
        f"journalctl --no-pager -q -g pam_unix -n {lines}"
    )
    if result.returncode != 0:
        raise RuntimeError(f"journalctl query failed: {result.stderr.strip()}")
    return [line for line in result.stdout.strip().splitlines() if line]


def run_check():
    env = load_env()
    host = env["SENTINEL_SERVER_HOST"]
    user = env["SENTINEL_SERVER_USER"]
    ssh_key = env["SENTINEL_SERVER_SSH_KEY"]

    findings = []

    if not check_journald_running(host, user, ssh_key):
        findings.append("systemd-journald is not active — login events cannot be logged at all")

    recent_events = []
    if not findings:
        recent_events = get_recent_login_events(host, user, ssh_key)
        if not recent_events:
            findings.append(
                "No pam_unix (login/logoff) entries found in the journal — "
                "logging mechanism may be non-functional or events aren't reaching it"
            )

    return {
        "control": "ISM-0584",
        "description": "Logon, failed logon, and logoff events are logged",
        "pass": len(findings) == 0,
        "findings": findings,
        "sample_recent_events": recent_events[:3],
    }


if __name__ == "__main__":
    result = run_check()
    print(f"{result['control']} — {result['description']}")
    print("PASS" if result["pass"] else "FAIL")
    for f in result["findings"]:
        print(f"  - {f}")
    if result["sample_recent_events"]:
        print("  Sample recent events:")
        for line in result["sample_recent_events"]:
            print(f"    {line}")
