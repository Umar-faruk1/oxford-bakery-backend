from database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True) 
    image = Column(String(1000), nullable=True)
    role = Column(String(50), default="users")  # Add role field with default value
    status = Column(String(50), default="active")  # 'active' or 'inactive'
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    image = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with menu items
    menu_items = relationship("MenuItem", back_populates="category")

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    image = Column(String(1000), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    status = Column(String(50), default="active")  # 'active' or 'inactive'
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with category
    category = relationship("Category", back_populates="menu_items")

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)
    discount = Column(String(50))  # Can be percentage (e.g., "20%") or fixed amount
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Make nullable
    reference = Column(String(255))
    email = Column(String(255))
    name = Column(String(255))
    phone = Column(String(50))
    address = Column(String(500))
    amount = Column(Float)
    delivery_fee = Column(Float, default=20.00)
    final_amount = Column(Float)  # Add this field
    promo_code = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")
    payment_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship(
        "User",
        backref=backref("orders", cascade="all, delete-orphan"),
        single_parent=True
    )
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # order, user, system
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
