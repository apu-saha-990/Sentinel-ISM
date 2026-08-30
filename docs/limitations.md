# Sentinel — Known Limitations (v1.0)

Honest, short list of what v1.0 doesn't do — so nothing here is accidentally overstated to a panel or interviewer.

## Scope limitations

- **Single host only.** Checks run against `sentinel-server` alone. No second host, no cross-host comparison, no central record of results — that's v1.1 scope, not started.
- **No scheduling or automation.** Every scan is run manually (`python3 -m collector.collector`), on demand. No cron job, no continuous monitoring, no alerting on a new finding. Deliberately out of scope per the build plan.
- **No dashboard.** Output is CLI text only. No web UI, no historical trend view, no way to compare one scan's results against a previous scan.
- **No remediation.** The scanner reports findings; it does not fix anything automatically (e.g. it won't disable `snapd` for you). This is intentional — an assessor tool should report, not silently change the system it's assessing.

## Known open findings (real, not bugs)

- **ISM-0383 currently fails** with 2 findings: `multipathd.service` and `snapd.service` are running on `sentinel-server` but not on the allow-list. This is a deliberate decision (see learning log, 2026-08-30) to keep them visible as open findings rather than either disabling them without justification or quietly allow-listing them. Not yet resolved either way.

## Design limitations

- **ISM-0584 and ISM-1985/ISM-1815 do not check `/var/log/auth.log`.** This VM has no rsyslog installed; login events are recorded only via `systemd-journald`. The checks were adapted to query `journalctl` and check journal file permissions instead — a deliberate, documented adjustment to real system state, not an oversight (see learning log, 2026-08-30).
- **ISM-1508 checks sudo *group membership* only**, not the full contents of `/etc/sudoers`/`/etc/sudoers.d/*` (e.g. it wouldn't catch a custom `NOPASSWD` rule granted outside group membership). This matches the build plan's stated scope for this control; deeper sudoers-file auditing was never part of what this control claims to check.
- **No retry or resilience logic.** If SSH to `sentinel-server` fails mid-scan (e.g. the VM's DHCP-assigned IP has changed), the scan fails with an error rather than retrying or degrading gracefully. Acceptable for a manually-run v1.0 tool; would need addressing before any kind of unattended/scheduled use.
- **Credentials/host details are environment-specific.** `.env` values (host IP, SSH key path) are specific to this exact VM and host pairing — the scanner isn't portable to a different environment without reconfiguring `.env` and re-verifying the baseline in `policy/baseline.yml` against whatever's actually running there.

## Why these limits exist

None of the above are things that "should have been done but weren't" — they're the boundary the build plan deliberately drew for v1.0: prove a working scanner against a real single VM, using only real machine state, before extending to two hosts, central records, and the deliberate-change detection test that v1.1 covers.
