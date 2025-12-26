#!/usr/bin/env python3
"""
Simple database migration runner for Moneybags.

Usage:
    python migrations/migrate.py [migration_file]

If no migration file specified, lists available migrations.
"""

import sys
import os
import json
from pathlib import Path

try:
    import pymysql
except ImportError:
    print("Error: pymysql not installed. Run: pip install pymysql")
    sys.exit(1)


def get_db_config():
    """Get database configuration from moneybags_db_config.json."""
    config_file = Path(__file__).parent.parent / 'moneybags_db_config.json'

    if not config_file.exists():
        print(f"Error: Database configuration file not found: {config_file}")
        print("\nPlease create moneybags_db_config.json with your database settings:")
        print('''{
  "db_host": "localhost",
  "db_port": 3306,
  "db_name": "MASTERDB",
  "db_user": "root",
  "db_password": "your_password",
  "db_pool_size": 10
}''')
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    return {
        'host': config['db_host'],
        'port': config['db_port'],
        'database': config['db_name'],
        'user': config['db_user'],
        'password': config['db_password'],
        'charset': 'utf8mb4'
    }


def list_migrations():
    """List available migration files."""
    migrations_dir = Path(__file__).parent
    sql_files = sorted(migrations_dir.glob('*.sql'))

    if not sql_files:
        print("No migration files found.")
        return

    print("\nAvailable migrations:")
    print("-" * 50)
    for sql_file in sql_files:
        print(f"  {sql_file.name}")
    print("-" * 50)
    print(f"\nTotal: {len(sql_files)} migration(s)")


def run_migration(migration_file):
    """Run specified migration file."""
    migration_path = Path(__file__).parent / migration_file

    if not migration_path.exists():
        print(f"Error: Migration file not found: {migration_file}")
        return False

    print(f"\nRunning migration: {migration_file}")
    print("-" * 50)

    # Read SQL file
    with open(migration_path, 'r') as f:
        sql = f.read()

    # Connect to database
    try:
        config = get_db_config()
        print(f"Connecting to {config['host']}:{config['port']}/{config['database']}...")

        connection = pymysql.connect(**config)
        cursor = connection.cursor()

        # Execute SQL (split by semicolons for multiple statements)
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"Executing statement {i}/{len(statements)}...")
                cursor.execute(statement)

        connection.commit()
        print(f"\n✓ Migration completed successfully!")
        print(f"  Executed {len(statements)} SQL statement(s)")

        cursor.close()
        connection.close()
        return True

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 50)
    print("Moneybags Database Migration Runner")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nUsage: python migrate.py [migration_file.sql]")
        list_migrations()
        print("\nExample:")
        print("  python migrations/migrate.py 001_initial_schema.sql")
        return

    migration_file = sys.argv[1]
    success = run_migration(migration_file)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
