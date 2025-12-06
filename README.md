# Moneybags

Self-hosted web application for personal budget planning and expense tracking.

## Overview

Moneybags helps you take control of your personal finances by allowing you to:
- Create yearly budgets for income and expenses
- Track actual income and expenses as they occur
- Compare budget vs. actuals with visual dashboards
- Analyze spending patterns across years
- Manage categories, payees, and budget templates

## Production Status

**Status:** Production-ready ✅

The core application is fully implemented and tested with 34 passing tests. Dashboard and Analysis pages are intentionally placeholders, pending production data to inform their design.

**Implemented features:**
- ✅ Complete Budget & Actuals interface with htmx auto-save
- ✅ Category and Payee management (CRUD operations)
- ✅ Budget template management by year
- ✅ Transaction tracking with date, amount, payee, and comments
- ✅ Dynamic currency support (NOK, USD, EUR) - symbol before amount with space
- ✅ CSV export functionality
- ✅ Comprehensive form validation (client + server + database)
- ✅ Error handling with toast notifications
- ✅ Connection pooling and transaction management
- ✅ Docker deployment with volume persistence

**Planned features:**
- 🔲 Dashboard with charts and key metrics (awaiting production data)
- 🔲 Analysis page with multiple views (awaiting production data)

## Features

- **Budget & Actuals** - Side-by-side budget planning and actual tracking with automatic save
- **Configuration** - Manage categories, payees, currency settings, and budget templates
- **Dynamic Currency** - Choose between NOK, USD, or EUR with proper formatting
- **Dashboard** _(placeholder)_ - Visual overview with charts and key metrics
- **Analysis** _(placeholder)_ - Deep dive into spending patterns with multiple views

## Tech Stack

- **Backend:** FastAPI + PeeWee ORM + MariaDB
- **Frontend:** Bootstrap + htmx + Chart.js + TomSelect
- **Deployment:** Docker container

## Quick Start

### Local Development

1. **Create virtual environment** (in separate directory):
   ```bash
   python3 -m venv /home/xivind/code/moneybags-runtime
   source /home/xivind/code/moneybags-runtime/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   cd /home/xivind/code/moneybags
   pip install -r requirements.txt
   ```

3. **Start the application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8009 --log-config uvicorn_log_config.ini --reload
   ```

4. **Configure database:**
   - Open browser to http://localhost:8009
   - You'll see a banner prompting you to configure the database
   - Click "Go to Configuration"
   - Scroll to "Database Connection" section
   - Enter your MariaDB connection details
   - Click "Save Settings"
   - Restart the application

   This creates `moneybags_db_config.json` in the project directory:
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

### Docker Deployment

1. **Create database configuration file:**
   ```bash
   mkdir -p ~/code/container_data
   ```

   Create `~/code/container_data/moneybags_db_config.json` with your database settings:
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

   **Important:** This file MUST exist before running the container.

2. **Deploy container:**
   ```bash
   ./create-container-moneybags.sh
   ```

3. **Access the application:**
   - Open browser to http://localhost:8009
   - Application will automatically connect to MariaDB using settings from `moneybags_db_config.json`

## Database Requirements

Moneybags requires a MariaDB database. The application will automatically:
- Create all required tables on first run
- Seed initial data (categories, payees, configuration)
- Set up budget templates for the current year

## Configuration

### Database Connection
- Stored in `moneybags_db_config.json` (not tracked in Git)
- Docker: Persisted via volume mount at `~/code/container_data/moneybags_db_config.json`
- Can be updated via Configuration page in the UI

### Application Settings
- Currency format (NOK, USD, EUR)
- Categories (income and expense types)
- Payees (transaction partners)
- Budget templates by year

## Project Structure

```
moneybags/
├── main.py                    # FastAPI routes
├── business_logic.py          # Business logic and validation
├── database_manager.py        # Database CRUD operations
├── database_model.py          # PeeWee ORM models
├── utils.py                   # Helper functions
├── static/
│   ├── js/app.js             # Frontend JavaScript (single file)
│   └── css/custom.css        # Custom styles (single file)
├── templates/                 # Jinja2 HTML templates
├── migrations/                # Database migration scripts
└── tests/                     # Test suite
```

## Development Notes

- Virtual environment: `/home/xivind/code/moneybags-runtime/` (separate from repo)
- All JavaScript in one file: `static/js/app.js` (no inline scripts)
- All CSS in one file: `static/css/custom.css` (no inline styles)
- Clean architecture: main.py → business_logic.py → database_manager.py → models
- Database credentials stored in `moneybags_db_config.json` (excluded from Git)
- Currency format: Symbol before amount with space (kr 1 234 | $ 1 234 | € 1 234)
- Number format: Space as thousand separator
- Production-ready with 34 passing tests

## Testing

```bash
pytest tests/ -v
```

## Documentation

- **CLAUDE.md** - Comprehensive development guide for AI assistance
- **DATABASE_DESIGN.md** - Complete database schema documentation
- **BACKEND_IMPLEMENTATION.md** - Backend implementation blueprint

## License

Personal project for budget management.
