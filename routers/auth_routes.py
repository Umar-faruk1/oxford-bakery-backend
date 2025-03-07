from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserSignup, UserSignin
from .auth import hash_password, verify_password, create_jwt_token, verify_token

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Configure security scheme
security = HTTPBearer()

# Helper function to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserSignup, db: Session = Depends(get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = User(fullname=user.fullname, email=user.email, password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@router.post("/signin", status_code=status.HTTP_200_OK)
def signin(user: UserSignin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_jwt_token({"email": db_user.email, "role": db_user.role})
    
    # Include the full API URL in the image URL if it exists
    image_url = None
    if db_user.image:
        image_url = f"http://localhost:8000{db_user.image}"
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": db_user.email,
            "name": db_user.fullname,
            "image": image_url,
            "role": db_user.role
        }
    } 