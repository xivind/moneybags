-- Initial Moneybags Database Schema
-- Generated from DATABASE_DESIGN.md
-- This SQL is for reference - PeeWee ORM creates these tables automatically

-- Create database (if needed)
CREATE DATABASE IF NOT EXISTS moneybags CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE moneybags;

-- Categories: Income and expense categories
CREATE TABLE IF NOT EXISTS moneybags_categories (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(10) NOT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY unique_category_name (name),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payees: Transaction payees
CREATE TABLE IF NOT EXISTS moneybags_payees (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(10) NOT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY unique_payee_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Budget Templates: Defines which categories are active for each year
CREATE TABLE IF NOT EXISTS moneybags_budget_templates (
    id VARCHAR(10) PRIMARY KEY,
    year INT NOT NULL,
    category_id VARCHAR(10) NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_year (year),
    INDEX idx_category_id (category_id),
    FOREIGN KEY (category_id) REFERENCES moneybags_categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Budget Entries: Budget amounts for each category/year/month
CREATE TABLE IF NOT EXISTS moneybags_budget_entries (
    id VARCHAR(10) PRIMARY KEY,
    category_id VARCHAR(10) NOT NULL,
    year INT NOT NULL,
    month TINYINT NOT NULL,
    amount INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_category_year_month (category_id, year, month),
    FOREIGN KEY (category_id) REFERENCES moneybags_categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Transactions: Actual income and expense transactions
CREATE TABLE IF NOT EXISTS moneybags_transactions (
    id VARCHAR(10) PRIMARY KEY,
    category_id VARCHAR(10) NOT NULL,
    payee_id VARCHAR(10) NULL,
    date DATE NOT NULL,
    amount INT NOT NULL,
    comment TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_category_id (category_id),
    INDEX idx_payee_id (payee_id),
    INDEX idx_date (date),
    FOREIGN KEY (category_id) REFERENCES moneybags_categories(id),
    FOREIGN KEY (payee_id) REFERENCES moneybags_payees(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Configuration: Application settings
CREATE TABLE IF NOT EXISTS moneybags_configuration (
    id VARCHAR(10) PRIMARY KEY,
    `key` VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY unique_config_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed initial configuration
INSERT INTO moneybags_configuration (id, `key`, value, created_at, updated_at) VALUES
('conf01', 'currency_format', 'nok', NOW(), NOW()),
('conf02', 'db_host', 'localhost', NOW(), NOW()),
('conf03', 'db_port', '3306', NOW(), NOW()),
('conf04', 'db_name', 'moneybags', NOW(), NOW()),
('conf05', 'db_user', 'moneybags_user', NOW(), NOW()),
('conf06', 'db_pool_size', '10', NOW(), NOW())
ON DUPLICATE KEY UPDATE updated_at=NOW();
