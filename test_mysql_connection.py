import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

try:
    print("Attempting to connect to MySQL...")
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    if connection.is_connected():
        db_info = connection.get_server_info()
        print(f"Connected to MySQL Server version {db_info}")
        
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS oxfordbakery")
        print("Database 'oxfordbakery' created or already exists")
        
        cursor.execute("USE oxfordbakery")
        print("Using database 'oxfordbakery'")
        
        # Create orders table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reference VARCHAR(255),
                status VARCHAR(50),
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Orders table created or already exists")
        
        # Create notifications table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                title VARCHAR(255),
                message TEXT,
                type VARCHAR(50),
                `read` BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Notifications table created or already exists")

except Error as e:
    print(f"Error while connecting to MySQL: {e}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection closed.") 