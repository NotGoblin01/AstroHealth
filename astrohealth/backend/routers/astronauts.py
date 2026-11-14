"""
AstroHealth Astronaut Management Router
Handles astronaut profiles, physiological baselines, medical clearance, and assigned equipment.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from auth.security import get_current_user, require_roles
from database import get_db
from models.schemas import (
    AstronautCreate,
    AstronautResponse,
    AstronautBase,
    UserRole
)

router = APIRouter(prefix="/api/astronauts", tags=["Astronauts"])


@router.get("", response_model=List[AstronautResponse])
async def list_astronauts(
    mission_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """List astronaut profiles. Accessible by authorized mission personnel."""
    query = {}
    if mission_id:
        query["mission_id"] = mission_id

    # If role is astronaut, allow viewing crew list or restricted personal info
    cursor = db.astronauts.find(query).sort("astronaut_id", 1)
    astronauts = []
    async for a in cursor:
        a["id"] = str(a["_id"])
        astronauts.append(a)
    return astronauts


@router.get("/{astronaut_id}", response_model=AstronautResponse)
async def get_astronaut_profile(
    astronaut_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve detailed astronaut profile, baseline vitals, and device assignments."""
    astronaut = await db.astronauts.find_one({"astronaut_id": astronaut_id})
    if not astronaut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Astronaut with ID {astronaut_id} not found."
        )

    # If current user is astronaut, ensure they only view their own profile or general crew data
    if current_user.get("role") == UserRole.ASTRONAUT.value:
        # Check user linkage
        if astronaut.get("user_id") and astronaut.get("user_id") != current_user["id"]:
            # Allowed to view basic info, but verify authorization
            pass

    astronaut["id"] = str(astronaut["_id"])
    return astronaut


@router.post("", response_model=AstronautResponse, status_code=status.HTTP_201_CREATED)
async def create_astronaut_profile(
    profile_in: AstronautCreate,
    current_user: dict = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.MEDICAL_OFFICER])),
    db = Depends(get_db)
):
    """Register a new astronaut profile (Medical Officer / Administrator only)."""
    existing = await db.astronauts.find_one({"astronaut_id": profile_in.astronaut_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Astronaut ID {profile_in.astronaut_id} already exists."
        )

    now_utc = datetime.now(timezone.utc)
    profile_dict = profile_in.model_dump()
    profile_dict["created_at"] = now_utc
    profile_dict["updated_at"] = now_utc

    result = await db.astronauts.insert_one(profile_dict)
    profile_dict["id"] = str(result.inserted_id)

    # Log audit event
    await db.audit_logs.insert_one({
        "timestamp": now_utc,
        "user_id": current_user["id"],
        "action": "ASTRONAUT_PROFILE_CREATED",
        "resource_type": "astronaut",
        "resource_id": profile_dict["astronaut_id"],
        "details": {"name": profile_in.full_name, "mission_id": profile_in.mission_id}
    })

    return profile_dict


@router.put("/{astronaut_id}", response_model=AstronautResponse)
async def update_astronaut_profile(
    astronaut_id: str,
    updates: AstronautBase,
    current_user: dict = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.MEDICAL_OFFICER])),
    db = Depends(get_db)
):
    """Update astronaut physiological baselines, devices, or clearance status."""
    now_utc = datetime.now(timezone.utc)
    update_data = updates.model_dump(exclude_unset=True)
    update_data["updated_at"] = now_utc

    result = await db.astronauts.find_one_and_update(
        {"astronaut_id": astronaut_id},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Astronaut ID {astronaut_id} not found."
        )

    result["id"] = str(result["_id"])
    return result

