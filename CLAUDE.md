# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Local development (PDM):**
```bash
pdm install                        # Install dependencies
pdm run front                      # Run frontend on port 84
pdm run admin                      # Run admin panel on port 85
pdm run generate_admin_password    # Generate admin token (printed to stdout)
```

**Docker deployment:**
```bash
docker compose up -d               # Start both services
docker compose logs -f front       # Stream frontend logs
docker compose logs -f admin       # Stream admin logs
docker compose exec admin pdm run generate_admin_password
```

No test suite or linter is configured.

## Architecture

This is a **two-service FastAPI application** sharing a single SQLite database (`./data/bonnici_portfolio.db`):

- **`front/`** (port 84) — Public-facing portfolio site. Renders Jinja2 templates, handles the contact form, collects visitor device/IP data, and fires webhooks to Discord/Slack/Teams.
- **`admin/`** (port 85) — Password-protected admin panel. Manages portfolio content, contact messages, visitor analytics, webhook configuration, and data export/import.

Both services are started independently (separate `uvicorn` processes) and communicate only through the shared database and JSON config file.

### Shared modules (repo root)
| File | Purpose |
|------|---------|
| `database.py` | SQLAlchemy session factory for the shared SQLite DB |
| `models.py` | ORM models: `ContactMessage`, `Entry`, `AdminToken`, `Webhook` |
| `config_manager.py` | Reads/writes `data/config.json` (profile, skills, projects) |

### Frontend (`front/`)
- `main.py` — FastAPI app init, static file mounts
- `routes/home.py` — Three endpoints: `GET /` (portfolio page), `POST /contact` (form submission + webhook), `POST /device-info` (JS-collected device data)
- Visitor tracking: IP geolocation via ip-api.com (localhost replaced with 8.8.8.8 for testing), user-agent parsing via the `user-agents` library, device info posted by client JS then cached in-memory until contact form ties it to a DB entry

### Admin panel (`admin/`)
- `main.py` — FastAPI app init
- `cli.py` — `generate_password` CLI command (hashes token with SHA256, stores in DB, deletes all previous tokens)
- `routes/` — One file per section: `home.py` (dashboard), `admin.py` (login/logout), `messages.py`, `visitors.py`, `webhooks.py`, `portfolio.py`, `profile.py`, `settings.py` (export/import)
- Auth: token stored as SHA256 hash in `AdminToken` table; session cookie (httponly, samesite=lax) valid for 6 months; `secure=True` requires HTTPS — set to `False` for plain HTTP access during server setup

### Configuration
- `data/config.json` — Portfolio content (profile, skills, projects, what_im_doing). Auto-created from `data/config_sample.json` if missing.
- `ConfigManager` enforces constraints: max 10 skill sections, `.webp`-only for skill images.
- `data/` is a Docker volume; `config.json` and the SQLite DB are gitignored.

### Data export/import (`admin/routes/settings.py`)
- Export: streams a ZIP containing `config.json`, `webhooks.json`, and all referenced images (profile, skills, portfolio). Admin token is intentionally excluded.
- Import: fully overwrites `config.json`, replaces all webhooks in DB, and extracts images to `data/images/`. Per-file error isolation ensures one failed image doesn't abort the rest; response includes `extracted` and `warnings` arrays.
- Profile image is always at `data/images/profile.webp` (fixed path, not referenced in config).

### Webhook system
Webhooks (Discord/Slack/Teams URLs stored in the `Webhook` table) are triggered on new visitor arrival and contact form submission. Platform is auto-detected from URL pattern; each platform gets a custom-formatted payload.
