# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the bot:**
```bash
python main.py
```

**Install dependencies:**
```bash
poetry install
# or
pip install -r requirements.txt
```

**Database migrations (Alembic):**
```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration (auto-generate from model changes)
alembic revision --autogenerate -m "description"

# Migration naming convention: YYYYMMDD_description
# e.g. alembic/versions/20260411_create_career_fair_events.py
```
Alembic reads DB credentials from `.env` (via `load_config()`).

**Deploy to production:**
```bash
./deploy.sh   # pulls latest, restarts systemd service `cbc_bot`, tails logs
```

**One-off admin scripts** (run from repo root, require `.env`):
```bash
python scripts/broadcasts/create_broadcast_type.py   # create a broadcast type in DB
python scripts/export_forum_registrations.py         # export registrations to CSV
python scripts/generate_certificates.py              # generate participant certificates
```

There is no test suite configured for this project.

## Environment variables (`.env`)

| Variable | Required | Notes |
|---|---|---|
| `BOT_TOKEN` | yes | Telegram bot token |
| `DB_USER`, `DB_PASS`, `DB_NAME`, `DB_HOST`, `DB_PORT` | yes | PostgreSQL |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | yes | Redis for FSM state |
| `ADMIN_IDS` | yes | Comma-separated Telegram user IDs |
| `GOOGLE_CREDENTIALS_PATH`, `GOOGLE_SPREADSHEET_ID` | no | Enables Google Sheets sync |
| `GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_ENABLE_DRIVE` | no | Enables Google Drive uploads |
| `DB_POOL_SIZE`, `DB_POOL_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_STATEMENT_TIMEOUT_MS`, `DB_CONNECT_TIMEOUT`, `DB_ECHO_SQL` | no | SQLAlchemy engine tuning |

## Architecture

### Startup flow (`app/bot/bot.py: main()`)
1. Load config from `.env`
2. Connect to Redis → create `RedisStorage` for aiogram FSM
3. Connect to PostgreSQL via SQLAlchemy async engine; run healthcheck
4. Wire dispatcher: routers + middlewares + aiogram-dialog → call `setup_dialogs(dp)`
5. Store `Bot` and `Dispatcher` in `AppContainer` — module-level singleton (`app/services/app_container.py`) used by APScheduler jobs, which cannot receive non-picklable objects as arguments. Access via `get_container()`.
6. On-startup tasks: cache photo/task/ICS `file_id`s, sync online lectures from `config/lectures.json` to DB, load `config/grant_lessons.json` into memory
7. Start polling loop

### Dialog system (aiogram-dialog)
All user-facing UI is built with **aiogram-dialog**. Each feature lives under `app/bot/dialogs/<feature>/` with four files:
- `states.py` — `StatesGroup` defining the dialog's state machine
- `dialogs.py` — `Dialog(Window(...))` declarations wiring widgets, getters, and handlers
- `getters.py` — async functions that supply data to window templates (injected by aiogram-dialog)
- `handlers.py` — callback/button handlers that drive state transitions

Dialogs must be registered in `bot.py: _configure_dispatcher()` via `dp.include_routers(...)`. `app/bot/dialogs/registration/` exists but is currently not registered and not reachable by normal users.

### Database layer

**Two-type pattern per table**: Every table has an ORM entity (SQLAlchemy `Base` subclass, e.g. `Users`) and a domain model dataclass (inheriting abstract `BaseModel`, e.g. `UsersModel`). Repositories always return domain models via `.to_model()` / `.from_orm()` — handlers never receive raw ORM entities.

- **Models** (ORM entities + domain models): `app/infrastructure/database/models/`
- **Repositories**: `app/infrastructure/database/database/` — one file per table (e.g. `users.py`, `forum_registrations.py`). Class names are prefixed with `_` (e.g. `_UsersDB`) to signal they are private.
- **DB facade**: `app/infrastructure/database/database/db.py` — `DB` aggregates all repository instances (`db.users`, `db.forum_registrations`, etc.). This is the only DB object handlers receive.
- **Session lifecycle**: `DatabaseMiddleware` opens one `AsyncSession` per Telegram update, wraps it in a transaction (`async with session.begin()`), and injects `db: DB` into handler data. The full handler call (including all dialog getters and transitions) runs within that single transaction. Handlers must not open their own sessions.
- **Engine**: module-level singleton in `app/infrastructure/database/sqlalchemy_core.py`. Uses `postgresql+psycopg_async` driver.

