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

# Sentinel — Session Handout — 2026-08-30 (v1.1 start)

**Current version/stage:** v1.1, early stage — sentinel-endpoint VM built, isolated network and central record not yet done

**Done this session:**
- Built sentinel-endpoint VM in virt-manager: 2 vCPU / 4096 MiB RAM / 30GB disk, Ubuntu Server 26.04.1 LTS (minimized), matching sentinel-server's install pattern
- Installed OpenSSH server during setup (checked the box this time, unlike default)
- Confirmed SSH access from ArtX: `ssh sentinelendpoint@192.168.122.170` (password auth first, then switched to key-based)
- Reused sentinel-server's existing SSH key (`~/.ssh/sentinel_server_key`) for sentinel-endpoint via `ssh-copy-id` — confirmed passwordless login works
- Updated `docs/vm-access.md` with real sentinel-endpoint host/user/key references (no secrets in the file itself)
- Added SENTINEL_ENDPOINT_HOST, SENTINEL_ENDPOINT_USER, SENTINEL_ENDPOINT_PASSWORD, SENTINEL_ENDPOINT_SSH_KEY to local `.env`

**Currently broken / unresolved:**
- Nothing broken. bug-report.md still shows 1 bug fixed, 0 open (BUG-001 only).

**Next step:**
Build the isolated lab network with static IPs on both VMs (v1.1 build plan, environment work before any new code). Both VMs are currently still on the default NAT/DHCP network (sentinel-server: 192.168.122.126, sentinel-endpoint: 192.168.122.170) — this step changes that.

**Anything the next session needs to know before touching code:**
- sentinel-endpoint disk is 25GB→ wait, actually 30GB (matches plan) — confirmed during install, no deviation to note.
- sentinel-endpoint username is `sentinelendpoint` (not `sentinel` like the other VM) — different username between the two hosts, worth remembering when scripting against both.
- Switching network config on a live SSH session risks locking yourself out mid-change — go slowly, verify each VM is still reachable before moving to the next config change.
- No learning log entry written yet for v1.1 — should be added before v1.1 is called complete, per project rules.

# Sentinel — Session Handout — 2026-08-31

**Current version/stage:** v1.1, in progress — isolated network migration started, sentinel-endpoint done, sentinel-server not yet done

