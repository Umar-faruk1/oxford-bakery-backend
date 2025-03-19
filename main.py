from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
from models import Base
from routers import auth_routes, user_routes, admin_routes, menu_routes, promo_routes, payment_routes, notification_routes
from websocket_manager import manager

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the uploads directory to serve static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(menu_routes.router, prefix="/api")
app.include_router(promo_routes.router, prefix="/api")
app.include_router(payment_routes.router, prefix="/api")
app.include_router(notification_routes.router, prefix="/api")

# Optional: Add a test route
@app.get("/")
def read_root():
    return {"message": "Welcome to Oxford Bakery API"}

@app.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle received data if needed
    except Exception:
        manager.disconnect(websocket)


