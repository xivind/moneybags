# Database Migrations for Moneybags

This directory contains database migration scripts for the Moneybags application.

## Overview

Moneybags uses **PeeWee ORM** which automatically creates tables. However, this directory provides:
1. Reference SQL schema for manual database setup
2. Migration scripts for schema changes
3. Documentation of database evolution

## Initial Setup

The application automatically creates tables on first run via `database_manager.create_tables_if_not_exist()`.

For manual setup or external tools, use:
```bash
mysql -u root -p < migrations/001_initial_schema.sql
```

## Migration Strategy

Since PeeWee handles schema creation automatically, migrations are primarily for:
1. **Data migrations** - Transforming existing data
2. **Manual deployments** - When PeeWee auto-creation is disabled
3. **Documentation** - Recording schema changes over time

## Future Migrations

To create a new migration:

1. Create file: `migrations/00X_description.sql` (X = next number)
2. Document the change and reason
3. Test on development database first
4. Apply to production during maintenance window

Example:
```sql
-- migrations/002_add_currency_column.sql
-- Add currency column to transactions table for multi-currency support

ALTER TABLE transactions ADD COLUMN currency VARCHAR(3) DEFAULT 'NOK';
UPDATE transactions SET currency = 'NOK' WHERE currency IS NULL;
```

## Rollback Strategy

Always:
1. Backup database before migrations
2. Test migrations on development copy
3. Have rollback SQL ready
4. Document rollback steps

## Notes

- PeeWee's `create_tables(safe=True)` only creates missing tables
- Schema changes require manual migrations or model updates
- Use `pymysql` or `mysql` CLI for applying migrations
- Version control all migration files
