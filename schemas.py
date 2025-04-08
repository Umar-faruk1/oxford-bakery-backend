from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

class UserSignup(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    confirm_password: str

class UserSignin(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    fullname: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    fullname: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "fullname": "John Doe",
                "role": "users",
                "status": "active"
            }
        }

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str
    image: Optional[str] = None
    joinDate: str

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, user):
        return cls(
            id=user.id,
            name=user.fullname,
            email=user.email,
            role=user.role,
            status=user.status,
            image=f"{BACKEND_URL}{user.image}" if user.image else None,
            joinDate=user.created_at.strftime("%Y-%m-%d") if user.created_at else datetime.now().strftime("%Y-%m-%d")
        )

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    image: Optional[str] = None
    item_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, category, with_count: bool = True):
        return cls(
            id=category.id,
            name=category.name,
            description=category.description,
            image=f"{BACKEND_URL}{category.image}" if category.image else None,
            item_count=len(category.menu_items) if with_count else 0,
            created_at=category.created_at,
            updated_at=category.updated_at
        )

class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    status: str = "active"

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemUpdate(MenuItemBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    status: Optional[str] = None

class MenuItemResponse(MenuItemBase):
    id: int
    image: Optional[str] = None
    category: CategoryResponse
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, menu_item):
        return cls(
            id=menu_item.id,
            name=menu_item.name,
            description=menu_item.description,
            price=menu_item.price,
            category_id=menu_item.category_id,
            status=menu_item.status,
            image=f"{BACKEND_URL}{menu_item.image}" if menu_item.image else None,
            category=CategoryResponse.from_db_model(menu_item.category, with_count=False),
            created_at=menu_item.created_at,
            updated_at=menu_item.updated_at
        )

class PromoCodeBase(BaseModel):
    code: str
    discount: str
    start_date: datetime
    end_date: datetime

class PromoCodeCreate(PromoCodeBase):
    pass

class PromoCodeUpdate(BaseModel):
    code: Optional[str] = None
    discount: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class PromoCodeResponse(BaseModel):
    id: int
    code: str
    discount: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @classmethod
    def from_db_model(cls, promo):
        if not promo:
            return None
        return cls(
            id=promo.id,
            code=promo.code,
            discount=str(promo.discount),  # Convert to string if it's not already
            start_date=promo.start_date,
            end_date=promo.end_date,
            is_active=promo.is_active,
            usage_count=promo.usage_count,
            created_at=promo.created_at,
            updated_at=promo.updated_at
        )

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class OrderItem(BaseModel):
    menu_item_id: int
    name: str
    quantity: int
    price: float
    image: Optional[str] = None

class OrderBase(BaseModel):
    reference: Optional[str] = None
    amount: float
    delivery_fee: float
    final_amount: float
    status: str = "pending"
    payment_status: str = "pending"
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    amount: float
    delivery_fee: float
    final_amount: float
    payment_reference: str
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    items: List[OrderItem]
    promo_code: Optional[str] = None

    class Config:
        from_attributes = True

class OrderResponse(OrderBase):
    id: int
    user_id: int
    payment_reference: Optional[str] = None
    created_at: datetime
    items: List[OrderItem]

    @field_validator('items', mode='before')
    @classmethod
    def parse_items(cls, value):
        if isinstance(value, str):
            return json.loads(value)
        return value

    class Config:
        from_attributes = True

class OrderFilter(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    per_page: int = 10

class PaginatedOrderResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    per_page: int
    pages: int
