"""
AstroHealth Mission Management Router
Handles spaceflight missions, target parameters, habitat compartmentalization, and crew assignments.
"""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_current_user, require_roles
from database import get_db
from models.schemas import (
    MissionCreate,
    MissionResponse,
    MissionBase,
    UserRole
)

router = APIRouter(prefix="/api/missions", tags=["Missions"])


@router.get("", response_model=List[MissionResponse])
async def list_missions(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """List all deep space and orbital exploration missions."""
    cursor = db.missions.find().sort("launch_date", -1)
    missions = []
    async for m in cursor:
        m["id"] = str(m["_id"])
        missions.append(m)
    return missions


@router.get("/{mission_code}", response_model=MissionResponse)
async def get_mission(
    mission_code: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve detailed mission parameters, crew roster, and habitat layout."""
    mission = await db.missions.find_one({"mission_code": mission_code})
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Mission {mission_code} not found."
        )
    mission["id"] = str(mission["_id"])
    return mission


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(
    mission_in: MissionCreate,
    current_user: dict = Depends(require_roles([UserRole.ADMINISTRATOR])),
    db = Depends(get_db)
):
    """Initialize a new space exploration mission (Admin only)."""
    existing = await db.missions.find_one({"mission_code": mission_in.mission_code})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Mission code {mission_in.mission_code} already exists."
        )

    now_utc = datetime.now(timezone.utc)
    mission_dict = mission_in.model_dump()
    mission_dict["created_at"] = now_utc

    result = await db.missions.insert_one(mission_dict)
    mission_dict["id"] = str(result.inserted_id)

    # Log audit event
    await db.audit_logs.insert_one({
        "timestamp": now_utc,
        "user_id": current_user["id"],
        "action": "MISSION_CREATED",
        "resource_type": "mission",
        "resource_id": mission_dict["mission_code"],
        "details": {"mission_name": mission_in.mission_name, "target": mission_in.target}
    })

    return mission_dict

