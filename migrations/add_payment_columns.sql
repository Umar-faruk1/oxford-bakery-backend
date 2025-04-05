ALTER TABLE orders 
ADD COLUMN payment_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN payment_reference VARCHAR(255) NULL; 