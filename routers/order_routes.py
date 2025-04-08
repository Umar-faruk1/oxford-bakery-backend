from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from datetime import datetime
from database import get_db
from models import Order, User, Notification, PromoCode
from schemas import OrderResponse, OrderCreate, PaginatedOrderResponse
from routers.auth_routes import get_current_user
import json
import requests
import os
from dotenv import load_dotenv
import uuid
from pydantic import ValidationError
import hmac
import hashlib
from sqlalchemy.sql import text

load_dotenv()
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

router = APIRouter()

# Add this with your other imports
OrderStatus = Literal["pending", "processing", "completed", "cancelled", "delivered"]

@router.get("/admin/orders", response_model=PaginatedOrderResponse)
async def get_admin_orders(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Order)
    
    # Apply filters
    if status and status != "all":
        query = query.filter(Order.status == status)
    if payment_status and payment_status != "all":
        query = query.filter(Order.payment_status == payment_status)
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)
    
    # Add pagination
    total = query.count()
    query = query.order_by(Order.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    orders = query.all()
    response_orders = []
    
    for order in orders:
        try:
            # Parse items JSON to list of OrderItems
            items = json.loads(order.items) if order.items else []
            
            order_dict = {
                "id": order.id,
                "reference": order.reference,
                "user_id": order.user_id,
                "amount": order.amount,
                "delivery_fee": order.delivery_fee,
                "final_amount": order.final_amount,
                "status": order.status,
                "payment_status": order.payment_status,
                "payment_reference": order.payment_reference,
                "items": items,
                "created_at": order.created_at,
                "email": order.email,
                "name": order.name,
                "phone": order.phone,
                "address": order.address
            }
            response_orders.append(OrderResponse(**order_dict))
        except Exception as e:
            print(f"Error processing order {order.id}: {str(e)}")
            continue
    
    return PaginatedOrderResponse(
        items=response_orders,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )

@router.get("/orders", response_model=List[OrderResponse])
async def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).all()
    
    # Convert orders to response format
    response_orders = []
    for order in orders:
        try:
            items = json.loads(order.items) if order.items else []
            if not isinstance(items, list):
                items = []
                
            response_orders.append(OrderResponse(
                id=order.id,
                reference=order.reference,
                user_id=order.user_id,
                amount=order.amount,
                delivery_fee=order.delivery_fee,
                final_amount=order.final_amount,
                status=order.status,
                items=items,
                created_at=order.created_at,
                email=order.email,
                name=order.name,
                phone=order.phone,
                address=order.address
            ))
        except Exception as e:
            print(f"Error processing order {order.id}: {str(e)}")
            continue
    
    return response_orders

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return order

