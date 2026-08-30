# Sentinel — Session Handout — 2026-08-28

**Current version/stage:** v1.0, step 2 of 5 (VM built and reachable — collector scripts not yet started)

**Done this session:**
- Confirmed CPU virtualization support (`egrep -c '(vmx|svm)' /proc/cpuinfo` → 44)
- Installed KVM/QEMU/libvirt/virt-manager on host (ArtX)
- Fixed a real bug (BUG-001, see bug-report.md) where group membership didn't take effect after logout/login — needed a full reboot
- Confirmed virt-manager connects to QEMU/KVM cleanly
- Set up git identity, generated SSH key, linked to GitHub (user: apu-saha-990)
- Scaffolded the full repo structure per the build plan (collector/, policy/, record/, docs/)
- Fixed a GitHub push rejection (email privacy protection) by switching to GitHub's noreply email
- Pushed initial scaffold to https://github.com/apu-saha-990/Sentinel-ISM
- Created `.env` (real secrets, git-ignored) and `docs/vm-access.md` (references only, no secrets) for VM credentials
- Downloaded Ubuntu Server 26.04.1 LTS ISO (first attempt accidentally grabbed Desktop — corrected)
- Built `sentinel-server` VM in virt-manager: 4 vCPU / 8GB RAM / 60GB disk, Ubuntu Server (minimized) install
- Installed OpenSSH server during setup
- Confirmed SSH access from host to sentinel-server working: `ssh sentinel@192.168.122.126`
- Filled in all three v1.0 learning-log checkpoints (systemd/units, auth.log, stat vs content checks) in Apu's own words
- Added notes to learning log on the six ISM controls (plain-language) and Desktop vs Server reasoning

**Currently broken / unresolved:**
- Nothing currently broken. BUG-001 is FIXED (see bug-report.md).