**Done this session:**
- Created new isolated libvirt network "Sentinel-Lab" (device `virbr1`, subnet `192.168.100.0/24`, DHCP range `.128–.254`, NAT forwarding) — separate from the original `default` network (`virbr0`, `192.168.122.0/24`) both VMs were on
- Switched sentinel-endpoint's NIC from `default` to `Sentinel-Lab` via virt-manager hardware settings (VM was shut off at the time, zero risk)
- Booted sentinel-endpoint, confirmed it picked up a DHCP address on the new network via console (`192.168.100.163`)
- Wrote a static netplan config for sentinel-endpoint: static IP `192.168.100.11/24`, gateway `192.168.100.1` (the Sentinel-Lab bridge), DNS `8.8.8.8`/`8.8.4.4`
- **Learned the hard way:** typing multi-line YAML directly into the VM console loses indentation (console doesn't preserve leading spaces reliably) — the fix was writing the netplan file on ArtX instead (where paste/indentation works normally), then `scp`-ing it to the VM and moving it into place with `sudo cp` over SSH
- Applied the new netplan config (`sudo netplan apply`) — this dropped the old SSH session (expected, since the IP changed mid-session) — reconnected successfully on the new static IP `192.168.100.11` using the same SSH key as before
- Confirmed internet access still works on the isolated network via `curl` (got HTTP 200 from archive.ubuntu.com) — `ping` isn't available on this minimized install, not installed just for this check
- Updated `docs/vm-access.md`: sentinel-endpoint's Host/IP now shows `192.168.100.11` (static, on Sentinel-Lab, virbr1)
- Updated local `.env`: `SENTINEL_ENDPOINT_HOST` changed to `192.168.100.11`
- Committed and pushed: `docs/vm-access.md` and `docs/handout-latest.md` (commit `5d8c770`)

**Currently broken / unresolved:**
- Nothing broken. One terminal window on ArtX got stuck on a dead SSH session after the netplan apply (expected side effect of changing the IP mid-session) — harmless, just close it, a fresh terminal connected fine.
- **sentinel-server is still on the old `default` NAT network** at `192.168.122.126` — not yet migrated. This is the main unfinished piece of the network step.

**Next step:**
Repeat the same migration on sentinel-server: switch its NIC to `Sentinel-Lab` (VM must be shut off first), assign static IP `192.168.100.10/24` (reserved, not yet used), same gateway (`192.168.100.1`) and DNS (`8.8.8.8`/`8.8.4.4`) as sentinel-endpoint. Use the same "write netplan file on ArtX, scp it over, sudo cp into place" method — don't try typing YAML directly into the VM console again.

**Anything the next session needs to know before touching code:**
- **Static IP plan:** sentinel-server → `192.168.100.10`, sentinel-endpoint → `192.168.100.11` (already done). Keep this convention for any future hosts.
- **Netplan file path on both VMs:** `/etc/netplan/00-installer-config.yaml`
- **sentinel-endpoint's MAC address** (needed if rewriting its netplan again): `52:54:00:30:5e:a7` — sentinel-server's MAC will need to be checked fresh (`ip a` on its console) since it hasn't been recorded yet on the new network.
- **`nano` is not installed** on either minimized VM — don't suggest it for editing files on the VMs directly; use the ArtX-then-scp method instead.
- Once sentinel-server is migrated too, `.env` (`SENTINEL_SERVER_HOST`) and `docs/vm-access.md` need the same kind of update sentinel-endpoint just got.
- After both VMs are on the isolated network with static IPs, the v1.1 build plan's next piece is the central record of results on sentinel-server (new code: `record/db.py`) — not started yet.
- No v1.1 learning log entry written yet — worth adding one covering today's console-indentation lesson before v1.1 is called complete.


# Sentinel — Session Handout — 2026-09-05

**Current version/stage:** v1.1, in progress — network migration complete, two-host scanning now working, not yet committed

**Done this session:**
- Migrated sentinel-server onto the isolated Sentinel-Lab network: shut off VM, switched NIC from `default` (virbr0) to `Sentinel-Lab` (virbr1) in virt-manager, confirmed temporary DHCP address via console (`192.168.100.190`), recorded MAC address (`52:54:00:0d:b5:ab`)
- Wrote and applied static netplan config for sentinel-server (`192.168.100.10/24`, gateway `192.168.100.1`, DNS `8.8.8.8`/`8.8.4.4`) using the ArtX-then-scp method from BUG-002 — no repeat of the console-indentation bug
- Confirmed clean SSH reconnect on the new static IP with no password prompt
- Updated `.env` (`SENTINEL_SERVER_HOST` → `192.168.100.10`) and cleaned up duplicate blank `SENTINEL_ENDPOINT_*` lines that had been left in `.env` from an earlier session
- Updated `docs/vm-access.md` with both hosts' real IPs, MACs, and a new shared `## Network` section for the Sentinel-Lab subnet/gateway/DNS
- Both VMs are now fully on Sentinel-Lab with static IPs — network migration portion of v1.1 is complete
- Re-ran `sentinel scan` against sentinel-server post-migration to confirm nothing broke — same results as before (4/5, known findings only)
- **Refactored the collector to scan both hosts in one run:**
  - `policy/engine.py`: `run_all_checks()` now takes `host`, `user`, `ssh_key`, `host_label` as parameters instead of reading `.env` internally
  - `collector/collector.py`: now loads `.env` itself, defines both hosts, loops over them, prints a separate labeled report per host
  - Checked `collector/ssh_utils.py` first to confirm `SENTINEL_ENDPOINT_SSH_KEY`'s `~`-path wouldn't break anything — it's fine, `ssh` expands `~` internally regardless of shell
- Ran the two-host scan for the first time — sentinel-endpoint showed false-positive findings caused by a shared baseline built only from sentinel-server's account name and service list
- Pulled sentinel-endpoint's real running-services list via `systemctl list-units --type=service --state=running` (not guessed) and restructured `policy/baseline.yml` into per-host sections (`hosts: sentinel-server: / sentinel-endpoint:`), keeping `log_permissions` shared since the journal path pattern is the same on both
- Identified and documented a real, transient false-positive: `systemd-timedated.service` briefly showed as a finding on sentinel-endpoint because it's D-Bus-activated and gets woken up by the ISM-0988 check's own `timedatectl` call, then stops when idle — deliberately not added to the allow-list since doing so would mask a genuine future activation
- Re-ran the two-host scan after the baseline fix: sentinel-server unchanged (4/5, known findings), sentinel-endpoint now correctly shows 4/5 with only the genuine open findings (multipathd, snapd) — the account/sudoers false positives are gone

**Currently broken / unresolved:**
- Nothing broken. bug-report.md still shows 1 bug fixed, 0 open (BUG-001, BUG-002 both FIXED).
- **Not yet committed** — `git status` shows all of today's changes as modified/untracked, nothing staged yet.
- **Filename mismatch caught before committing:** the learning-log file got saved locally as `docs/learning-log/v1_0.md` (underscore) instead of the original `v1.0.md` (dot), so git currently shows the original as deleted and the new one as untracked. Needs `mv docs/learning-log/v1_0.md docs/learning-log/v1.0.md` before staging, so git tracks it as one continuous file rather than a delete+add.

**Next step:**
1. Fix the learning-log filename (`mv` command above), confirm with `git status` that it now shows as modified, not deleted+untracked.
2. Stage and commit today's changes with an explicit file list (`collector/collector.py`, `policy/engine.py`, `policy/baseline.yml`, `docs/vm-access.md`, `docs/learning-log/v1.0.md`, `docs/handout-latest.md`, `docs/bugs/bug-report.md` — check `git status` again to confirm the full real list before staging, don't assume this one is complete).
3. After that's pushed: two things remain before v1.1 can be called complete — the deliberate-change detection test on sentinel-endpoint (add a sudo user, confirm the next scan catches it), and building `record/db.py` for a central results record on sentinel-server.

