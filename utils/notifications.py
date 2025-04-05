import os
from typing import Optional
import httpx
from fastapi import BackgroundTasks

async def send_email(to_email: str, subject: str, content: str):
    """Send email using your preferred email service"""
    # TODO: Implement email sending using your preferred service
    # For example: SendGrid, AWS SES, etc.
    pass

async def send_order_notification(order_id: int, status: str, user_email: str):
    """Send order status notification to user"""
    status_messages = {
        "created": "Your order has been received and is being processed.",
        "processing": "Your order is being prepared.",
        "ready": "Your order is ready for pickup/delivery.",
        "out_for_delivery": "Your order is out for delivery.",
        "completed": "Your order has been delivered. Enjoy!",
        "cancelled": "Your order has been cancelled."
    }
    
    message = status_messages.get(status.lower(), f"Your order status has been updated to: {status}")
    subject = f"Order #{order_id} Update"
    
    await send_email(user_email, subject, message)

async def send_payment_notification(order_id: int, status: str, user_email: str):
    """Send payment status notification to user"""
    if status.lower() == "success":
        subject = f"Payment Confirmed for Order #{order_id}"
        message = "Your payment has been successfully processed. We'll start preparing your order right away!"
    else:
        subject = f"Payment Update for Order #{order_id}"
        message = f"Your payment status has been updated to: {status}"
    
    await send_email(user_email, subject, message)
