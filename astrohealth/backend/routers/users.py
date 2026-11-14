"""
AstroHealth User Management Router
Provides CRUD endpoints for managing user accounts and roles.
"""
from datetime import datetime
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_current_user, require_roles
from database import get_db
from models.schemas import UserResponse, UserRole, UserBase

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    role: UserRole = None,
    current_user: dict = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.MEDICAL_OFFICER])),
    db = Depends(get_db)
):
    """List system users with optional role filtering."""
    query = {}
    if role:
        query["role"] = role.value

    cursor = db.users.find(query).sort("created_at", -1)
    users = []
    async for u in cursor:
        u["id"] = str(u["_id"])
        users.append(u)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve specific user details."""
    # Allow if self or if admin/medical officer
    if current_user["id"] != user_id and current_user.get("role") not in [UserRole.ADMINISTRATOR.value, UserRole.MEDICAL_OFFICER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user["id"] = str(user["_id"])
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    updates: UserBase,
    current_user: dict = Depends(require_roles([UserRole.ADMINISTRATOR])),
    db = Depends(get_db)
):
    """Update user information and roles (Admin only)."""
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")

    update_dict = updates.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()

    result = await db.users.find_one_and_update(
        {"_id": obj_id},
        {"$set": update_dict},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result["id"] = str(result["_id"])
    return result

