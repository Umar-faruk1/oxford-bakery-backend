from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import ProfileUpdate, PasswordUpdate
from .auth_routes import get_current_user
from .auth import verify_password, hash_password
import os
from datetime import datetime
import shutil

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.put("/profile", status_code=status.HTTP_200_OK)
async def update_profile(
    profile: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.fullname = profile.fullname
    db.commit()
    return {"message": "Profile updated successfully"}

@router.put("/password", status_code=status.HTTP_200_OK)
async def update_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_data.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    current_user.password = hash_password(password_data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@router.post("/profile-image", status_code=status.HTTP_200_OK)
async def upload_profile_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"profile_{current_user.id}_{timestamp}{os.path.splitext(image.filename)[1]}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image"
        )
    
    # Update user's image URL in database
    image_url = f"/uploads/{filename}"
    current_user.image = image_url
    db.commit()
    
    # Return the full URL
    return {"image_url": f"http://localhost:8000{image_url}"} 