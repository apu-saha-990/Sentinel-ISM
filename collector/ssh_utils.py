"""
Shared SSH helper for all collector checks — every check module reaches
its target host the same way, so this keeps that logic in exactly one
place rather than duplicated across check scripts.

As of v1.1, also holds copy_file_to_remote() — the SCP equivalent of
run_remote_command(), used to push the central results database
(record/sentinel_results.db) to sentinel-server after each scan.
"""

import subprocess


def load_env(env_path=".env"):
    """Minimal .env loader — avoids adding a dependency just for this."""
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
    """Run a command on a remote host over SSH using key-based auth."""
    ssh_cmd = [
        "ssh",
        "-i", ssh_key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        f"{user}@{host}",
        command,
    ]
    return subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)


def copy_file_to_remote(local_path, host, user, ssh_key, remote_path):
    """Copy a local file to a remote host over SCP using the same
    key-based auth as run_remote_command(). Used to push the finished
    results database to sentinel-server after each scan run.

    Note: SCP does not create the destination directory for you — the
    remote directory must already exist. collector.py runs a
    'mkdir -p' over run_remote_command() first for this reason.
    """
    scp_cmd = [
        "scp",
        "-i", ssh_key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        local_path,
        f"{user}@{host}:{remote_path}",
    ]
    return subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
