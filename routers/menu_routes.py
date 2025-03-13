from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Body
from sqlalchemy.orm import Session
from database import get_db
from models import MenuItem, Category, User
from schemas import (
    MenuItemCreate, MenuItemUpdate, MenuItemResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from typing import List
from .auth_routes import get_current_user
import os
import shutil
from uuid import uuid4
import json

router = APIRouter(
    prefix="/menu",
    tags=["menu"]
)

# Helper function to save uploaded files
async def save_upload_file(upload_file: UploadFile) -> str:
    if not upload_file:
        return None
        
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Generate unique filename
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    # Use os.path.join and replace backslashes with forward slashes
    file_path = os.path.join(upload_dir, unique_filename).replace('\\', '/')
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return f"/{file_path}"

# Category endpoints
@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create categories"
        )
    
    try:
        image_path = await save_upload_file(image) if image else None
        
        db_category = Category(
            name=name,
            description=description,
            image=image_path
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        return CategoryResponse.from_db_model(db_category)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return [CategoryResponse.from_db_model(category) for category in categories]

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return CategoryResponse.from_db_model(category)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    name: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update categories"
        )
    
    try:
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Update fields
        db_category.name = name
        db_category.description = description
        
        if image:
            image_path = await save_upload_file(image)
            db_category.image = image_path
        
        db.commit()
        db.refresh(db_category)
        
        return CategoryResponse.from_db_model(db_category)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete categories"
        )
    
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has menu items
    if len(db_category.menu_items) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing menu items"
        )
    
    db.delete(db_category)
    db.commit()
    
    return {"message": "Category deleted successfully"}

# Menu Item endpoints
@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    status: str = Form("active"),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create menu items"
        )
    
    # Verify category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    try:
        image_path = await save_upload_file(image) if image else None
        
        db_item = MenuItem(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            status=status,
            image=image_path
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        return MenuItemResponse.from_db_model(db_item)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/items", response_model=List[MenuItemResponse])
async def get_menu_items(
    skip: int = 0,
    limit: int = 100,
    category_id: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(MenuItem)
    if category_id:
        query = query.filter(MenuItem.category_id == category_id)
    
    items = query.offset(skip).limit(limit).all()
    return [MenuItemResponse.from_db_model(item) for item in items]

@router.get("/items/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    return MenuItemResponse.from_db_model(item)

@router.put("/items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int,
    item_update: str = Form(None),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update menu items"
        )
    
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    
    try:
        # Parse the update data
        if not item_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
            
        update_data = json.loads(item_update)
        
        # If category_id is being updated, verify the new category exists
        if update_data.get('category_id'):
            category = db.query(Category).filter(Category.id == update_data['category_id']).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
        
        # Update fields from the JSON data
        for field, value in update_data.items():
            if field == 'status':
                # Convert status string to boolean
                setattr(db_item, field, value == 'active')
            elif field == 'price':
                # Ensure price is a float
                try:
                    setattr(db_item, field, float(value))
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid price format"
                    )
            elif field == 'category_id':
                # Ensure category_id is an integer
                try:
                    setattr(db_item, field, int(value))
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid category ID format"
                    )
            else:
                setattr(db_item, field, value)
        
        # Handle image upload if provided
        if image:
            image_path = await save_upload_file(image)
            db_item.image = image_path
        
        db.commit()
        db.refresh(db_item)
        
        return MenuItemResponse.from_db_model(db_item)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON data in item_update"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/items/{item_id}")
async def delete_menu_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete menu items"
        )
    
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    
    db.delete(db_item)
    db.commit()
    
    return {"message": "Menu item deleted successfully"} 