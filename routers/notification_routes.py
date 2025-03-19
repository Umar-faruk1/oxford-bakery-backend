from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Notification
from schemas import NotificationResponse
from datetime import datetime

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get("/")
async def get_notifications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get all notifications"""
    try:
        notifications = db.query(Notification)\
            .order_by(Notification.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        return notifications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notification.read = True
        db.commit()
        return notification
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.patch("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    try:
        db.query(Notification)\
            .filter(Notification.read == False)\
            .update({"read": True})
        db.commit()
        return {"message": "All notifications marked as read"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 