@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate promo code if provided
        if order.promo_code:
            promo = db.query(PromoCode).filter(
                PromoCode.code == order.promo_code,
                PromoCode.is_active == True
            ).first()
            
            if not promo:
                raise HTTPException(status_code=400, detail="Invalid promo code")
            
            # Increment usage count
            promo.usage_count += 1
            db.commit()

        # Print incoming data for debugging
        print("Incoming order data:", order.model_dump())
        
        # Generate unique reference
        reference = f"ord_{uuid.uuid4().hex[:12]}"
        
        # Format items to ensure they have all required fields
        formatted_items = []
        for item in order.items:
            formatted_item = {
                "menu_item_id": item.menu_item_id,
                "name": item.name,
                "quantity": item.quantity,
                "price": item.price,
                "image": item.image if hasattr(item, 'image') else None
            }
            formatted_items.append(formatted_item)
        
        # Create new order
        db_order = Order(
            user_id=current_user.id,
            reference=reference,
            amount=order.amount,
            delivery_fee=order.delivery_fee,
            final_amount=order.final_amount,
            payment_reference=order.payment_reference,
            email=order.email,
            name=order.name,
            phone=order.phone,
            address=order.address,
            items=json.dumps(formatted_items),
            status="pending",
            payment_status="pending",
            created_at=datetime.utcnow()
        )
        
        try:
            db.add(db_order)
            db.commit()
            db.refresh(db_order)
            
            # Convert the order back to response format
            items = json.loads(db_order.items) if db_order.items else []
            return OrderResponse(
                id=db_order.id,
                reference=db_order.reference,
                user_id=db_order.user_id,
                amount=db_order.amount,
                delivery_fee=db_order.delivery_fee,
                final_amount=db_order.final_amount,
                status=db_order.status,
                payment_status=db_order.payment_status,
                payment_reference=db_order.payment_reference,
                items=items,
                created_at=db_order.created_at,
                email=db_order.email,
                name=db_order.name,
                phone=db_order.phone,
                address=db_order.address
            )
        except Exception as db_error:
            db.rollback()
            print(f"Database error: {str(db_error)}")
            raise HTTPException(status_code=422, detail=f"Database error: {str(db_error)}")
            
    except ValidationError as ve:
        print(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=422, detail=ve.errors())
    except Exception as e:
        print(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    # Get the Paystack signature from headers
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="No signature provided")
    
    # Get the raw body
    body = await request.body()
    
    # Verify the signature
    computed_hmac = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        body,
        hashlib.sha512
    ).hexdigest()
    
    if not hmac.compare_digest(computed_hmac, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse the webhook payload
    payload = json.loads(body)
    event = payload.get("event")
    
    if event == "charge.success":
        reference = payload["data"]["reference"]
        
        # Find and update the order
        order = db.query(Order).filter(Order.payment_reference == reference).first()
        if order:
            order.payment_status = "paid"
            order.status = "processing"
            db.commit()
            
            # Create a notification for the user
            notification = Notification(
                user_id=order.user_id,
                title="Payment Successful",
                message=f"Your order #{order.reference} has been paid and is being processed.",
                type="order"
            )
            db.add(notification)
            db.commit()
            
            return {"status": "success"}
    
    return {"status": "ignored"}

@router.post("/verify-payment/{reference}")
async def verify_payment(
    reference: str,
    db: Session = Depends(get_db)
):
    # Verify with Paystack
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }
    
    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["data"]["status"] == "success":
                # Update order
                order = db.query(Order).filter(
                    Order.payment_reference == reference
                ).first()
                
                if order:
                    order.payment_status = "paid"
                    order.status = "processing"
                    
                    # Create a notification for the user
                    notification = Notification(
                        user_id=order.user_id,
                        title="Payment Successful",
                        message=f"Your order #{order.reference} has been paid and is being processed.",
                        type="order"
                    )
                    db.add(notification)
                    db.commit()
                    
                    return {"status": "success", "message": "Payment verified"}
                
        raise HTTPException(status_code=400, detail="Payment verification failed")
    except Exception as e:
        print(f"Payment verification error: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment verification failed")

@router.patch("/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify admin access
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Validate status
    status = status_update.get("status")
    if not status or status not in ["pending", "processing", "completed", "cancelled", "delivered"]:
        raise HTTPException(status_code=422, detail="Invalid status value")
    
    try:
        # Update status
        order.status = status
        db.commit()
        db.refresh(order)
        
        # Create notification for the user
        notification = Notification(
            user_id=order.user_id,
            title="Order Status Updated",
            message=f"Your order #{order.reference} status has been updated to {status}.",
            type="order"
        )
        db.add(notification)
        db.commit()
        
        return {
            "message": "Order status updated successfully",
            "status": status,
            "order": OrderResponse(
                id=order.id,
                reference=order.reference,
                user_id=order.user_id,
                amount=order.amount,
                delivery_fee=order.delivery_fee,
                final_amount=order.final_amount,
                status=order.status,
                payment_status=order.payment_status,
                payment_reference=order.payment_reference,
                items=json.loads(order.items) if order.items else [],
                created_at=order.created_at,
                email=order.email,
                name=order.name,
                phone=order.phone,
                address=order.address
            )
        }
    except Exception as e:
        db.rollback()
        print(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 