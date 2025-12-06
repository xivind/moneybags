# Instructions for Claude Code to build the moneybags web application

This file contains instructions for Claude Code to guide the development and maintenance of the Moneybags web application.

## Purpose of the Moneybags web application

The purpose of the Moneybags web application is to help users have control of their personal economy. The program lets users create yearly budgets (both for income and expenses), and then lets users register actual income and expenses as time passes by. Users can attach comments to each value entered.

The application has four main parts:
1. **Dashboard** - Visually appealing dashboard with interesting information
2. **Budget & Actuals** - Yearly budget (income and expenses) and yearly actual income and expenses (budget and actual in the same view)
3. **Analysis** - Deep dive into data, query different things, and drill down
4. **Configuration** - User preferences (Currency notation, database connection settings, category/payee management, budget templates by year)

The program takes into account that each year has some of the same posts (which need to be seen in relation to each other), but new posts may also exist that have not been used in previous years. Posts that were used at some time may no longer be used in future years. Ensuring data integrity and the ability to analyze and see data across years is paramount.

**UX is critical**: The application uses htmx so saving and reloading happens automatically, without the user being redirected to the top of the page or losing context.

## Production Status

**Current Status:** Production-ready ✅

The core application is fully implemented, tested (34 passing tests), and ready for production deployment. Dashboard and Analysis pages are intentionally placeholders, pending production data to inform their design.

**What's implemented:**
- ✅ Complete Budget & Actuals interface (htmx auto-save, transaction tracking)
- ✅ Configuration management (categories, payees, currency, budget templates)
- ✅ Dynamic currency support (NOK/USD/EUR) - symbol before amount with space
- ✅ Form validation at all layers (client, server, database)
- ✅ Error handling with user-friendly toast notifications
- ✅ Connection pooling, transaction management, retry logic
- ✅ Docker deployment with volume persistence
- ✅ CSV export functionality
- ✅ Clean architecture with zero inline styles/scripts

**What's placeholder (awaiting production data):**
- 🔲 Dashboard page with charts and visualizations
- 🔲 Analysis page with deep-dive views

## Tech Stack

### Backend
- **FastAPI** - Web framework for API routes
- **uvicorn** - ASGI server to run FastAPI
- **PeeWee ORM** - Database ORM for MariaDB
- **pymysql** - Database driver for MySQL/MariaDB (required by PeeWee)
- **playhouse.pool** - Connection pooling (part of PeeWee, provides PooledMySQLDatabase)
- **MariaDB** - Database running in separate Docker container or separate host

### Frontend
- **Bootstrap** - Responsive design framework (works on mobile and desktop)
- **htmx** - Automatic saving/reloading without page redirects
- **Vanilla JavaScript** - All JS in single file (static/js/app.js)
- **TomSelect** - Advanced input boxes for select elements
- **Tempus Dominus** - Date and time picker
- **Chart.js** - Visualizations for dashboard

### CSS
- All CSS in single file (static/css/custom.css)
- No inline styles in HTML templates

## Architectural Constraints

### General Constraints
- **main.py** - Contains router ONLY, no business logic
- **business_logic.py** - All business logic, calculations, validation. Calls database_manager.py for CRUD operations. NEVER calls database directly.
- **database_manager.py** - All CRUD operations, connection management, transaction handling
- **database_model.py** - Pure data models (NO LOGIC, NO backrefs, NO defaults)
- **utils.py** - Helper methods (UUID generation, date validation, NULL conversion)
- **uvicorn_log_config.ini** - Logging configuration (uniform logging for FastAPI and Python)

### Database Architecture (from DATABASE_DESIGN.md)

**Connection Management:**
- Uses `PooledMySQLDatabase` for connection pooling (htmx performance)
- Pool size configurable (default: 10 connections)
- Connection recycling (default: 3600 seconds)
- Health checks and automatic reconnection
- Retry logic for transient failures (3 retries, 1s delay)

**Transaction Management:**
- All write operations wrapped with `@with_transaction` decorator
- Ensures atomicity (all or nothing)
- Automatic rollback on errors
- Explicit commit on success

**Performance Features:**
- Configuration caching (5-minute timeout, in-memory)
- Query timing metrics (logs slow queries > 1 second)
- Connection resilience (health checks, reconnection)

**Data Principles:**
- UUIDs generated in business_logic.py via `utils.generate_uid()`
- Timestamps set in business_logic.py (YYYY-MM-DD HH:MM:SS format)
- Empty strings converted to NULL via `utils.empty_to_none()`
- All currency amounts stored as integers (no decimals)
- Foreign keys use explicit `_id` suffix (category_id, payee_id)

### Frontend Organization
- **ALL JavaScript** must be in `/static/js/app.js` - NO inline scripts in HTML templates
- **ALL CSS** must be in `/static/css/custom.css` - NO inline styles in HTML templates
- HTML templates should only contain structure and template logic (Jinja2)
- This keeps the codebase maintainable and makes it easy to find and modify styles or behavior