**Next step:**
- Start writing the first real collector check script: ISM-0383 (unneeded accounts/services disabled), in `collector/checks/accounts_services.py`. This means:
  1. Get the real list of user accounts on sentinel-server (`/etc/passwd` or similar)
  2. Get the real list of enabled/running systemd services (`systemctl list-units --type=service`)
  3. Compare both against an allow-list (currently empty placeholders in `policy/baseline.yml` — will need to decide what the real allow-list should be based on what's actually on sentinel-server)

**Anything the next session needs to know before touching code:**
- VM access: `ssh sentinel@192.168.122.126` — password in local `.env`, never in this repo. See `docs/vm-access.md` for the reference (no secrets in that file).
- The VM is a **minimized** Ubuntu Server install — some common CLI tools may be missing and need `apt install`ing as we discover gaps (this is expected and fine, matches the "closer to baseline" choice made deliberately).
- `.env` and `.gitignore` exist locally but do NOT come through if the repo is re-downloaded as a zip from Claude — they need to be manually recreated if that ever happens again (happened once this session, cost some time).
- `policy/baseline.yml` still has empty/placeholder allow-lists (accounts, services, sudoers) — these need real values decided once we look at what's actually running on sentinel-server.
- IP `192.168.122.126` is DHCP-assigned via libvirt's default NAT network — it *could* change if the VM's DHCP lease expires and renews differently, worth double-checking with `ip a` on the VM if SSH ever stops connecting to this address.

# Sentinel — Session Handout — 2026-08-30

**Current version/stage:** v1.0 — COMPLETE. Ready to begin v1.1.

**Done this session:**
- Pulled real account list (`/etc/passwd`) and real running-services list (`systemctl --state=running`) from sentinel-server
- Built real `policy/baseline.yml` allow-lists from actual VM state (accounts: root, sentinel; services: 13 named daemons)
- Deliberately left `multipathd.service` and `snapd.service` OFF the allow-list — open finding by design, not yet resolved either way
- Set up SSH key-based auth (ArtX → sentinel-server) so the collector can run non-interactively; password auth still works for console/emergency use
- Wrote and verified all five collector checks against real VM data:
  - ISM-0383 (accounts/services) — FAIL, 2 known findings
  - ISM-1508 (sudoers) — PASS
  - ISM-0584 (auth logging) — PASS (adapted to journald; this system has no rsyslog/auth.log)
  - ISM-1985 / ISM-1815 (log permissions) — PASS (checks journal file perms, mode 640)
  - ISM-0988 (time sync) — PASS
- Refactored architecture: moved all comparison/baseline logic out of individual check scripts and centralized it in `policy/engine.py`. Check scripts now only collect raw data (`collect()` functions).
- Built `collector/collector.py` as the real `sentinel scan` entry point — runs all six controls in one pass, prints one structured report
- Added `collector/ssh_utils.py` for shared SSH connection logic (previously duplicated per-script)
- Added `docs/runbook.md` (exact commands, what runs where, expected results, troubleshooting)
- Added `docs/limitations.md` (honest scope/design limitations for panel prep)
- All learning log entries for v1.0 written up to date in `docs/learning-log/v1.0.md`
- **Post-completion verification exercise:** created two real test accounts on sentinel-server (`testuser1`, `testuser2` — both real login accounts, `/bin/bash`, passwords not stored in the repo) to verify checks against unplanned, real changes rather than just the known-good baseline:
  - `sentinel scan` correctly flagged both new accounts by name under ISM-0383, alongside the existing multipathd/snapd findings
  - Logged in as `testuser1` and confirmed `sudo whoami` is correctly denied (ISM-1508 boundary holds for a genuine non-sudo account)
  - Confirmed `testuser1`'s SSH session (open and close) shows up correctly in `journalctl -g pam_unix` (ISM-0584 catches every account's activity, not just `sentinel`'s)
- Everything (except the test-account verification work) committed and pushed to `main` in small, individually-described commits

**v1.0 "complete when" criteria (from build plan) — MET:**
`sentinel scan` (`python3 -m collector.collector`) runs on ArtX against the real VM and produces one accurate report against all six controls, using only real machine state.

**Currently broken / unresolved:**
- Nothing broken. `bug-report.md` still shows 1 bug fixed, 0 open (BUG-001 only).
- Open, non-bug item: `multipathd.service` and `snapd.service` remain undecided (deliberately not disabled, not allow-listed) — a real finding kept visible on purpose, not a defect.
- **New open item:** `testuser1` and `testuser2` now exist for real on sentinel-server (created for the verification exercise above). Decision not yet made on whether to keep them permanently (as additional open findings, same pattern as multipathd/snapd) or delete them (`sudo deluser --remove-home <user>`) now that verification is done. Current scan result reflects them as active findings under ISM-0383.
- **Not yet done:** a proper dated learning log entry for the verification exercise itself hasn't been written yet — the testing happened, but `docs/learning-log/v1.0.md` doesn't yet reflect it. Worth adding before calling this fully wrapped up.
- Test account credentials for `testuser1`/`testuser2` are being kept in a separate personal document, deliberately not in `.env` or `vm-access.md` (the collector doesn't use them for anything, so they don't belong alongside real operational secrets).

**Next step:**
Two options, Apu's choice:
1. Decide keep-or-delete on `testuser1`/`testuser2`, write the learning log entry for the verification exercise, then move to v1.1.
2. Skip straight to v1.1 per the build plan: stand up `sentinel-endpoint` VM (second monitored host), set up the isolated lab network with static IPs on both VMs, then build the central record of results on `sentinel-server`.

**Anything the next session needs to know before touching code:**
- **How to run anything:** check `docs/runbook.md` first — it has exact commands, correct working directory, and expected results for every check and the full scan. The full scan MUST be run as `python3 -m collector.collector` (module syntax) from the repo root — not as a direct file path — because of the package-style imports introduced in this session's refactor.
- **Auth:** SSH key-based auth is now the standard method to sentinel-server (`SENTINEL_SERVER_SSH_KEY` in `.env`, set up 2026-08-30). Password auth still exists for console/emergency use only. `testuser1`/`testuser2` are password-only, no SSH keys set up for them.
- **Architecture:** `collector/checks/*.py` = raw data collection only, no comparison logic. `policy/engine.py` = all comparison/pass-fail logic, in one place. Any new check (v1.1 onward) should follow this same split.
- **sentinel-server currently has 2 extra accounts beyond baseline** (`testuser1`, `testuser2`) — this is why `sentinel scan` shows more ISM-0383 findings than the original 2 (multipathd/snapd). This is expected given the verification exercise, not a new bug.
- **sentinel-server's IP** (`192.168.122.126`) is still DHCP-assigned and can drift — check `docs/runbook.md`'s troubleshooting section if a scan suddenly can't connect.
- **v1.1 will need a second VM** (`sentinel-endpoint`) and an isolated lab network with static IPs on both VMs — this is new environment work, not code work, as the first step.
