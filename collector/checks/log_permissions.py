"""
ISM-1985 — Event logs protected from unauthorised access (not world-readable)
ISM-1815 — Event logs protected from unauthorised modification/deletion (not world-writable)

Combined into one check since both controls examine the same files, just
different bits of the same permission mode. Targets the systemd journal
files (see ISM-0584 note: this system has no /var/log/auth.log, journald
is the real log mechanism here).

Reads real file permission bits via `stat` over SSH — pure metadata check,
no file content is read (permission checks and content checks are a
deliberately different thing, per the v1.0 learning log).

No simulated or placeholder data — every result reflects the actual
permission bits on sentinel-server's journal files at the moment the
check runs.
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


def load_baseline(baseline_path="policy/baseline.yml"):
    with open(baseline_path) as f:
        return yaml.safe_load(f)


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
    if result.returncode != 0:
        raise RuntimeError(f"SSH command failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def get_journal_file_permissions(host, user, ssh_key, journal_glob):
    """Return list of (path, octal_mode) for all files matching the glob."""
    raw = run_remote_command(
        host, user, ssh_key,
        f"stat -c '%a %n' {journal_glob}"
    )
    files = []
    for line in raw.strip().splitlines():
        if not line.strip():
            continue
        mode, path = line.split(maxsplit=1)
        files.append((path, mode))
    return files


def check_not_world_readable(mode):
    """ISM-1985: the 'others' digit (last of 3) must not include read (4)."""
    others_digit = int(mode[-1])
    return not (others_digit & 4)


def check_not_world_writable(mode):
    """ISM-1815: the 'others' digit (last of 3) must not include write (2)."""
    others_digit = int(mode[-1])
    return not (others_digit & 2)


def run_check():
    env = load_env()
    baseline = load_baseline()

    host = env["SENTINEL_SERVER_HOST"]
    user = env["SENTINEL_SERVER_USER"]
    ssh_key = env["SENTINEL_SERVER_SSH_KEY"]
    journal_glob = baseline["log_permissions"]["journal_glob"]

    files = get_journal_file_permissions(host, user, ssh_key, journal_glob)

    findings = []
    if not files:
        findings.append(f"No files matched journal glob '{journal_glob}' — cannot verify log protection")

    for path, mode in files:
        if not check_not_world_readable(mode):
            findings.append(f"ISM-1985: '{path}' (mode {mode}) is world-readable")
        if not check_not_world_writable(mode):
            findings.append(f"ISM-1815: '{path}' (mode {mode}) is world-writable")

    return {
        "control": "ISM-1985 / ISM-1815",
        "description": "Event logs protected from unauthorised access and modification",
        "pass": len(findings) == 0,
        "findings": findings,
        "files_checked": files,
    }


if __name__ == "__main__":
    result = run_check()
    print(f"{result['control']} — {result['description']}")
    print("PASS" if result["pass"] else "FAIL")
    for f in result["findings"]:
        print(f"  - {f}")
    if result["files_checked"]:
        print("  Files checked:")
        for path, mode in result["files_checked"]:
            print(f"    {mode}  {path}")