### Database Configuration
- Database configuration kept simple: no backrefs, no automatically generated IDs
- Always create unique IDs in backend and submit to database
- Connection settings stored in `db_config.json` file (persisted via Docker volume mount)
- Configuration caching in business_logic.py reduces database queries

## Development Setup

### Virtual Environment
- **IMPORTANT**: Virtual environment is in `/home/xivind/code/moneybags-runtime/` (separate from repo)
- This follows the pattern from gas-gauge and gear-calc projects
- Never create venv inside the repo directory

**Setup:**
```bash
# Create venv (if needed)
python3 -m venv /home/xivind/code/moneybags-runtime

# Activate venv
source /home/xivind/code/moneybags-runtime/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Connection (db_config.json)

**First-time setup:**
1. Start the application: `uvicorn main:app --host 0.0.0.0 --port 8000 --log-config uvicorn_log_config.ini --reload`
2. Open browser to http://localhost:8000
3. You'll see a banner prompting you to configure the database
4. Click "Go to Configuration" and enter your database connection details:
   - Database Host (e.g., `sandbox` or IP address)
   - Port (default: `3306`)
   - Database Name (e.g., `MASTERDB`)
   - Username and Password
   - Connection Pool Size (default: `10`)
5. Click "Save Settings" and restart the application

The configuration is saved to `db_config.json` (excluded from Git in `.gitignore`):
```json
{
  "db_host": "sandbox",
  "db_port": 3306,
  "db_name": "MASTERDB",
  "db_user": "root",
  "db_password": "devpassword",
  "db_pool_size": 10
}
```

**Important**: The `db_config.json` file is excluded from Git (in `.gitignore`) and Docker (in `.dockerignore`).

### Running Locally

```bash
# 1. Activate venv
source /home/xivind/code/moneybags-runtime/bin/activate

# 2. Go to project directory
cd /home/xivind/code/moneybags

# 3. Run with uvicorn (recommended for development)
uvicorn main:app --host 0.0.0.0 --port 8000 --log-config uvicorn_log_config.ini --reload

