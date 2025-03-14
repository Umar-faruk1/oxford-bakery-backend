import mysql.connector
from mysql.connector import Error
from urllib.parse import unquote

def init_database():
    try:
        # Create connection without database specified
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="faruk@2001"  # Original password with @ symbol
        )
        
        if conn.is_connected():
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS oxfordbakery")
            print("Database oxfordbakery created successfully")
            
            # Close connection
            cursor.close()
            conn.close()
            print("MySQL connection is closed")
            
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")

if __name__ == "__main__":
    init_database() 