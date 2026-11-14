"""
AstroHealth Authentication API Router
Handles login, registration, current user profile, and token refresh.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from bson import ObjectId

from auth.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    get_current_user
)
from database import get_db
from models.schemas import (
    UserCreate, 
    UserResponse, 
    TokenResponse, 
    UserLogin,
    UserRole
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db = Depends(get_db)):
    """Register a new user in the AstroHealth system."""
    # Check if username or email exists
    existing_user = await db.users.find_one({
        "$or": [{"username": user_in.username}, {"email": user_in.email}]
    })
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered."
        )

    now_utc = datetime.now(timezone.utc)
    user_dict = user_in.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = now_utc
    user_dict["updated_at"] = now_utc
    user_dict["is_active"] = True

    result = await db.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)

    # Log audit event
    await db.audit_logs.insert_one({
        "timestamp": now_utc,
        "user_id": user_dict["id"],
        "action": "USER_REGISTERED",
        "resource_type": "user",
        "resource_id": user_dict["id"],
        "details": {"username": user_in.username, "role": user_in.role}
    })

    return user_dict


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin, db = Depends(get_db)):
    """Authenticate user with username and password, return JWT token."""
    user = await db.users.find_one({"username": login_data.username})
    if not user or not verify_password(login_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or security credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    now_utc = datetime.now(timezone.utc)
    user_id = str(user["_id"])
    access_token = create_access_token(
        data={
            "sub": user_id,
            "username": user["username"],
            "role": user["role"]
        }
    )

    user_response = {
        "id": user_id,
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "callsign": user.get("callsign"),
        "rank": user.get("rank"),
        "mission_id": user.get("mission_id"),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at", now_utc)
    }

    # Log audit event
    await db.audit_logs.insert_one({
        "timestamp": now_utc,
        "user_id": user_id,
        "action": "USER_LOGIN",
        "resource_type": "auth",
        "resource_id": user_id,
        "details": {"username": user["username"], "role": user["role"]}
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    """OAuth2 compatible token endpoint for OpenAPI Swagger UI."""
    return await login_user(UserLogin(username=form_data.username, password=form_data.password), db)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Retrieve current logged in user information."""
    now_utc = datetime.now(timezone.utc)
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "callsign": current_user.get("callsign"),
        "rank": current_user.get("rank"),
        "mission_id": current_user.get("mission_id"),
        "is_active": current_user.get("is_active", True),
        "created_at": current_user.get("created_at", now_utc)
    }
