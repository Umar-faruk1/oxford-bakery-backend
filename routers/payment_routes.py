from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import httpx
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import requests

from database import get_db
from models import Order, OrderItem, User, Notification, PromoCode
from schemas import OrderCreate, PaymentVerification, OrderResponse, OrderStatusUpdate
from .auth_routes import get_current_user

load_dotenv()
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

# Add this function to handle notifications
async def send_notification(db: Session, notification_data: dict):
    notification = Notification(
        title=notification_data["title"],
        message=notification_data["message"],
        type=notification_data["type"]
    )
    db.add(notification)
    db.commit()

@router.post("/create-order")
async def create_order(
    order_data: dict,
    db: Session = Depends(get_db)
):
    try:
        # Calculate final amount
        final_amount = order_data["amount"]

        # Create order
        order = Order(
            reference=order_data["reference"],
            email=order_data["email"],
            name=order_data["name"],
            phone=order_data["phone"],
            address=order_data["address"],
            amount=order_data["amount"],
            delivery_fee=20.00,
            final_amount=final_amount,
            promo_code=order_data.get("promo_code"),
            status="pending",
            created_at=datetime.now()
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # Increment promo code usage if used
        if order.promo_code:
            promo = db.query(PromoCode).filter(
                PromoCode.code == order.promo_code,
                PromoCode.is_active == True
            ).first()
            if promo:
                promo.usage_count += 1
                db.commit()

        # Create order items
        for item in order_data["items"]:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item["menu_item_id"],
                quantity=item["quantity"],
                price=item["price"]
            )
            db.add(order_item)
        
        db.commit()
        return {"order_id": order.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/verify/{reference}")
async def verify_payment(
    reference: str,
    db: Session = Depends(get_db)
):
    try:
        # Update order status
        order = db.query(Order).filter(Order.reference == reference).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        order.status = "paid"
        order.updated_at = datetime.now()
        db.commit()

        return {"message": "Payment verified successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/orders")
async def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for the current user"""
    try:
        if current_user.role == "admin":
            orders = db.query(Order).order_by(Order.created_at.desc()).all()
        else:
            orders = db.query(Order).filter(Order.user_id == current_user.id)\
                .order_by(Order.created_at.desc()).all()
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order

@router.post("/webhook")
async def paystack_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Verify Paystack webhook signature
    payload = await request.body()
    signature = request.headers.get("x-paystack-signature")

    # Verify signature here...

    try:
        event = json.loads(payload)
        if event["event"] == "charge.success":
            reference = event["data"]["reference"]
            order = db.query(Order).filter(Order.reference == reference).first()

            if order:
                order.status = "processing"
                order.payment_status = "paid"
                db.commit()

                # Send notification
                notification_data = {
                    "title": "Payment Successful",
                    "message": f"Payment received for order #{order.id}",
                    "type": "order"
                }
                background_tasks.add_task(send_notification, db, notification_data)

                return {"status": "success"}

        return {"status": "ignored"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update the order status
    order.status = status_update.status
    db.commit()
    db.refresh(order)
    
    # Broadcast the update via WebSocket if needed
    # await manager.broadcast({"type": "ORDER_UPDATE", "data": order})
    
    return order 