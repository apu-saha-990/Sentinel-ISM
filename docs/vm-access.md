# Sentinel — VM Access Reference

This file documents *what credentials exist and where*, never the actual values.
Real secrets live only in `.env` (git-ignored, never committed).

## sentinel-server
- Host/IP: 192.168.122.126 (DHCP-assigned via libvirt default NAT network, enp1s0) — also see `SENTINEL_SERVER_HOST` in `.env`
- Hostname: sentinel-server
- SSH user: sentinel — see `SENTINEL_SERVER_USER` in `.env`
- Password: see `SENTINEL_SERVER_PASSWORD` in `.env` (only used for initial console login — prefer SSH key auth once set up)
- OpenSSH server: installed during Ubuntu Server setup

## sentinel-endpoint
- Host/IP: 192.168.122.170 (DHCP-assigned via libvirt default NAT network, enp1s0) — also see `SENTINEL_ENDPOINT_HOST` in `.env`
- Hostname: sentinel-endpoint
- SSH user: sentinelendpoint — see `SENTINEL_ENDPOINT_USER` in `.env`
- Password: see `SENTINEL_ENDPOINT_PASSWORD` in `.env`
- SSH key: reuses the same key as sentinel-server, see `SENTINEL_ENDPOINT_SSH_KEY` in `.env` (set up 2026-08-30)
- OpenSSH server: installed during Ubuntu Server setup
## Notes
- `.env` is in `.gitignore` — confirm with `git check-ignore .env` before ever committing anything, if unsure.
- Consider switching to SSH key-based auth for both VMs once basic access is confirmed working, to reduce password reliance.
- SSH key: see `SENTINEL_SERVER_SSH_KEY` in `.env` (passwordless key-based auth, set up 2026-08-30)
