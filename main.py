"""
Main application file for Moneybags.
All routes consolidated here - no separate router files.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import business_logic

# Setup logging
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(title="Moneybags")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Moneybags application...")
    try:
        business_logic.initialize_database()
        if business_logic.DATABASE_CONFIGURED:
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database not configured - user needs to configure database connection")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't raise - allow app to start so user can configure database
    logger.info("Moneybags application started")

# ==================== HTML VIEWS ====================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Dashboard showing financial overview"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "database_configured": business_logic.DATABASE_CONFIGURED
    })

@app.get("/budget", response_class=HTMLResponse)
def budget_page(request: Request):
    """Budget and actuals page"""
    return templates.TemplateResponse("budget.html", {
        "request": request
    })

@app.get("/analysis", response_class=HTMLResponse)
def analysis_page(request: Request):
    """Analysis page with charts and deep dives"""
    return templates.TemplateResponse("analysis.html", {
        "request": request
    })

@app.get("/config", response_class=HTMLResponse)
def config_page(request: Request):
    """Configuration page for user preferences"""
    return templates.TemplateResponse("config.html", {
        "request": request,
        "database_configured": business_logic.DATABASE_CONFIGURED
    })

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker and monitoring.

    Tests actual database connectivity by executing a simple query.
    Returns 200 if healthy, 503 if database is unreachable.
    """
    try:
        # Check if database is configured
        if not business_logic.DATABASE_CONFIGURED:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "reason": "Database not configured"
                }
            )

        # Test database connection with simple query
        import database_manager as db
        is_connected = db.check_connection()

        if is_connected:
            return {
                "status": "healthy",
                "database": "connected"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "reason": "Database connection lost"
                }
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "reason": "Health check error"
            }
        )

# ==================== BUDGET API ROUTES ====================

@app.get("/api/budget/{year}")
async def get_budget_data(year: int):
    """
    Get complete budget data for a year.

    Returns:
    {
        "year": 2025,
        "categories": [...],  # Categories active in this year's template
        "budget_entries": {...},  # All budget entries for the year
        "transactions": {...}  # All transactions for the year
    }
    """
    try:
        data = business_logic.get_budget_data_for_year(year)
        return {"success": True, "data": data}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error getting budget data for year {year}: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/budget/entry")
