"""
ISM-1985 / ISM-1815 — Event log protection (data collection only)

Targets the systemd journal files (/var/log/journal/<machine-id>/*.journal),
not /var/log/auth.log — see ISM-0584 note. Collects real permission-mode
bits via `stat`. Returns raw data only — the world-readable /
world-writable judgment happens in policy/engine.py.
"""

from collector.ssh_utils import run_remote_command


def collect(host, user, ssh_key, journal_glob):
    result = run_remote_command(host, user, ssh_key, f"stat -c '%a %n' {journal_glob}")
    if result.returncode != 0:
        return {"files": []}
    files = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        mode, path = line.split(maxsplit=1)
        files.append((path, mode))
    return {"files": files}
