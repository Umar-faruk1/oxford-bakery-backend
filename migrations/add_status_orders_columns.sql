-- Add status column with default value 'active'
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- Add orders column with default value 0
ALTER TABLE users ADD COLUMN orders INT DEFAULT 0; 