"""
ISM-1508 — Privileged access limited to what's required

Connects to sentinel-server over SSH (key-based auth) and pulls the real
membership of the 'sudo' group, then compares it against the allow-list in
policy/baseline.yml. Flags any member of the sudo group who is not
explicitly expected — the point of this control is catching privilege
creep, not judging whether existing members deserve access.

Only checks group membership, per the build plan — this does not parse
/etc/sudoers or /etc/sudoers.d/* for rule-level detail (e.g. NOPASSWD
overrides). Group membership is the checkable signal the build plan
specifies for this control; broader sudoers-file auditing is out of scope.

No simulated or placeholder data — every result reflects the actual sudo
group membership on sentinel-server at the moment the check runs.
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
        raise RuntimeError(
            f"SSH command failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def get_sudo_group_members(host, user, ssh_key):
    """Return list of usernames in the 'sudo' group, from getent group sudo."""
    raw = run_remote_command(host, user, ssh_key, "getent group sudo").strip()
    # Format: sudo:x:27:user1,user2,user3
    fields = raw.split(":")
    if len(fields) < 4 or not fields[3]:
        return []
    return [name.strip() for name in fields[3].split(",")]


def check_sudoers(members, allowed_members):
    """Flag any sudo group member not explicitly on the allow-list."""
    findings = []
    for member in members:
        if member not in allowed_members:
            findings.append(f"'{member}' is a member of the sudo group but is not on the allow-list")
    return findings


def run_check():
    env = load_env()
    baseline = load_baseline()

    host = env["SENTINEL_SERVER_HOST"]
    user = env["SENTINEL_SERVER_USER"]
    ssh_key = env["SENTINEL_SERVER_SSH_KEY"]

    members = get_sudo_group_members(host, user, ssh_key)
    findings = check_sudoers(members, baseline["sudoers"]["allowed_members"])

    return {
        "control": "ISM-1508",
        "description": "Privileged access limited to what's required",
        "pass": len(findings) == 0,
        "findings": findings,
    }


if __name__ == "__main__":
    result = run_check()
    print(f"{result['control']} — {result['description']}")
    print("PASS" if result["pass"] else "FAIL")
    for f in result["findings"]:
        print(f"  - {f}")
