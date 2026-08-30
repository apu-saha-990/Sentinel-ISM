# Sentinel — Runbook

Exact commands for running any part of the scanner. This exists so "what do I actually type, and from where" is never a guess.

## Prerequisites (one-time, already done as of 2026-08-30)

- SSH key-based auth set up from ArtX → sentinel-server (see `vm-access.md`)
- `SENTINEL_SERVER_SSH_KEY`, `SENTINEL_SERVER_HOST`, `SENTINEL_SERVER_USER` set in `.env` (git-ignored, never committed)
- PyYAML installed on ArtX: `python3 -c "import yaml"` should not error. If it does: `pip install pyyaml --break-system-packages`

## Run the ISM-0383 check (accounts/services)

**Run this on ArtX (the host) — never on the VM itself.** The script SSHes *out* to sentinel-server; it doesn't run there.

```bash
cd ~/Sentinel-ISM
python3 collector/checks/accounts_services.py
```

**Expected output shape:**

## Run the ISM-1508 check (sudoers)

**Run this on ArtX (the host) — never on the VM itself.**

```bash
cd ~/Sentinel-ISM
python3 collector/checks/sudoers.py
```

**Expected output shape:**

**Currently expected result (as of 2026-08-30):** PASS, 0 findings.


