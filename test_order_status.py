import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_order_status():
    conn = None
    try:
        print("Connecting to MySQL database...")
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'oxfordbakery')
        )
        print("Successfully connected to MySQL database")
        
        cursor = conn.cursor(dictionary=True)
        
        # Get all orders
        print("\nFetching all orders...")
        cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
        orders = cursor.fetchall()
        
        if not orders:
            print("No orders found in the database")
            return
        
        print("\nFound orders:")
        for order in orders:
            print(f"Order ID: {order['id']}")
            print(f"Reference: {order['reference']}")
            print(f"Status: {order['status']}")
            print(f"User ID: {order['user_id']}")
            print("-" * 50)
        
        # Test updating order #24's status
        target_order_id = 24
        print(f"\nTesting status update for order {target_order_id}...")
        
        # Update order status
        new_status = "processing"
        cursor.execute("""
            UPDATE orders 
            SET status = %s 
            WHERE id = %s
        """, (new_status, target_order_id))
        
        # Create notification
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, `read`)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            orders[0]['user_id'],  # Using the user_id from the first order
            "Order Status Updated",
            f"Your order #{orders[0]['reference']} status has been updated to {new_status}.",
            "order",
            False
        ))
        
        conn.commit()
        print(f"Successfully updated order {target_order_id} status to {new_status}")
        
        # Verify the update
        cursor.execute("SELECT status FROM orders WHERE id = %s", (target_order_id,))
        updated_order = cursor.fetchone()
        print(f"Verified new status: {updated_order['status']}")
        
        # Check notification
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE user_id = %s 
            ORDER BY id DESC LIMIT 1
        """, (orders[0]['user_id'],))
        notification = cursor.fetchone()
        if notification:
            print("\nCreated notification:")
            print(f"Title: {notification['title']}")
            print(f"Message: {notification['message']}")
            print(f"Type: {notification['type']}")
            print(f"Read: {notification['read']}")
        
    except Error as e:
        print(f"MySQL Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"General error: {str(e)}")
        sys.exit(1)
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nMySQL connection closed.")

if __name__ == "__main__":
    test_order_status() 