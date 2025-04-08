import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    conn = None
    try:
        print("Attempting to connect to MySQL database...")
        # Connect to the database
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='faruk@2001',
            database='oxfordbakery'
        )
        print("Successfully connected to MySQL database")
        
        cursor = conn.cursor()
        
        # Check if notifications table exists
        print("Checking if notifications table exists...")
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'oxfordbakery'
            AND table_name = 'notifications'
        """)
        
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            print("Creating notifications table...")
            # Create notifications table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    `read` BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            print("Successfully created notifications table with user_id column")
        else:
            print("Notifications table exists, checking for user_id column...")
            # Check if user_id column exists
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = 'oxfordbakery'
                AND table_name = 'notifications'
                AND column_name = 'user_id'
            """)
            
            column_exists = cursor.fetchone()[0] > 0
            
            if not column_exists:
                print("Adding user_id column...")
                # Add user_id column if it doesn't exist
                cursor.execute("""
                    ALTER TABLE notifications
                    ADD COLUMN user_id INT,
                    ADD FOREIGN KEY (user_id) REFERENCES users(id)
                """)
                print("Successfully added user_id column to notifications table")
            else:
                print("user_id column already exists in notifications table")
        
        conn.commit()
        print("Migration completed successfully")
        
    except Error as e:
        print(f"MySQL Error: {str(e)}")
        if e.errno == 1045:  # Access denied
            print("Error: Access denied. Please check your MySQL username and password.")
        elif e.errno == 1049:  # Unknown database
            print("Error: Database 'oxfordbakery' does not exist. Please create it first.")
        elif e.errno == 2003:  # Can't connect to server
            print("Error: Cannot connect to MySQL server. Please check if the server is running.")
        sys.exit(1)
    except Exception as e:
        print(f"General error: {str(e)}")
        sys.exit(1)
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    run_migration() 