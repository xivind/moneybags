-- Migration 003: Migrate Supersaver Data
-- This migration converts data from the old standalone supersaver app to the new moneybags supersaver tables
--
-- OLD SCHEMA (supersaver table):
--   - uid (text)
--   - record_time (datetime)
--   - saved (float) - positive = deposit, negative = withdrawal
--   - category (text)
--
-- NEW SCHEMA (moneybags_supersaver_categories + moneybags_supersaver):
--   - Separate category table with unique IDs
--   - Amount stored as positive integer (deposits/savings only)
--   - Date field (not datetime)
--   - UUID-style IDs
--   - Created/updated timestamps
--   - NOTE: Withdrawals are not migrated (supersaver now tracks savings only)

-- Step 1: Create new tables if they don't exist
CREATE TABLE IF NOT EXISTS moneybags_supersaver_categories (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS moneybags_supersaver (
    id VARCHAR(10) PRIMARY KEY,
    category_id VARCHAR(10) NOT NULL,
    amount INT NOT NULL,
    date DATE NOT NULL,
    comment TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (category_id) REFERENCES moneybags_supersaver_categories(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_category_date (category_id, date),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 2: Extract unique categories from old supersaver table and insert into new categories table
-- Generate IDs using MySQL equivalent of utils.generate_uid() (6 hex chars + 4 timestamp digits)
INSERT INTO moneybags_supersaver_categories (id, name, created_at, updated_at)
SELECT
    LOWER(CONCAT(
        SUBSTR(MD5(CONCAT(category, RAND())), 1, 6),
        LPAD(UNIX_TIMESTAMP() % 10000, 4, '0')
    )) as id,
    category as name,
    NOW() as created_at,
    NOW() as updated_at
FROM (
    SELECT DISTINCT category
    FROM supersaver
    WHERE category IS NOT NULL AND category != ''
) AS unique_categories
ON DUPLICATE KEY UPDATE name = name;  -- Skip if category already exists

-- Step 3: Migrate transaction data from old supersaver to new moneybags_supersaver
-- Convert:
--   - saved > 0 → amount=ROUND(saved) (deposits only, skip withdrawals)
--   - record_time → date (DATE)
--   - category name → category_id (lookup from categories table)
-- NOTE: Only migrating deposits (positive values). Withdrawals are ignored.
INSERT IGNORE INTO moneybags_supersaver (id, category_id, amount, date, comment, created_at, updated_at)
SELECT
    s.uid as id,
    c.id as category_id,
    ROUND(s.saved) as amount,
    DATE(s.record_time) as date,
    NULL as comment,  -- Old schema didn't have comments
    s.record_time as created_at,
    s.record_time as updated_at
FROM supersaver s
INNER JOIN moneybags_supersaver_categories c ON c.name = s.category
WHERE s.saved IS NOT NULL AND s.saved > 0;  -- Only migrate deposits

-- Step 4: Verify migration
-- Show summary of migrated data
SELECT
    'Categories migrated:' as summary,
    COUNT(*) as count
FROM moneybags_supersaver_categories
UNION ALL
SELECT
    'Savings entries migrated:' as summary,
    COUNT(*) as count
FROM moneybags_supersaver
UNION ALL
SELECT
    'Total savings amount:' as summary,
    COALESCE(SUM(amount), 0) as count
FROM moneybags_supersaver;

-- NOTE: After verifying the migration is successful, you can optionally:
-- 1. Rename old table: RENAME TABLE supersaver TO supersaver_backup;
-- 2. Or drop old table: DROP TABLE supersaver;
--
-- DO NOT DO THIS UNTIL YOU'VE VERIFIED THE MIGRATION IS CORRECT!
