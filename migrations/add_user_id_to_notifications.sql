-- Add user_id column to notifications table
ALTER TABLE notifications ADD COLUMN user_id INTEGER REFERENCES users(id); 