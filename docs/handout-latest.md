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
