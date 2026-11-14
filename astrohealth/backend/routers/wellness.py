"""
AstroHealth Psychological Wellness Router
Provides private daily wellness assessments, sleep quality tracking,
stress self-reporting, supportive non-diagnostic insights, and history.
Strictly protects crew privacy via role-based access control.
"""
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query

from database import get_db
from models.schemas import (
    UserRole,
    DailyWellnessCreate,
    DailyWellnessResponse,
)
from auth.security import get_current_user, require_roles

router = APIRouter(prefix="/api/wellness", tags=["Psychological Wellness"])


def generate_supportive_insight(entry: DailyWellnessCreate) -> str:
    """
    Generates supportive, non-diagnostic guidance based on self-reported scores.
    Strictly non-diagnostic and grounding in aerospace sleep/circadian hygiene.
    """
    insights = []
    if entry.sleep_hours < 6.0:
        insights.append(
            f"Sleep duration ({entry.sleep_hours}h) is below optimal deep-space baseline (7.5h). "
            "Consider 30-minute scheduled sleep banking prior to heavy cognitive duties."
        )
    elif entry.sleep_hours >= 7.5 and entry.sleep_quality_score >= 8:
        insights.append("Sleep architecture and reported restorative quality are excellent.")

    if entry.stress_score >= 8 or entry.fatigue_score >= 8:
        insights.append(
            "High subjective stress/fatigue noted. Autonomic relaxation protocol "
            "(guided box-breathing or earth audio soundscapes) is recommended during evening wind-down."
        )
    elif entry.stress_score <= 3 and entry.mood_score >= 8:
        insights.append("Psychological resilience indicators and mood valence remain strongly positive.")

    if entry.workload_rating >= 8:
        insights.append("Reported mission workload is elevated. Ensure regular scheduled micro-breaks.")

    if not insights:
        insights.append("Circadian rhythms and daily wellness ratings appear balanced and nominal.")

    return " ".join(insights)


@router.post("", response_model=DailyWellnessResponse, status_code=status.HTTP_201_CREATED)
async def submit_daily_wellness(
    entry_in: DailyWellnessCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Submit daily psychological wellness evaluation.
    Astronauts may submit for themselves; Medical Officers may record on behalf of crew.
    """
    # Privacy check: Astronauts can only submit for their own astronaut_id
    if current_user.get("role") == UserRole.ASTRONAUT.value:
        astro_id = current_user.get("astronaut_id")
        if astro_id and entry_in.astronaut_id != astro_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Astronauts may only submit private wellness logs for themselves."
            )

    # Generate supportive non-diagnostic insight
    insight = generate_supportive_insight(entry_in)

    doc = entry_in.model_dump()
    doc.update({
        "created_at": datetime.utcnow(),
        "supportive_insight": insight
    })

    # Upsert by astronaut_id and date
    result = await db.mental_health_logs.update_one(
        {"astronaut_id": entry_in.astronaut_id, "date": entry_in.date},
        {"$set": doc},
        upsert=True
    )

    saved = await db.mental_health_logs.find_one(
        {"astronaut_id": entry_in.astronaut_id, "date": entry_in.date}
    )
    saved["id"] = str(saved["_id"])
    return DailyWellnessResponse(**saved)


@router.get("/history/{astronaut_id}", response_model=List[DailyWellnessResponse])
async def get_wellness_history(
    astronaut_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Retrieve psychological wellness history.
    Strict privacy: Astronauts can only inspect their own logs.
    Medical Officers and Admins can inspect authorized crew records.
    """
    user_role = current_user.get("role")
    if user_role == UserRole.ASTRONAUT.value and current_user.get("astronaut_id") != astronaut_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Psychological wellness records are confidential to the individual astronaut."
        )

    cursor = db.mental_health_logs.find(
        {"astronaut_id": astronaut_id}
    ).sort("date", -1).limit(days)

    records = []
    async for r in cursor:
        r["id"] = str(r["_id"])
        records.append(DailyWellnessResponse(**r))
    return records


@router.get("/latest/{astronaut_id}", response_model=Optional[DailyWellnessResponse])
async def get_latest_wellness(
    astronaut_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get the most recent daily wellness entry for an astronaut."""
    user_role = current_user.get("role")
    if user_role == UserRole.ASTRONAUT.value and current_user.get("astronaut_id") != astronaut_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    doc = await db.mental_health_logs.find_one(
        {"astronaut_id": astronaut_id},
        sort=[("date", -1)]
    )
    if not doc:
        return None

    doc["id"] = str(doc["_id"])
    return DailyWellnessResponse(**doc)