async def save_budget_entry(request: Request):
    """
    Create or update budget entry.

    Request body:
    {
        "category_id": "abc123",
        "year": 2025,
        "month": 1,
        "amount": 53000
    }
    """
    try:
        data = await request.json()
        result = business_logic.save_budget_entry(
            category_id=data["category_id"],
            year=data["year"],
            month=data["month"],
            amount=data["amount"]
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error saving budget entry: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.delete("/api/budget/entry/{entry_id}")
async def delete_budget_entry(entry_id: str):
    """Delete budget entry."""
    try:
        business_logic.delete_budget_entry(entry_id)
        return {"success": True}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error deleting budget entry: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/transactions/{category_id}/{year}/{month}")
async def get_transactions(category_id: str, year: int, month: int):
    """Get all transactions for category/year/month."""
    try:
        transactions = business_logic.get_transactions(category_id, year, month)
        return {"success": True, "data": transactions}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/transaction")
async def create_transaction(request: Request):
    """
    Create new transaction.

    Request body:
    {
        "category_id": "abc123",
        "date": "2025-01-15",
        "amount": 55920,
        "payee_id": "def456",  # optional
        "comment": "Salary January"  # optional
    }
    """
    try:
        data = await request.json()
        result = business_logic.create_transaction(
            category_id=data["category_id"],
            date=data["date"],
            amount=data["amount"],
            payee_id=data.get("payee_id"),
            comment=data.get("comment")
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.put("/api/transaction/{transaction_id}")
async def update_transaction(transaction_id: str, request: Request):
    """Update existing transaction."""
    try:
        data = await request.json()
        result = business_logic.update_transaction(
            transaction_id=transaction_id,
            date=data["date"],
            amount=data["amount"],
            payee_id=data.get("payee_id"),
            comment=data.get("comment")
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.delete("/api/transaction/{transaction_id}")
async def delete_transaction(transaction_id: str):
    """Delete transaction."""
    try:
        business_logic.delete_transaction(transaction_id)
        return {"success": True}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ==================== CATEGORY API ROUTES ====================

@app.get("/api/categories")
async def get_categories():
    """Get all categories."""
    try:
        categories = business_logic.get_all_categories()
        return {"success": True, "data": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/category")
async def create_category(request: Request):
    """
    Create new category.

    Request body:
    {
        "name": "New Category",
        "type": "income"  # or "expenses"
    }
    """
    try:
        data = await request.json()
        result = business_logic.create_category(
            name=data["name"],
            type=data["type"]
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.put("/api/category/{category_id}")
async def update_category(category_id: str, request: Request):
    """Update category (rename only - type cannot change if data exists)."""
    try:
        data = await request.json()
        result = business_logic.update_category(
            category_id=category_id,
            name=data["name"]
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.delete("/api/category/{category_id}")
async def delete_category(category_id: str):
    """Delete category (only if not in use)."""
    try:
        business_logic.delete_category(category_id)
        return {"success": True}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ==================== PAYEE API ROUTES ====================

@app.get("/api/payees")
async def get_payees():
    """Get all payees."""
    try:
        payees = business_logic.get_all_payees()
        return {"success": True, "data": payees}
    except Exception as e:
        logger.error(f"Error getting payees: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/payee")
async def create_payee(request: Request):
    """
    Create new payee.

    Request body:
    {
        "name": "Netflix",
        "type": "Actual"  # or "Generic"
    }
    """
    try:
        data = await request.json()
        result = business_logic.create_payee(
            name=data["name"],
            type=data.get("type", "Actual")
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error creating payee: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.put("/api/payee/{payee_id}")
async def update_payee(payee_id: str, request: Request):
    """Update payee (renames all transaction references)."""
    try:
        data = await request.json()
        result = business_logic.update_payee(
            payee_id=payee_id,
            name=data["name"],
            type=data.get("type")
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error updating payee: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.delete("/api/payee/{payee_id}")
async def delete_payee(payee_id: str):
    """Delete payee (only if not in use)."""
    try:
        business_logic.delete_payee(payee_id)
        return {"success": True}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error deleting payee: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ==================== BUDGET TEMPLATE API ROUTES ====================

@app.get("/api/budget-template/{year}")
async def get_budget_template(year: int):
    """Get categories active in year's budget template."""
    try:
        categories = business_logic.get_budget_template(year)
        return {"success": True, "data": categories}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error getting budget template: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/budget-template")
async def add_category_to_template(request: Request):
    """
    Add category to year's budget template.

    Request body:
    {
        "year": 2025,
        "category_id": "abc123"
    }
    """
    try:
        data = await request.json()
        result = business_logic.add_category_to_template(
            year=data["year"],
            category_id=data["category_id"]
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error adding category to template: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.delete("/api/budget-template/{year}/{category_id}")
async def remove_category_from_template(year: int, category_id: str):
    """Remove category from year's template (only if no data exists)."""
    try:
        business_logic.remove_category_from_template(year, category_id)
        return {"success": True}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error removing category from template: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/budget-template/copy")
async def copy_budget_template(request: Request):
    """
    Copy budget template from one year to another.

    Request body:
    {
        "from_year": 2024,
        "to_year": 2025
    }
    """
    try:
        data = await request.json()
        result = business_logic.copy_budget_template(
            from_year=data["from_year"],
            to_year=data["to_year"]
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error copying budget template: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/years")
async def get_available_years():
    """Get all years that have budget templates."""
    try:
        years = business_logic.get_available_years()
        return {"success": True, "data": years}
    except Exception as e:
        logger.error(f"Error getting available years: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ==================== CONFIGURATION API ROUTES ====================

@app.get("/api/config/currency")
async def get_currency_configuration():
    """
    Get currency configuration settings.

    Returns currency_format and other app configuration from MariaDB Configuration table.
    Note: Database connection settings are in /api/config/db-connection endpoint.
    """
    try:
        config = business_logic.get_all_configuration()
        return {"success": True, "data": config}
    except Exception as e:
        logger.error(f"Error getting currency configuration: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.put("/api/config/currency")
async def update_currency_configuration(request: Request):
    """
    Update currency configuration settings.

    Request body:
    {
        "currency_format": "nok"
    }

    Valid values: "nok", "usd", "eur"

    Note: Database connection settings should use /api/config/save-db-connection endpoint.
    """
    try:
        data = await request.json()
        result = business_logic.update_configuration(data)
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error updating currency configuration: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/config/test-db-connection")
async def test_db_connection(request: Request):
    """Test database connection with provided settings."""
    try:
        data = await request.json()
        result = business_logic.test_database_connection(
            host=data["host"],
            port=data["port"],
            database=data["database"],
            user=data["user"],
            password=data["password"]
        )
        # Return result directly (it already has 'success' and 'message' fields)
        return result
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/config/db-connection")
async def get_db_connection():
    """
    Get current database connection settings from moneybags_db_config.json.

    Note: Password is not returned for security reasons.
    """
    try:
        config = business_logic.load_database_config()

        if config is None:
            return {
                "success": True,
                "data": {
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_name": "",
                    "db_user": "",
                    "db_pool_size": 10
                }
            }

        # Return config without password for security
        return {
            "success": True,
            "data": {
                "db_host": config.get("db_host", "localhost"),
                "db_port": config.get("db_port", 3306),
                "db_name": config.get("db_name", ""),
                "db_user": config.get("db_user", ""),
                "db_pool_size": config.get("db_pool_size", 10)
            }
        }
    except Exception as e:
        logger.error(f"Error loading database connection settings: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/config/save-db-connection")
async def save_db_connection(request: Request):
    """
    Save database connection settings to moneybags_db_config.json file.

    Request body:
    {
        "db_host": "localhost",
        "db_port": 3306,
        "db_name": "MASTERDB",
        "db_user": "root",
        "db_password": "password",
        "db_pool_size": 10
    }
    """
    try:
        data = await request.json()

        # Validate required fields
        required_fields = ["db_host", "db_port", "db_name", "db_user", "db_password"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Prepare config dict
        config = {
            "db_host": data["db_host"],
            "db_port": int(data["db_port"]),
            "db_name": data["db_name"],
            "db_user": data["db_user"],
            "db_password": data["db_password"],
            "db_pool_size": int(data.get("db_pool_size", 10))
        }

        # Save to file
        business_logic.save_database_config(config)

        return {
            "success": True,
            "message": "Database configuration saved successfully. Please restart the application for changes to take effect."
        }
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error saving database configuration: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8009,
        log_config="uvicorn_log_config.ini"
    )