### Role system

Roles are stored as a JSONB string array in `users.roles` (e.g. `["guest"]`, `["staff"]`). Active role strings: `guest`, `staff`, `volunteer`. New users are auto-created with `["guest"]`.

Admin identity is **separate from DB roles** — it is determined by `ADMIN_IDS` in `.env`. The `AdminFilter` (`app/bot/filters/admin.py`) checks `message.from_user.id in config.admin_ids`. Admins can toggle their own DB role between `staff` and `guest` via `/ch_roles` for testing.

Note: `docs/RBAC_SYSTEM.md` describes a planned RBAC architecture (with `HasRole`/`HasMinRole` filters, role hierarchy, Redis caching, etc.) that is not yet implemented in the codebase.

### Middleware stack (applied in order)
1. `AdminLockMiddleware` — blocks all non-admin updates when `bot:lock_mode = 1` in Redis
2. `ErrorHandlerMiddleware` — top-level exception catcher
3. `DatabaseMiddleware` — creates DB session, auto-creates new users with role `guest`, injects `db`, `config`, `bot`, `redis` into handler data

### Public commands
- `/start` — routes to main menu if already registered, or `StartHelpSG.want_reg`. Supports `reg-<code>` deeplink for forum auto-registration.
- `/menu` — resets dialog stack to `MainMenuSG.MAIN`
- `/whoami` — shows user ID and username

### Admin commands (admin-only, filtered by `AdminFilter`)
Registered in `admin_lock_router` (returned by `setup_admin_lock_router()`):

| Command | Action |
|---|---|
| `/lock` / `/unlock` | Toggle `bot:lock_mode` in Redis |
| `/status` | Show lock status + admin list |
| `/ch_roles` | Toggle own role between `staff` and `guest` |
| `/sync_google` | Manually trigger Google Sheets volunteer sync |
| `/force_start` | Open registration dialog |
| `/grant_gsom <uid> <1\|0> [mentor]` | Add/remove user from GSOM grant branch |
| `/grant_lesson <uid> <tag> <1\|0>` | Unlock/lock a specific grant lesson |
| `/grant_status <uid>` | Show GSOM lesson status for a user |
| `/volunteer_review` | Open paginated volunteer part-2 review UI |
| `/dashboard` | Print forum registration statistics |
| `/config_reset` | Force-reload `grant_lessons.json` from disk |

### Feature modules
- **selections/creative** and **selections/volunteer** — two-part application flows. Part 2 has a countdown timer (`app/services/vol_part2_timer.py`).
- **online** — online lecture registration; lectures defined in `config/lectures.json` are synced to DB at startup via `app/services/online_lectures_sync.py`.
- **grants** — Росмолодёжь grants section. GSOM sub-branch controlled via `user_mentors` table; lesson unlock system driven by `config/grant_lessons.json` (in-memory cache reloadable via `/config_reset`).
- **career_fair**, **forum**, **lectory** — event registration and Q&A dialogs.
- **broadcasts** — admin dialog to send broadcast messages; broadcast types stored in DB.

### Config JSON files (`config/`)
These files drive runtime behaviour and are not migrations:
- `lectures.json` — online lecture definitions (synced to DB at startup; see `lectures.json.example`)
- `grant_lessons.json` — lesson definitions for the GSOM grants branch (`tag`, `name`, `description`, `url`)
- `tracks_config.json`, `career_info.json`, `lectory.json` — static content for feature dialogs
- `photo_file_ids.json`, `video_file_ids.json`, `ics_file_ids.json` — caches Telegram `file_id` values for static assets (populated at startup, persisted to disk)

### Google Sheets sync
`app/services/` contains per-module sync services (`volunteer_google_sync.py`, `creative_google_sync.py`, `volunteer_part2_google_sync.py`, `interview_google_sync.py`). All require `GOOGLE_CREDENTIALS_PATH` and `GOOGLE_SPREADSHEET_ID`. Google Drive upload is separately gated by `GOOGLE_ENABLE_DRIVE=true`.

### Legacy code
`app/bot/dialogs/legacy/` and `app/infrastructure/database/models/legacy/` contain old dialogs and models from a previous selection cycle. They are not registered in the dispatcher. Do not add new features there.
