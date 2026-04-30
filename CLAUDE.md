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
Alembic reads DB credentials from `.env` (via `load_config()`), or from `DATABASE_URL` env var directly.

**Deploy to production:**
```bash
./deploy.sh   # pulls latest, restarts systemd service `cbc_bot`, tails logs
```

**One-off admin scripts** (run from repo root, require `.env`):
```bash
python scripts/broadcasts/create_broadcast_type.py   # create a broadcast type in DB
python scripts/export_forum_registrations.py         # export registrations to CSV
```

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
4. Wire dispatcher: routers + middlewares + aiogram-dialog
5. Store `Bot` and `Dispatcher` in `AppContainer` (module-level singleton used by APScheduler jobs)
6. On-startup checks: upload any new photos/task files to Telegram to cache their `file_id`, sync online lectures from config, load grant lessons config, sync ICS calendar files
7. Start polling loop

### Dialog system (aiogram-dialog)
All user-facing UI is built with **aiogram-dialog**. Each feature lives under `app/bot/dialogs/<feature>/` with four files:
- `states.py` — `StatesGroup` defining the dialog's state machine
- `dialogs.py` — `Dialog(Window(...))` declarations wiring widgets, getters, and handlers
- `getters.py` — async functions that supply data to window templates (injected by aiogram-dialog)
- `handlers.py` — callback/button handlers that drive state transitions

Dialogs are registered in `bot.py: _configure_dispatcher()` via `dp.include_routers(...)`.

### Database layer
- **Models**: SQLAlchemy ORM models in `app/infrastructure/database/models/`
- **DB facade**: `app/infrastructure/database/database/db.py` — `DB` class aggregates all per-table repository classes (e.g. `db.users`, `db.forum_registrations`, `db.volunteer_applications`). This is the only database object handlers receive.
- **Session lifecycle**: `DatabaseMiddleware` opens one `AsyncSession` per update, wrapped in a transaction, and injects `db: DB` into handler data. Handlers must not manage their own sessions.
- **Engine**: module-level singleton in `app/infrastructure/database/sqlalchemy_core.py`. Uses `postgresql+psycopg_async` driver.

### Middleware stack (applied in order)
1. `AdminLockMiddleware` — blocks all non-admin updates when `bot:lock_mode = 1` in Redis
2. `ErrorHandlerMiddleware` — top-level exception catcher
3. `DatabaseMiddleware` — creates DB session, auto-creates new users with role `guest`, injects `db`, `config`, `bot`, `redis` into handler data

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
- **online** — online lecture registration; lectures are synced from a config file at startup via `app/services/online_lectures_sync.py`.
- **grants** — Росмолодёжь grants section with a GSOM sub-branch controlled via `user_mentors` table and lesson unlock system configured in `grant_lessons.json`.
- **career_fair**, **forum**, **lectory** — event registration and Q&A dialogs.
- **broadcasts** — admin dialog to send broadcast messages; broadcast types stored in DB.

### Google Sheets sync
`app/services/` contains per-module sync services (e.g. `volunteer_google_sync.py`, `creative_google_sync.py`). All require `GOOGLE_CREDENTIALS_PATH` and `GOOGLE_SPREADSHEET_ID`. Google Drive upload is separately gated by `GOOGLE_ENABLE_DRIVE=true`.

### File ID management
Photos and task files are uploaded to Telegram once at startup so their Telegram `file_id` values are cached. Managers: `app/services/photo_file_id_manager.py`, `app/services/task_file_id_manager.py`, `app/services/ics_file_id_manager.py`.

### Legacy code
`app/bot/dialogs/legacy/` contains old dialogs from a previous selection cycle. They are not registered in the dispatcher but kept for reference. Do not add new features there.
