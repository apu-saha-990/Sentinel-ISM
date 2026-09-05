# Sentinel — VM Access Reference

This file documents *what credentials exist and where*, never the actual values.
Real secrets live only in `.env` (git-ignored, never committed).

## sentinel-server
- Host/IP: 192.168.100.10 (static, on Sentinel-Lab network, virbr1, enp1s0) — also see `SENTINEL_SERVER_HOST` in `.env`
- Hostname: sentinel-server
- MAC address: 52:54:00:0d:b5:ab
- SSH user: sentinel — see `SENTINEL_SERVER_USER` in `.env`
- Password: see `SENTINEL_SERVER_PASSWORD` in `.env` (console/emergency use only — SSH key auth is standard)
- SSH key: see `SENTINEL_SERVER_SSH_KEY` in `.env` (passwordless key-based auth, set up 2026-08-30)
- OpenSSH server: installed during Ubuntu Server setup

- Central results record: `~/sentinel-record/results.db` (SQLite, pushed here by collector.py after every scan — see record/db.py)

## sentinel-endpoint
- Host/IP: 192.168.100.11 (static, on Sentinel-Lab network, virbr1, enp1s0) — also see `SENTINEL_ENDPOINT_HOST` in `.env`
- Hostname: sentinel-endpoint
- MAC address: 52:54:00:30:5e:a7
- SSH user: sentinelendpoint (note: different username from sentinel-server) — see `SENTINEL_ENDPOINT_USER` in `.env`
- Password: see `SENTINEL_ENDPOINT_PASSWORD` in `.env` (console/emergency use only)
- SSH key: reuses sentinel-server's key (`SENTINEL_SERVER_SSH_KEY` in `.env`), installed via `ssh-copy-id`

## Network
- Both VMs are on the isolated `Sentinel-Lab` libvirt network (device `virbr1`, subnet `192.168.100.0/24`, DHCP range `.128–.254`, NAT forwarding to the internet).
- Gateway: 192.168.100.1
- DNS: 8.8.8.8, 8.8.4.4
- Netplan config path on both VMs: `/etc/netplan/00-installer-config.yaml`
- Migration from the original `default` network (virbr0, 192.168.122.0/24, DHCP) is complete as of 2026-09-05.

## Notes
- `.env` is in `.gitignore` — confirm with `git check-ignore .env` before ever committing anything, if unsure.
- SSH key-based auth is the standard method for both VMs; password auth exists for console/emergency use only.
