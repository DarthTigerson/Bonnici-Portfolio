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
docker-compose up -d               # Start both services
docker-compose logs -f front       # Stream frontend logs
docker-compose logs -f admin       # Stream admin logs
docker-compose exec admin pdm run generate_admin_password
```

No test suite or linter is configured.

## Architecture

This is a **two-service FastAPI application** sharing a single SQLite database (`./data/bonnici_portfolio.db`):

- **`front/`** (port 84) — Public-facing portfolio site. Renders Jinja2 templates, handles the contact form, collects visitor device/IP data, and fires webhooks to Discord/Slack/Teams.
- **`admin/`** (port 85) — Password-protected admin panel. Manages portfolio content, contact messages, visitor analytics, and webhook configuration.

Both services are started independently (separate `uvicorn` processes) and communicate only through the shared database and JSON config file.

### Shared modules (repo root)
| File | Purpose |
|------|---------|
| `database.py` | SQLAlchemy session factory for the shared SQLite DB |
| `models.py` | ORM models: `ContactMessage`, `Entry`, `AdminToken`, `Webhook` |
| `config_manager.py` | Reads/writes `data/config.json` (profile, skills, projects) |

### Frontend (`front/`)
- `main.py` — FastAPI app init, static file mounts, template config
- `routes/home.py` — Three endpoints: `GET /` (portfolio page), `POST /contact` (form submission + webhook), `POST /device-info` (JS-collected device data)
- Visitor tracking: IP geolocation via ip-api.com, user-agent parsing via the `user-agents` library, device info posted by client JS

### Admin panel (`admin/`)
- `main.py` — FastAPI app init
- `cli.py` — `generate_password` CLI command (hashes token with SHA256, stores in DB)
- `routes/` — One file per section: `home.py` (dashboard), `admin.py` (login/logout), `messages.py`, `visitors.py`, `webhooks.py`, `portfolio.py`, `profile.py`
- Auth: token stored as SHA256 hash in `AdminToken` table; session cookie valid for 6 months; generating a new token invalidates all previous ones

### Configuration
- `data/config.json` — Portfolio content (profile, skills, projects, what_im_doing). Auto-created from `data/config_sample.json` if missing.
- `ConfigManager` enforces constraints: max 10 skill sections, specific image format rules.
- `data/` is a Docker volume; `config.json` and the SQLite DB are gitignored.

### Webhook system
Webhooks (Discord/Slack/Teams URLs stored in the `Webhook` table) are triggered on:
1. New visitor arrival
2. Contact form submission

The frontend sends HTTP POST requests to each configured webhook URL with a formatted payload.
