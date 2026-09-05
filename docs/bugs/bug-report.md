STATUS: v1.1, network migration complete, two-host scanning working, central results record built and verified on both hosts, 2 bugs fixed, 0 open

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

## BUG-002 — netplan YAML indentation lost when typed directly into VM console
**Date found:** 2026-08-31
**Version/stage:** v1.1, isolated network migration (sentinel-endpoint static IP setup)
**Symptom:** Attempted to write a netplan static-IP config directly on sentinel-endpoint's VM console using a `sudo tee ... << 'EOF'` heredoc, typing each line manually. After writing, `cat`-ing the file back showed every line flush-left with zero indentation — despite typing what looked like indented lines during entry. The resulting YAML was structurally invalid (no nesting between `network:`, `ethernets:`, `enp1s0:`, etc.).
**Root cause:** The virt-manager SPICE console (a serial/graphical terminal, not a real interactive shell with the usual line-editing support) does not reliably preserve leading whitespace when a multi-line heredoc is typed line-by-line — each new line effectively starts at column 0 regardless of intended indent. This isn't a netplan or YAML issue — it's specific to typing multi-line indented text directly into this console.
**ISM control affected (if any):** N/A — infrastructure/tooling issue, not an ISM control check
**Fix applied:** Abandoned typing the config directly on the VM console. Instead, wrote the netplan YAML file on ArtX (a real terminal where heredoc/paste correctly preserves indentation), transferred it to the VM with `scp`, then moved it into place on the VM with `sudo cp` over SSH. Verified indentation was correct with `cat` before running `netplan apply`.
**Status:** FIXED (worked around) — confirmed correct static IP (`192.168.100.11/24`) applied successfully on sentinel-endpoint using this method. Documented as the standard approach for any future file edits requiring multi-line/indented content on either VM: always compose on ArtX and transfer via `scp`, never type indented content directly into the VM console.


