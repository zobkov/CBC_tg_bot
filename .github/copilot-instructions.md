# CBC Crew Selection Bot AI Assistant Guidelines

## Project Architecture

This is a **Telegram bot for managing recruitment applications** built with aiogram 3.x and aiogram-dialog for complex conversation flows. The bot handles multi-stage application processes for the CBC (Китайско-Большой Конкурс) forum.

### Core Technology Stack
- **Bot Framework**: aiogram 3.x with HTML parse mode
- **Dialog System**: aiogram-dialog for complex conversation flows  
- **State Management**: Redis with FSM storage (TTL: 24 hours)
- **Database**: PostgreSQL with psycopg3 connection pooling
- **Config**: Environment variables + JSON files for business logic
- **External APIs**: Google Sheets API, Google Drive API (optional)

### Key Architecture Patterns

**Dialog-Based Architecture**: Each user interaction flow is a separate dialog in `app/bot/dialogs/` with:
- `dialogs.py` - Window definitions and conversation flow
- `states.py` - FSM state definitions  
- `handlers.py` - Business logic and data processing
- `getters.py` - Data retrieval for dialog context

**Multi-Database Pattern**: 
- `db_applications` - Main application data (PostgreSQL)
- `redis` - Session state and temporary data
- Both pools accessible via `dp["db_applications"]` and Redis storage

**Configuration Hierarchy**:
```
config/
├── config.py          # Environment variables + dataclasses
├── departments.json    # Business data with subdepartments  
├── selection_config.json # Stages, deadlines, form options
└── *.json.example     # Template files
```

## Development Workflows

### Database Changes
1. Create numbered migration in `migrations/` (e.g., `009_description.sql`)
2. Run via `run_applications_migrations.py` 
3. Update corresponding handlers/getters if schema changes

### Adding New Dialog Flows
1. Create state class in `app/bot/states/new_feature.py`
2. Create dialog directory: `app/bot/dialogs/new_feature/`
3. Import and register dialog in `app/bot/bot.py` routers section
4. Follow existing patterns for handlers/getters/dialogs structure

### Configuration Updates
- **Business Logic**: Modify JSON files in `config/` (departments, stages, etc.)
- **Secrets**: Update environment variables, restart bot
- **Photo Assets**: Update `photo_file_ids.json`, run `regenerate_photo_file_ids.py`
- **Task File Assets**: Update `task_file_ids.json`, run `regenerate_task_file_ids.py`
- **Position Mappings**: Update CSV, run `generate_position_file_mapping.py`, clear cache via `clear_mapping_cache()`

## Project-Specific Conventions

### State Management Patterns
- Use `FirstStageSG`, `TaskSG`, etc. state groups for dialog flows
- Edit flows mirror main flows with `edit_` prefix states
- Confirmation patterns: main form → edit menu → field-specific edit → back to confirmation

### Data Flow Pattern
```
User Input → Handler → Database Update → Google Sheets Sync (optional)
```

### Priority System
Applications support 3-priority job selection:
- `department_1/position_1` (highest priority)  
- `department_2/position_2`
- `department_3/position_3`
- Handle subdepartments via `subdepartment_1/2/3` fields

### Position-to-Task File Mapping System
- **Unique Position IDs**: Format `"dept.subdept.position"` (e.g., `"1.0.1"`, `"2.1.4"`)
- **Mapping Files**:
  - `position-file_mapping.csv` - Source CSV with position-to-file mappings
  - `config/position_id_mapping.json` - Static ID mappings for departments/positions
  - `config/position-file_map.json` - Generated mapping from position IDs to task files
- **Update Workflow**: Run `generate_position_file_mapping.py` after CSV changes
- **Usage**: `app/utils/position_mapping.py` provides utilities for ID conversion and file lookup

### File Upload Strategy
1. Save to local `storage/resumes/` with sanitized filenames
2. Optional Google Drive upload if `enable_drive=True`
3. Store both local path and Drive URL in database
4. Use `MediaFileUpload` with resumable uploads for large files

### Solution Upload System
- **File Storage Structure**: `storage/solutions/{department}/{user_id}/`
- **File Naming Pattern**: `{surname}_{username}_{number}_{original_name}.{ext}`
- **UserFilesManager**: Core utility class in `app/utils/user_files_manager.py`
  - Department-based file organization
  - Regex-based file number extraction: `r'_(\d+)_'`
  - Sanitized filename handling with transliteration
  - File count tracking and deletion operations
- **Size Limits**: 100MB maximum per file upload
- **Submission Tracking**: Database fields `task_1_submitted`, `task_2_submitted`, `task_3_submitted`

## Critical Integration Points

### Environment Configuration
Required variables:
```bash
BOT_TOKEN, DB_APPLICATIONS_*, REDIS_*, GOOGLE_* (optional)
```

### Google Services (Optional)
- Service account with Sheets + Drive API access
- Auto-creates missing Drive folders on startup  
- Graceful degradation if Google services unavailable
- Detailed error logging with actionable solutions

### Redis State Storage
- `DefaultKeyBuilder(with_bot_id=True, with_destiny=True)`
- 24-hour TTL for both state and data
- Connection health checks on startup

### Database Connection Pooling
```python
AsyncConnectionPool(min_size=1, max_size=3, open=False)
```

## Testing & Debugging

### Local Development
```bash
python3 main.py  # Runs with .env file
```

### Log Analysis
- Structured logging in `app/logs/`
- Error reports in `error_reports.json`
- Google API errors include diagnostic suggestions

### Photo Asset Management
```bash
python regenerate_photo_file_ids.py  # Updates Telegram file IDs
```

### Task File Asset Management
```bash
python regenerate_task_file_ids.py  # Updates Telegram file IDs for task files
```

## Common Gotchas

- **Dialog Context**: Use `getter` functions to provide data to dialog windows
- **Telegram File IDs**: Expire periodically, regenerate via `startup_photo_check()` and `startup_task_files_check()`
- **Unicode Handling**: Bot handles UTF-8 explicitly for non-UTF locales
- **Window Platform**: Uses `WindowsSelectorEventLoopPolicy()` on Windows
- **State Transitions**: Always validate state changes in handlers before database updates
- **Department Structure**: Handle both main departments and subdepartments in job selection
- **MediaAttachment Objects**: Task files are returned as MediaAttachment objects with file_id from Telegram
- **Callback Timeouts**: Always call `await callback.answer()` immediately in callback handlers to prevent "query is too old" errors
- **File Number Display**: Use regex pattern `r'_(\d+)_'` for extracting file numbers from complex filenames with multiple underscores

## Solution Upload System Implementation

### Core Components
- **UserFilesManager** (`app/utils/user_files_manager.py`):
  - Handles file saving with department-based organization
  - Provides file listing with proper number extraction
  - Manages file deletion operations
  - Uses transliteration for filename sanitization

### Dialog Flow Pattern for Tasks
```
Task Selection → File Upload → File Management → Submission Confirmation
```

### File Organization Strategy
- **Structure**: `storage/solutions/{department}/{user_id}/`
- **Benefits**: Department-first organization for easier admin access
- **Naming**: Includes user metadata for file identification
- **Numbering**: Sequential numbering with regex-based extraction

### Callback Handler Best Practices
- **Immediate Response**: Call `callback.answer()` first to prevent timeouts
- **Error Handling**: Use `callback.message.answer()` for error messages
- **Long Operations**: Perform after initial callback response
- **State Management**: Ensure proper dialog state transitions

When implementing file upload features, always consider timeout prevention and proper file organization patterns.