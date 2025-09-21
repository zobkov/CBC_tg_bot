# CBC Crew Selection Bot - AI Coding Instructions

## Project Overview
This is a Telegram bot for managing a multi-stage selection process for the China-Russia Business Congress (КБК) crew recruitment. Built with aiogram 3.x, aiogram-dialog, PostgreSQL, Redis, and Google Sheets integration.

## Architecture & Core Components

### Data Flow & Database Structure
- **Single PostgreSQL database**: Applications DB (legacy main DB consolidated)
- **Redis**: FSM state storage and APScheduler job store  
- **Google Sheets/Drive**: Resume export and external data sync
- **Applications table**: Core entity with priority system (3 department/position choices + subdepartments)

### Key Service Boundaries
- `app/bot/`: Telegram bot logic (handlers, dialogs, FSM states)
- `app/infrastructure/`: Database connections, Redis, storage abstractions
- `app/services/`: Business logic (broadcasting, photo management, Google integration)
- `config/`: Environment-based configuration with JSON selection rules

### Dialog System (aiogram-dialog)
- Multi-window form flows in `app/bot/dialogs/`
- Each dialog: `dialogs.py` (window definitions) + `getters.py` (data) + `handlers.py` (callbacks)
- FSM states in `app/bot/states/` define conversation flows
- Current dialogs: `first_stage/`, `job_selection/`, `main_menu/`, `start/`, `settings/`

## Critical Development Patterns

### Configuration Management
```python
# Load from environment + JSON configs
config = load_config()  # Combines .env + selection_config.json + departments.json
```
- **Secret data**: Environment variables (BOT_TOKEN, DB credentials)
- **Business rules**: JSON files (`selection_config.json`, `departments.json`)
- **departments.json** supports nested subdepartments with complex hierarchy:
```json
"creative": {
  "subdepartments": {
    "stage": {"positions": ["Хореограф", "Сценарист"]},
    "workshops": {"positions": ["Ведущий мастер-класса"]}
  }
}
```

### Database Operations
```python
# Single database setup (users table moved to applications DB)
db = DB(users_connection=conn, applications_connection=conn)
# Priority system: department_1/position_1/subdepartment_1, _2, _3
await db.applications.update_application(user_id, department_1="creative", subdepartment_1="stage")
```

### Photo/Media File Management
- **PhotoFileIdManager**: Manages Telegram file_id for assets in `app/bot/assets/images/`
- **Startup validation**: `startup_photo_check()` validates file_ids on bot startup
- **File_id storage**: `config/photo_file_ids.json` maps relative paths to Telegram file_ids
```python
# Get file_id for dialog media
from app.utils.optimized_dialog_widgets import get_file_id_for_path
file_id = get_file_id_for_path("department/creative.jpg")
```

### Dialog State Management
- Use `dp["config"]`, `dp["bot"]`, `dp["db_applications"]` for dependency injection
- Dialog handlers must be async and handle FSM transitions
- **File upload patterns**: `process_resume_file()` handles document uploads with filename generation
- **Resume storage**: Files saved to `app/storage/resumes/` with format `{surname}_{initials}_{username}_{timestamp}.ext`
- **Priority selection system**: Users select 3 department/position combos with conflict validation

### Migration System
- SQL files in `migrations/` with sequential numbering (000-007 applied)
- Run via `run_applications_migrations.py` for applications DB
- **Latest migration 007**: Added subdepartment support (subdepartment_1, _2, _3 columns)
- Track applied migrations in dedicated table

## Development Workflows

### Local Development
```bash
# Environment setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Database setup
python run_applications_migrations.py

# Bot startup
python main.py
```

### Production Deployment
```bash
# Systemd service management
./restart_bot.sh  # Restarts service + follows logs
```

### Background Services
- **BroadcastScheduler**: APScheduler with Redis persistence for time-based messaging
- **Photo file_id regeneration**: Telegram file_id validation on startup
- **Task management**: Current system supports task dialogs (placeholder for future task assignments)

## Integration Points

### Google Services Integration
- Optional Google Sheets export (controlled by `GOOGLE_ENABLE_DRIVE` env var)
- Resume file uploads to Google Drive with URL tracking
- Credentials in `google_credentials.json` (template provided)

### Redis Dependencies
- **Required** for FSM state storage and scheduler persistence
- Connection handling with password auth support
- Bot cannot start without Redis connection

### External Data Sources
- Stage timing and department structures loaded from JSON configs
- Position mappings support subdepartments (see `departments.json` structure)
- Support contacts and application rules in `selection_config.json`

## Testing & Debugging
- Test files follow pattern `test_*.py` in root directory
- Dialog testing via specific test dialogs in `app/bot/dialogs/test/`
- Error logging to `app/logs/` with structured JSON error reports
- Use `generate_timeseries_stats.py` for application analytics
- **Photo regeneration**: Use `regenerate_photo_file_ids.py` for manual file_id updates

## Common Gotchas
- File paths in dialogs use absolute paths from project root
- aiogram-dialog requires specific window/getter/handler patterns
- Department selection supports both flat positions and nested subdepartments
- Google integration is optional - bot works without it if env vars missing
- Redis connection is mandatory - implement proper connection error handling
- Photo file_ids must be validated on startup or regenerated if Telegram invalidates them