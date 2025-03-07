from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
from models import Base
from routers import auth_routes, user_routes, admin_routes, menu_routes, promo_routes

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Mount the uploads directory to serve static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(admin_routes.router)
app.include_router(menu_routes.router)
app.include_router(promo_routes.router)


