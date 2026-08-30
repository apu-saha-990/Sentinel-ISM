"""
ISM-0988 — An accurate and consistent time source is used

Confirms sentinel-server's clock is actually synchronized via NTP, not just
that a time-sync package is installed. Reads real output from `timedatectl`,
which reports both whether an NTP mechanism is active and whether the clock
is currently, actually synchronized — these are two different things (a
service can be running but not yet have achieved sync, e.g. right after
boot or a network outage).

No simulated or placeholder data — every result reflects the actual
timedatectl output on sentinel-server at the moment the check runs.
"""

import subprocess


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
    if result.returncode != 0:
        raise RuntimeError(f"SSH command failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def parse_timedatectl(raw):
    """Parse timedatectl's 'Key: Value' output into a dict."""
    values = {}
    for line in raw.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip()
    return values


def run_check():
    env = load_env()
    host = env["SENTINEL_SERVER_HOST"]
    user = env["SENTINEL_SERVER_USER"]
    ssh_key = env["SENTINEL_SERVER_SSH_KEY"]

    raw = run_remote_command(host, user, ssh_key, "timedatectl")
    values = parse_timedatectl(raw)

    findings = []

    synchronized = values.get("System clock synchronized", "").lower()
    if synchronized != "yes":
        findings.append(f"System clock is not synchronized (reported: '{synchronized or 'unknown'}')")

    ntp_service = values.get("NTP service", "").lower()
    if ntp_service != "active":
        findings.append(f"NTP service is not active (reported: '{ntp_service or 'unknown'}')")

    return {
        "control": "ISM-0988",
        "description": "An accurate and consistent time source is used",
        "pass": len(findings) == 0,
        "findings": findings,
        "raw_status": {
            "System clock synchronized": values.get("System clock synchronized", "unknown"),
            "NTP service": values.get("NTP service", "unknown"),
            "Time zone": values.get("Time zone", "unknown"),
        },
    }


if __name__ == "__main__":
    result = run_check()
    print(f"{result['control']} — {result['description']}")
    print("PASS" if result["pass"] else "FAIL")
    for f in result["findings"]:
        print(f"  - {f}")
    print("  Status:")
    for k, v in result["raw_status"].items():
        print(f"    {k}: {v}")
