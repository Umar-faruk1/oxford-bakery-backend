from sqlalchemy import create_engine, text

# Replace these with your actual database credentials
DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/oxford_bakery"

def run_migrations():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # Add status column
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
            print("Added status column successfully")
        except Exception as e:
            print(f"Error adding status column: {e}")
        
        # Add orders column
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN orders INT DEFAULT 0"))
            print("Added orders column successfully")
        except Exception as e:
            print(f"Error adding orders column: {e}")
        
        connection.commit()

if __name__ == "__main__":
    run_migrations() 