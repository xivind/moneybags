-- Migration: Add comment field to budget entries
-- Date: 2025-12-24
-- Description: Adds optional comment field to moneybags_budget_entries table

ALTER TABLE moneybags_budget_entries ADD COLUMN comment TEXT NULL;
