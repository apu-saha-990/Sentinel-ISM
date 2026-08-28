# Sentinel — VM Access Reference

This file documents *what credentials exist and where*, never the actual values.
Real secrets live only in `.env` (git-ignored, never committed).

## sentinel-server
- Host/IP: see `SENTINEL_SERVER_HOST` in `.env`
- SSH user: see `SENTINEL_SERVER_USER` in `.env`
- Password: see `SENTINEL_SERVER_PASSWORD` in `.env` (only used for initial console login — prefer SSH key auth once set up)
- OpenSSH server: installed during Ubuntu Server setup

## sentinel-endpoint (v1.1, not yet created)
- Host/IP: see `SENTINEL_ENDPOINT_HOST` in `.env`
- SSH user: see `SENTINEL_ENDPOINT_USER` in `.env`
- Password: see `SENTINEL_ENDPOINT_PASSWORD` in `.env`

## Notes
- `.env` is in `.gitignore` — confirm with `git check-ignore .env` before ever committing anything, if unsure.
- Consider switching to SSH key-based auth for both VMs once basic access is confirmed working, to reduce password reliance.
