-- Update any NULL created_at values to current timestamp
UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL; 