"""
Sentinel — Policy Engine

Central comparison logic for all six ISM controls. Each collector/checks/*.py
module only gathers raw state from a target host; every allow-list
comparison and pass/fail judgment happens here, against policy/baseline.yml.

As of v1.1, baseline.yml has per-host sections under `hosts:` (accounts,
services, sudoers) since sentinel-server and sentinel-endpoint have
different expected usernames and service lists. log_permissions stays
shared at the top level since the journal path pattern is the same on both.

run_all_checks() takes host/user/ssh_key/host_label as parameters — the
caller (collector.py) decides which host to point it at and which baseline
section to compare against.
"""

import yaml

from collector.checks import accounts_services, sudoers, auth_log, log_permissions, time_sync

NON_LOGIN_SHELLS = {"/usr/sbin/nologin", "/bin/false", "/bin/sync", "/sbin/nologin"}


def load_baseline(baseline_path="policy/baseline.yml"):
    with open(baseline_path) as f:
        return yaml.safe_load(f)


def evaluate_accounts_services(data, baseline, host_label):
    findings = []
    host_baseline = baseline["hosts"][host_label]

    allowed_login_shells = host_baseline["accounts"]["allowed_login_shells"]
    for username, shell in data["accounts"]:
        if shell in NON_LOGIN_SHELLS:
            continue
        if username not in allowed_login_shells:
            findings.append(
                f"Account '{username}' has login shell '{shell}' but is not on the allow-list"
            )

    allowed_active = host_baseline["services"]["allowed_active"]
    for service in data["running_services"]:
        if service not in allowed_active:
            findings.append(f"Service '{service}' is running but not on the allow-list")

    return {
        "control": "ISM-0383",
        "description": "Unneeded accounts/services disabled",
        "pass": len(findings) == 0,
        "findings": findings,
    }


def evaluate_sudoers(data, baseline, host_label):
    findings = []
    allowed_members = baseline["hosts"][host_label]["sudoers"]["allowed_members"]
    for member in data["sudo_group_members"]:
        if member not in allowed_members:
            findings.append(f"'{member}' is a member of the sudo group but is not on the allow-list")

    return {
        "control": "ISM-1508",
        "description": "Privileged access limited to what's required",
        "pass": len(findings) == 0,
        "findings": findings,
    }


def evaluate_auth_log(data):
    findings = []

    if data["journald_status"] != "active":
        findings.append("systemd-journald is not active — login events cannot be logged at all")

    if not findings and not data["recent_pam_events"]:
        findings.append(
            "No pam_unix (login/logoff) entries found in the journal — "
            "logging mechanism may be non-functional or events aren't reaching it"
        )

    return {
        "control": "ISM-0584",
        "description": "Logon, failed logon, and logoff events are logged",
        "pass": len(findings) == 0,
        "findings": findings,
        "sample_recent_events": data["recent_pam_events"][:3],
    }


def evaluate_log_permissions(data):
    findings = []

    if not data["files"]:
        findings.append("No journal files found to check — cannot verify log protection")

    for path, mode in data["files"]:
        others_digit = int(mode[-1])
        if others_digit & 4:
            findings.append(f"ISM-1985: '{path}' (mode {mode}) is world-readable")
        if others_digit & 2:
            findings.append(f"ISM-1815: '{path}' (mode {mode}) is world-writable")

    return {
        "control": "ISM-1985 / ISM-1815",
        "description": "Event logs protected from unauthorised access and modification",
        "pass": len(findings) == 0,
        "findings": findings,
        "files_checked": data["files"],
    }


def evaluate_time_sync(data):
    findings = []

    synchronized = data.get("System clock synchronized", "").lower()
    if synchronized != "yes":
        findings.append(f"System clock is not synchronized (reported: '{synchronized or 'unknown'}')")

    ntp_service = data.get("NTP service", "").lower()
    if ntp_service != "active":
        findings.append(f"NTP service is not active (reported: '{ntp_service or 'unknown'}')")

    return {
        "control": "ISM-0988",
        "description": "An accurate and consistent time source is used",
        "pass": len(findings) == 0,
        "findings": findings,
        "raw_status": {
            "System clock synchronized": data.get("System clock synchronized", "unknown"),
            "NTP service": data.get("NTP service", "unknown"),
            "Time zone": data.get("Time zone", "unknown"),
        },
    }


def run_all_checks(host, user, ssh_key, host_label):
    """Collect real state from the given host and evaluate all six controls
    against that host's own baseline section."""
    baseline = load_baseline()

    results = []

    accounts_data = accounts_services.collect(host, user, ssh_key)
    results.append(evaluate_accounts_services(accounts_data, baseline, host_label))

    sudoers_data = sudoers.collect(host, user, ssh_key)
    results.append(evaluate_sudoers(sudoers_data, baseline, host_label))

    auth_log_data = auth_log.collect(host, user, ssh_key)
    results.append(evaluate_auth_log(auth_log_data))

    journal_glob = baseline["log_permissions"]["journal_glob"]
    log_perm_data = log_permissions.collect(host, user, ssh_key, journal_glob)
    results.append(evaluate_log_permissions(log_perm_data))

    time_sync_data = time_sync.collect(host, user, ssh_key)
    results.append(evaluate_time_sync(time_sync_data))

    return results
