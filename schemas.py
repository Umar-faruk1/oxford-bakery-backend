from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

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
    orders: int
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
            orders=user.orders,
            image=f"http://localhost:8000{user.image}" if user.image else None,
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
            image=f"http://localhost:8000{category.image}" if category.image else None,
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
            image=f"http://localhost:8000{menu_item.image}" if menu_item.image else None,
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

class PromoCodeResponse(PromoCodeBase):
    id: int
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, promo):
        return cls(
            id=promo.id,
            code=promo.code,
            discount=promo.discount,
            start_date=promo.start_date,
            end_date=promo.end_date,
            usage_count=promo.usage_count,
            is_active=promo.is_active,
            created_at=promo.created_at,
            updated_at=promo.updated_at
        )

