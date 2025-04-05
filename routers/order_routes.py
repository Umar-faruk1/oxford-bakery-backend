from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from datetime import datetime
from database import get_db
from models import Order, User
from schemas import OrderResponse, OrderCreate, PaginatedOrderResponse
from routers.auth_routes import get_current_user
import json
import requests
import os
from dotenv import load_dotenv
import uuid
from pydantic import ValidationError

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
        # Print incoming data for debugging
        print("Incoming order data:", order.model_dump())
        
        # Generate unique reference
        reference = f"ord_{uuid.uuid4().hex[:12]}"
        
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
            items=json.dumps([item.model_dump() for item in order.items]),
            status="pending",
            payment_status="pending",
            created_at=datetime.utcnow()
        )
        
        try:
            db.add(db_order)
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception as db_error:
            db.rollback()
            print(f"Database error: {str(db_error)}")
            raise HTTPException(status_code=422, detail=f"Database error: {str(db_error)}")
            
    except ValidationError as ve:
        print(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=422, detail=ve.errors())
    except Exception as e:
        print(f"General error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

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
                    db.commit()
                    
                    return {"status": "success", "message": "Payment verified"}
                
        raise HTTPException(status_code=400, detail="Payment verification failed")
    except Exception as e:
        print(f"Payment verification error: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment verification failed")

@router.patch("/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: OrderStatus = Body(...),
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
    
    # Update status
    order.status = status
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Order status updated successfully",
        "status": status
    } 