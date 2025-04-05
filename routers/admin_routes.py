from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserUpdate, UserResponse, ProfileUpdate, PasswordUpdate
from typing import List
from .auth_routes import get_current_user
from .auth import verify_password, hash_password
import os
from pathlib import Path
import shutil

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

# Admin middleware
async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this resource"
        )
    return current_user

@router.get("/users")
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource"
            )
        
        users = db.query(User).all()
        # Format user data
        formatted_users = [{
            "id": user.id,
            "fullname": user.fullname,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "image": user.image,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            # Format for the Orders component
            "customer": {
                "name": user.fullname,
                "initials": "".join(name[0].upper() for name in user.fullname.split() if name)
            }
        } for user in users]
        
        return formatted_users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.from_db_model(user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    if user_data.email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_data.email
    
    if user_data.fullname is not None:
        user.fullname = user_data.fullname
    
    if user_data.role is not None:
        # Prevent changing the role of the last admin
        if user.role == "admin" and user_data.role != "admin":
            admin_count = db.query(User).filter(User.role == "admin").count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin user"
                )
        user.role = user_data.role

    if user_data.status is not None:
        user.status = user_data.status
    
    db.commit()
    
    return UserResponse.from_db_model(user)

@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Toggle status
    user.status = "inactive" if user.status == "active" else "active"
    db.commit()
    
    return UserResponse.from_db_model(user)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting the last admin
    if user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin user"
            )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

# Profile routes
@router.get("/profile", response_model=UserResponse)
async def get_admin_profile(current_user: User = Depends(get_admin_user)):
    return UserResponse.from_db_model(current_user)

@router.put("/profile", response_model=UserResponse)
async def update_admin_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    current_user.fullname = profile_data.fullname
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_db_model(current_user)

@router.post("/profile/avatar")
async def update_admin_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate file path
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"avatar_{current_user.id}{file_extension}"
    file_path = upload_dir / file_name
    
    # Save the file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user's image path in database
    current_user.image = f"/uploads/avatars/{file_name}"
    db.commit()
    
    return {"image_url": current_user.image}

@router.put("/profile/password")
async def change_admin_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_data.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.password = hash_password(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"} 