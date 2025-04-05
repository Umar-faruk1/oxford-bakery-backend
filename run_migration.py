from database import engine
from sqlalchemy import text

def check_column_exists(connection, column_name):
    result = connection.execute(text(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = 'orders' "
        "AND COLUMN_NAME = :column "
        "AND TABLE_SCHEMA = DATABASE()"
    ), {"column": column_name}).scalar()
    return result > 0

def modify_column_nullable(connection, column_name, data_type):
    connection.execute(text(
        f"ALTER TABLE orders MODIFY COLUMN {column_name} {data_type} NULL;"
    ))
    connection.commit()
    print(f"Modified {column_name} to be nullable")

def run_migration():
    with engine.connect() as conn:
        try:
            # Check and add payment_status column
            if not check_column_exists(conn, 'payment_status'):
                conn.execute(text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50) DEFAULT 'pending';"))
                print("Added payment_status column")
            else:
                print("payment_status column already exists")
            
            # Check and add payment_reference column
            if not check_column_exists(conn, 'payment_reference'):
                conn.execute(text("ALTER TABLE orders ADD COLUMN payment_reference VARCHAR(255) NULL;"))
                print("Added payment_reference column")
            else:
                print("payment_reference column already exists")
            
            conn.commit()
            print("Migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {str(e)}")

if __name__ == "__main__":
    run_migration() 