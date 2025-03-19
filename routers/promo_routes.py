from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import PromoCode, User
from schemas import PromoCodeCreate, PromoCodeUpdate, PromoCodeResponse
from .auth_routes import get_current_user
from datetime import datetime, timezone
from pydantic import BaseModel

class PromoValidateRequest(BaseModel):
    code: str

router = APIRouter(
    prefix="/promo",
    tags=["Promo Codes"]
)

@router.post("/", response_model=PromoCodeResponse)
async def create_promo_code(
    promo: PromoCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create promo codes"
        )

    # Check if promo code already exists
    existing_promo = db.query(PromoCode).filter(PromoCode.code == promo.code).first()
    if existing_promo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promo code already exists"
        )

    # Create new promo code
    db_promo = PromoCode(
        code=promo.code,
        discount=promo.discount,
        start_date=promo.start_date,
        end_date=promo.end_date,
        is_active=True
    )

    try:
        db.add(db_promo)
        db.commit()
        db.refresh(db_promo)
        return PromoCodeResponse.from_db_model(db_promo)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[PromoCodeResponse])
async def get_promo_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all promo codes"
        )

    promos = db.query(PromoCode).all()
    return [PromoCodeResponse.from_db_model(promo) for promo in promos]

@router.get("/{promo_id}", response_model=PromoCodeResponse)
async def get_promo_code(
    promo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view promo code details"
        )

    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )

    return PromoCodeResponse.from_db_model(promo)

@router.put("/{promo_id}", response_model=PromoCodeResponse)
async def update_promo_code(
    promo_id: int,
    promo_update: PromoCodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update promo codes"
        )

    # Get existing promo code
    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )

    # Check if code is being changed and if new code already exists
    if promo_update.code and promo_update.code != promo.code:
        existing_promo = db.query(PromoCode).filter(PromoCode.code == promo_update.code).first()
        if existing_promo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Promo code already exists"
            )

    # Update fields
    update_data = promo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(promo, field, value)

    try:
        db.commit()
        db.refresh(promo)
        return PromoCodeResponse.from_db_model(promo)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{promo_id}")
async def delete_promo_code(
    promo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete promo codes"
        )

    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )

    try:
        db.delete(promo)
        db.commit()
        return {"message": "Promo code deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/{promo_id}/toggle", response_model=PromoCodeResponse)
async def toggle_promo_status(
    promo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can toggle promo code status"
        )

    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )

    try:
        promo.is_active = not promo.is_active
        db.commit()
        db.refresh(promo)
        return PromoCodeResponse.from_db_model(promo)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/validate")
async def validate_promo_code(
    promo_data: PromoValidateRequest,
    db: Session = Depends(get_db)
):
    """Validate a promo code"""
    try:
        now = datetime.now(timezone.utc)
        promo = db.query(PromoCode).filter(
            PromoCode.code == promo_data.code,
            PromoCode.is_active == True,
            PromoCode.start_date <= now,
            PromoCode.end_date >= now
        ).first()

        if not promo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired promo code"
            )

        return {
            "valid": True,
            "code": promo.code,
            "discount": promo.discount,
            "usage_count": promo.usage_count
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 