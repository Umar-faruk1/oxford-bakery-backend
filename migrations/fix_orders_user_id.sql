-- Update any NULL user_ids to a default admin user (replace 1 with your admin user id)
UPDATE orders SET user_id = 1 WHERE user_id IS NULL;
-- Make user_id NOT NULL
ALTER TABLE orders MODIFY COLUMN user_id INT NOT NULL; 