**Anything the next session needs to know before touching code:**
- **The scanner now requires `host_label` as a 4th argument to `run_all_checks()`** — any future check or script calling it directly (not through `collector.py`) needs updating to match, or it'll throw a `TypeError`.
- **`policy/baseline.yml` is no longer a flat structure** — accounts/services/sudoers now live under `hosts: <host_label>:`, with only `log_permissions` staying at the top level. Any manual edits to the baseline need to go in the right host's section now.
- **sentinel-endpoint's real baseline was built from actual `systemctl` output pulled today (2026-09-05)** — same honesty standard as sentinel-server's original baseline, not assumed or copied.
- `docs/roadmap.md` exists as an untracked file per the last `git status` — not part of today's work, just noting it's sitting there uncommitted if that wasn't intentional.
- `.env` had duplicate blank `SENTINEL_ENDPOINT_*` lines removed this session — if `.env` ever needs recreating from scratch, don't reintroduce that duplication.


# Sentinel — Session Handout — 2026-09-05 (central record)

**Current version/stage:** v1.1, in progress — central record of results built and verified, deliberate-change test not yet done

**Done this session:**
- Built `record/db.py`: local SQLite database (three tables — scan_runs, control_results, findings) recording every scan's results
- Added `copy_file_to_remote()` to `collector/ssh_utils.py`; updated `collector/collector.py` to write each host's results to the database and push the finished file to sentinel-server via SCP after every run
- Verified end to end: database created correctly on ArtX, identical copy confirmed on sentinel-server at `~/sentinel-record/results.db`, all three tables checked directly and contain correct, correctly-linked data
- Noted `systemd-timedated.service` now also appears transiently on sentinel-server (previously only seen on sentinel-endpoint) — same D-Bus-activation explanation, not a bug
- Decided `record/*.db` stays out of git (already covered by existing `*.db` rule in `.gitignore`); confirmed with `git check-ignore`
- Updated `docs/learning-log/v1.1.md`, `docs/bugs/bug-report.md` (status line), `docs/vm-access.md`
- Committed and pushed: [fill in commit hash once pushed]

**Currently broken / unresolved:**
- Nothing broken. bug-report.md still shows 2 bugs fixed, 0 open.

**Next step:**
The deliberate-change detection test on sentinel-endpoint: add a real sudo user (or similar out-of-baseline change) on sentinel-endpoint, run the scan, and confirm it's correctly caught as a new ISM-1508 (or relevant control) finding. This is the last outstanding item for v1.1's "complete when" criteria per the build plan.

**Anything the next session needs to know before touching code:**
- `record/db.py` is not run standalone — it's only called from `collector.py`. Any new script that needs to read scan history should import `get_connection()` from `record/db.py` rather than opening the SQLite file directly.
- The authoritative results database is on sentinel-server (`~/sentinel-record/results.db`), not the ArtX copy — the ArtX copy is just the working copy before each transfer.
- Once the deliberate-change test is done, the only other item before v1.1 can be called complete per the build plan is nothing else — that test is the last piece.