# The --reload flag auto-restarts on code changes (useful for development)
```

**On first run**, the application automatically:
1. Connects to MariaDB
2. Creates all 6 tables if they don't exist
3. Seeds initial data if database is empty (categories, payees, config, budget template for current year)

### Docker Deployment

**IMPORTANT: Database configuration file is required BEFORE running the container.**

**Setup:**

1. **Create database configuration file:**
   ```bash
   mkdir -p ~/code/container_data/moneybags
   ```

   Create `~/code/container_data/moneybags/db_config.json` with your MariaDB connection settings:
   ```json
   {
     "db_host": "your-mariadb-host",
     "db_port": 3306,
     "db_name": "MASTERDB",
     "db_user": "your-username",
     "db_password": "your-password",
     "db_pool_size": 10
   }
   ```

   **This file MUST exist before running the container**, or the container will fail to start.

2. **Run deployment script:**
   ```bash
   ./create-container-moneybags.sh
   ```

3. **Access the application:**
   - Open browser to http://localhost:8003
   - Application will automatically connect to MariaDB using settings from `db_config.json`

**What the script does:**
1. Stops and removes old container/image
2. Builds fresh Docker image
3. Creates data directories (~/code/container_data/moneybags)
4. Runs container with:
   - Volume mount for `db_config.json` (persists database configuration)
   - Volume mount for data persistence
   - Port 8003→8000 mapping (access at http://localhost:8003)
   - Auto-restart policy
   - Europe/Stockholm timezone

**Database Configuration in Container:**
- Container mounts `db_config.json` from host: `~/code/container_data/moneybags/db_config.json`
- File MUST be manually created before first container run
- Settings persist across container rebuilds via volume mount
- Can be updated via Configuration page in the UI (requires restart)
- No environment variables needed for database connection

## Database Migrations

Located in `/migrations/` directory:

- **001_initial_schema.sql** - Reference SQL schema (PeeWee auto-creates tables, but this is useful for manual setup or documentation)
- **migrate.py** - Python migration runner for applying schema changes
- **README.md** - Migration documentation

**When to use migrations:**
- Schema changes (adding columns, indexes) after initial deployment
- Data transformations
- Manual database setup without running the app

**Run migration:**
```bash
python migrations/migrate.py 001_initial_schema.sql
```

## API Structure

All API routes in `main.py` follow this pattern:

**Budget API (7 endpoints):**
- GET `/api/budget/{year}` - Get complete budget data
- POST `/api/budget/entry` - Save budget entry
- GET `/api/transactions/{category_id}/{year}/{month}` - Get transactions
- POST `/api/transaction` - Create transaction
- PUT `/api/transaction/{transaction_id}` - Update transaction
- DELETE `/api/transaction/{transaction_id}` - Delete transaction

**Category API (4 endpoints):**
- GET `/api/categories` - Get all categories
- POST `/api/category` - Create category
- PUT `/api/category/{category_id}` - Update category
- DELETE `/api/category/{category_id}` - Delete category

**Payee API (4 endpoints):**
- GET `/api/payees` - Get all payees
- POST `/api/payee` - Create payee
- PUT `/api/payee/{payee_id}` - Update payee
- DELETE `/api/payee/{payee_id}` - Delete payee

**Budget Template API (5 endpoints):**
- GET `/api/budget-template/{year}` - Get template for year
- POST `/api/budget-template` - Add category to year template
- DELETE `/api/budget-template/{year}/{category_id}` - Remove category from year
- POST `/api/budget-template/copy` - Copy template from one year to another
- GET `/api/years` - Get all years with budget templates

**Configuration API (5 endpoints):**

*Currency settings (stored in MariaDB):*
- GET `/api/config/currency` - Get currency configuration settings from MariaDB (future feature)
- PUT `/api/config/currency` - Update currency configuration settings (future feature)

*Database connection settings (stored in db_config.json):*
- GET `/api/config/db-connection` - Get database connection settings from db_config.json (password excluded for security)
- POST `/api/config/test-db-connection` - Test database connection with provided settings
- POST `/api/config/save-db-connection` - Save database connection to db_config.json

**Note:** Configuration is split into two storage locations:
- Application settings (currency format, etc.) → MariaDB Configuration table
- Database connection settings (host, port, credentials, etc.) → db_config.json file

**Response Format:**
All API endpoints return JSON in format:
```json
{
  "success": true,
  "data": { ... }
}
```

Or on error:
```json
{
  "success": false,
  "error": "Error message"
}
```

## Key Implementation Details

### Connection Pooling
- Uses `PooledMySQLDatabase` (from playhouse.pool)
- Initialized in `database_manager.initialize_connection()`
- Configurable pool_size and stale_timeout

### Transaction Wrapping
- All write operations (create, update, delete) use `@with_transaction` decorator
- Defined in `database_manager.py`
- Ensures atomicity and automatic rollback

### Configuration Caching
- Implemented in `business_logic.py`
- 5-minute cache timeout
- Reduces database queries for config lookups
- Cache invalidated on config updates

### Query Performance
- Optional query timing with `@log_query_time` decorator
- Logs slow queries (> 1 second threshold)
- Can be disabled in production via `ENABLE_QUERY_METRICS = False`

### Error Handling
- All business logic functions raise `ValueError` with descriptive messages
- API routes catch exceptions and return appropriate HTTP status codes:
  - 400 for validation errors
  - 500 for server errors
- All errors logged with context

## Important Files

- **DATABASE_DESIGN.md** - Complete database schema documentation
- **BACKEND_IMPLEMENTATION.md** - Backend implementation blueprint (Phases 1-5)
- **requirements.txt** - Python dependencies
- **db_config.json** - Database connection settings (not in Git, contains credentials)
- **.gitignore** - Excludes db_config.json, venv files, data directories
- **.dockerignore** - Excludes db_config.json, tests, migrations, markdown files
- **Dockerfile** - Container image definition
- **create-container-moneybags.sh** - Deployment script
- **migrations/** - Database migration scripts

## Testing

Run tests with:
```bash
pytest tests/ -v
```

## Notes for Future Development

### Production-Ready Application (December 2025)
The application is production-ready with 34 passing tests. Core features fully implemented. Dashboard and Analysis are intentional placeholders pending production data.

### Critical Architecture Rules (NEVER violate these)
1. **NO inline styles** - All CSS in `static/css/custom.css` only
2. **NO inline scripts** - All JavaScript in `static/js/app.js` only
3. **Follow clean architecture** - main.py → business_logic.py → database_manager.py → models → database
4. **Never commit db_config.json** - Contains database credentials

### Currency Format (Production Standard)
- Symbol BEFORE amount with space: `kr 1,234` | `$ 1,234` | `€ 1,234`
- Number locale: `en-US` (comma thousands separator)
- Dynamic currency via config: NOK, USD, EUR
- Form labels update automatically when currency changes

### Database & Performance
5. **PeeWee auto-creates tables** - Migrations only for schema changes
6. **pymysql is required** - PeeWee needs this driver for MariaDB
7. **Database config via JSON file** - db_config.json persisted via Docker volume mount
8. **Connection pooling is critical** - For htmx performance requirements
9. **Configuration is cached** - 5-minute timeout to reduce DB queries
10. **Transaction wrapping** - All writes use @with_transaction decorator

### Development Environment
11. **Use venv from moneybags-runtime** - Not inside repo
12. **First-run experience** - Banner on dashboard prompts user to configure database
13. **Testing required** - Run `pytest tests/ -v` before commits
