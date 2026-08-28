STATUS: v1.0, step 1/5 (KVM/libvirt/virt-manager confirmed working, VM not yet created), 1 bug fixed, 0 open

# Sentinel — Bug Report

This file is append-only. Fixed bugs stay in the record — never delete or rewrite past entries.

Format for each entry:

```
## BUG-00X — [short title]
**Date found:** [date]
**Version/stage:** [e.g. v1.0, ISM-0584 check]
**Symptom:** what actually happened / what looked wrong
**Root cause:** what was actually going on underneath — not just the fix
**ISM control affected (if any):** [control number, or "N/A — infrastructure/tooling issue"]
**Fix applied:** what changed
**Status:** OPEN / FIXED / WORKAROUND (explain if workaround)
```

---

## BUG-001 — virt-manager can't connect to qemu:///system despite usermod
**Date found:** 2026-08-28
**Version/stage:** v1.0, environment setup (pre-VM, installing KVM/QEMU/libvirt)
**Symptom:** After running `sudo usermod -aG libvirt,kvm $USER` and logging out/back in, `virt-manager` still showed "Unable to connect to libvirt qemu:///system" / "QEMU/KVM - Not Connected". `groups` and `id` both showed no `libvirt` or `kvm` group membership, even though `getent group` confirmed the user was correctly added to both groups on disk.
**Root cause:** A logout/login is not always enough to refresh a session's group membership — it depends on the desktop environment/display manager, which can cache the session's initial group list from before the usermod ran. Only a full reboot (not just logout/login) reliably re-reads group membership for a graphical session.
**ISM control affected (if any):** N/A — infrastructure/tooling issue, not an ISM control check
**Fix applied:** Performed a full reboot (not logout/login) to force the session to re-read group membership.
**Status:** FIXED — confirmed after full reboot: `id` now shows `libvirt(125)` and `kvm(993)` in the session's active groups, and virt-manager connects to QEMU/KVM with no error dialog.
