"""
ISM-0383 — Unneeded accounts/services disabled

Connects to sentinel-server over SSH (key-based auth), pulls the real list of
user accounts (/etc/passwd) and the real list of currently RUNNING systemd
services (systemctl --state=running), and compares both against the
allow-lists in policy/baseline.yml.

Filters on 'running' rather than 'active' deliberately: 'active' also
includes one-shot boot units that ran once and exited (e.g. apparmor.service,
kdump-tools.service), which are not what ISM-0383 is asking about. The
baseline allow-list was built from continuously-running services, so the
check has to look at the same thing or every scan would falsely flag normal
boot units as unexpected.

No simulated or placeholder data — every result reflects the actual state of
sentinel-server at the moment the check runs.
"""

import subprocess
import yaml

NON_LOGIN_SHELLS = {"/usr/sbin/nologin", "/bin/false", "/bin/sync", "/sbin/nologin"}


def load_env(env_path=".env"):
    """Minimal .env loader — no extra dependency needed for this."""
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def load_baseline(baseline_path="policy/baseline.yml"):
    with open(baseline_path) as f:
        return yaml.safe_load(f)


def run_remote_command(host, user, ssh_key, command):
    """Run a command on sentinel-server over SSH using key-based auth."""
    ssh_cmd = [
        "ssh",
        "-i", ssh_key,
        "-o", "BatchMode=yes",  # fail instead of falling back to a password prompt
        "-o", "StrictHostKeyChecking=accept-new",
        f"{user}@{host}",
        command,
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        raise RuntimeError(
            f"SSH command failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def get_accounts(host, user, ssh_key):
    """Return list of (username, shell) tuples from /etc/passwd."""
    raw = run_remote_command(host, user, ssh_key, "cat /etc/passwd")
    accounts = []
    for line in raw.strip().splitlines():
        fields = line.split(":")
        if len(fields) < 7:
            continue
        accounts.append((fields[0], fields[6]))
    return accounts


def get_running_services(host, user, ssh_key):
    """Return list of service unit names currently in the 'running' SUB state."""
    raw = run_remote_command(
        host, user, ssh_key,
        "systemctl list-units --type=service --state=running --no-legend --plain"
    )
    services = []
    for line in raw.strip().splitlines():
        if line.strip():
            services.append(line.split()[0])
    return services


def check_accounts(accounts, allowed_login_shells):
    """
    Flag any account with a real login shell that isn't on the allow-list.
    Accounts with a non-login shell are never flagged by name — they're
    system/service accounts, checked structurally (not-login), not by name,
    since a minimized install adds/removes these on its own.
    """
    findings = []
    for username, shell in accounts:
        if shell in NON_LOGIN_SHELLS:
            continue
        if username not in allowed_login_shells:
            findings.append(
                f"Account '{username}' has login shell '{shell}' but is not on the allow-list"
            )
    return findings


def check_services(running_services, allowed_active):
    """Flag any currently running service not explicitly allowed."""
    findings = []
    for service in running_services:
        if service not in allowed_active:
            findings.append(f"Service '{service}' is running but not on the allow-list")
    return findings


def run_check():
    env = load_env()
    baseline = load_baseline()

    host = env["SENTINEL_SERVER_HOST"]
    user = env["SENTINEL_SERVER_USER"]
    ssh_key = env["SENTINEL_SERVER_SSH_KEY"]

    accounts = get_accounts(host, user, ssh_key)
    running_services = get_running_services(host, user, ssh_key)

    findings = (
        check_accounts(accounts, baseline["accounts"]["allowed_login_shells"])
        + check_services(running_services, baseline["services"]["allowed_active"])
    )

    return {
        "control": "ISM-0383",
        "description": "Unneeded accounts/services disabled",
        "pass": len(findings) == 0,
        "findings": findings,
    }


if __name__ == "__main__":
    result = run_check()
    print(f"{result['control']} — {result['description']}")
    print("PASS" if result["pass"] else "FAIL")
    for f in result["findings"]:
        print(f"  - {f}")
