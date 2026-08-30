"""
Shared SSH helper for all collector checks — every check module reaches
sentinel-server the same way, so this keeps that logic in exactly one place
rather than duplicated across check scripts.
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
    """Run a command on sentinel-server over SSH using key-based auth."""
    ssh_cmd = [
        "ssh",
        "-i", ssh_key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        f"{user}@{host}",
        command,
    ]
    return subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
    
    
