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

```
ISM-0383 — Unneeded accounts/services disabled
PASS or FAIL
  - (list of findings, if any)
```

**Currently expected result (as of 2026-08-30):** FAIL, 2 findings — `multipathd.service` and `snapd.service`. This is a deliberate, known, open finding (left off the allow-list on purpose, see learning log), not a bug.

## Run the ISM-1508 check (sudoers)

**Run this on ArtX (the host) — never on the VM itself.**

```bash
cd ~/Sentinel-ISM
python3 collector/checks/sudoers.py
```

**Expected output shape:**

```
ISM-1508 — Privileged access limited to what's required
PASS or FAIL
  - (list of findings, if any)
```

**Currently expected result (as of 2026-08-30):** PASS, 0 findings.

## Run the ISM-0584 check (auth logging via journald)

**Run this on ArtX (the host) — never on the VM itself.**

```bash
cd ~/Sentinel-ISM
python3 collector/checks/auth_log.py
```

**Note:** this system has no `/var/log/auth.log` (no rsyslog installed) — the check queries `journalctl` directly instead. See learning log entry 2026-08-30 for why.

**Expected output shape:**

```
ISM-0584 — Logon, failed logon, and logoff events are logged
PASS or FAIL
  - (list of findings, if any)
  Sample recent events: (a few real log lines, if PASS)
```

**Currently expected result (as of 2026-08-30):** PASS.

## Troubleshooting

- **"Connection refused" / SSH hangs:** sentinel-server's IP is DHCP-assigned and can change on lease renewal. Check the real current IP by logging into the VM console directly and running `ip a`, then update `SENTINEL_SERVER_HOST` in `.env` if it's changed.
- **Script prompts for a password:** key auth isn't working. Test directly: `ssh -i ~/.ssh/sentinel_server_key sentinel@<host>` — if that also prompts, the key wasn't installed correctly (check `~/.ssh` is `700` and `authorized_keys` is `600` on the VM).
- **`ModuleNotFoundError: No module named 'yaml'`:** run `pip install pyyaml --break-system-packages` on ArtX (not the VM).
- **`sudo: a terminal is required to authenticate` when testing manually:** add `-t` to the ssh command to force a pseudo-terminal, e.g. `ssh -t sentinel@192.168.122.126 "sudo ..."`. The collector scripts themselves never need this — they only run commands that don't require elevated privilege (`getent`, `journalctl`, `cat /etc/passwd`, `systemctl`).
