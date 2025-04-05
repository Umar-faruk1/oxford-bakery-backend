from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
from models import Base

# Import routers
from routers.auth_routes import router as auth_router
from routers.user_routes import router as user_router
from routers.admin_routes import router as admin_router
from routers.menu_routes import router as menu_router
from routers.promo_routes import router as promo_router
from routers.notification_routes import router as notification_router
from routers.order_routes import router as order_router

app = FastAPI(
    title="Oxford Bakery API",
    description="API for Oxford Bakery",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(menu_router, prefix="/api")
app.include_router(promo_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
app.include_router(order_router, prefix="/api")

@app.get("/api")
async def root():
    return {"message": "Welcome to Oxford Bakery API"}
