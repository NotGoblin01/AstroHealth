"""
AstroHealth Alert & Notification System Router
Manages automated clinical safety alerts, manual emergency distress escalations,
medical officer acknowledgments, resolution workflows, and audit logging.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query

from database import get_db
from models.schemas import (
    UserRole,
    AlertCategory,
    AlertStatus,
    HealthAlertCreate,
    HealthAlertResponse,
    AlertAcknowledgeRequest,
    AlertEmergencyRequest,
)
from auth.security import get_current_user, require_roles
from services.websocket_service import broadcaster

router = APIRouter(prefix="/api/alerts", tags=["Health Alerts"])


@router.get("", response_model=List[HealthAlertResponse])
async def list_alerts(
    astronaut_id: Optional[str] = None,
    category: Optional[AlertCategory] = None,
    status_filter: Optional[AlertStatus] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List alerts with optional filtering.
    Astronauts see personal alerts and spacecraft-wide emergencies.
    Medical Officers and Admins see all alerts.
    """
    query: Dict[str, Any] = {}
    if current_user.get("role") == UserRole.ASTRONAUT.value:
        astro_id = current_user.get("astronaut_id")
        if astro_id:
            query["$or"] = [{"astronaut_id": astro_id}, {"astronaut_id": "ALL_CREW"}]
        else:
            query["astronaut_id"] = "ALL_CREW"
    elif astronaut_id:
        query["astronaut_id"] = astronaut_id

    if category:
        query["category"] = category.value
    if status_filter:
        query["status"] = status_filter.value

    cursor = db.health_alerts.find(query).sort("created_at", -1).skip(skip).limit(limit)
    alerts = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        alerts.append(HealthAlertResponse(**doc))
    return alerts


@router.get("/active", response_model=List[HealthAlertResponse])
async def get_active_alerts(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve all currently active, unresolved health and safety alerts."""
    query = {"status": {"$in": [AlertStatus.ACTIVE.value, AlertStatus.INVESTIGATING.value]}}
    if current_user.get("role") == UserRole.ASTRONAUT.value:
        astro_id = current_user.get("astronaut_id")
        if astro_id:
            query["$or"] = [{"astronaut_id": astro_id}, {"astronaut_id": "ALL_CREW"}]

    cursor = db.health_alerts.find(query).sort("created_at", -1).limit(50)
    alerts = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        alerts.append(HealthAlertResponse(**doc))
    return alerts


@router.post("/emergency", response_model=HealthAlertResponse, status_code=status.HTTP_201_CREATED)
async def trigger_manual_emergency(
    req: AlertEmergencyRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Manually trigger an urgent crew distress or medical emergency alert.
    Accessible to all authenticated astronauts and mission personnel.
    """
    now = datetime.utcnow()
    alert_doc = {
        "astronaut_id": req.astronaut_id,
        "source": "manual_emergency",
        "category": AlertCategory.EMERGENCY.value,
        "title": f"CREW EMERGENCY: {req.title}",
        "message": req.reason,
        "details": {
            "declared_by": current_user.get("full_name", current_user.get("username")),
            "location": req.location,
            "user_role": current_user.get("role")
        },
        "status": AlertStatus.ACTIVE.value,
        "created_at": now
    }

    result = await db.health_alerts.insert_one(alert_doc)
    alert_id = str(result.inserted_id)
    alert_doc["id"] = alert_id

    # Audit log
    await db.audit_logs.insert_one({
        "timestamp": now,
        "action": "EMERGENCY_DECLARED",
        "user_id": current_user.get("id"),
        "details": {"alert_id": alert_id, "title": req.title, "astronaut_id": req.astronaut_id}
    })

    # High-priority WebSocket broadcast
    await broadcaster.broadcast({
        "type": "emergency_alert",
        "priority": "CRITICAL",
        "alert": {
            "id": alert_id,
            "title": alert_doc["title"],
            "message": alert_doc["message"],
            "astronaut_id": alert_doc["astronaut_id"],
            "category": alert_doc["category"],
            "created_at": now.isoformat()
        }
    })

    return HealthAlertResponse(**alert_doc)


@router.post("/{alert_id}/acknowledge", response_model=HealthAlertResponse)
async def acknowledge_alert(
    alert_id: str,
    ack_in: AlertAcknowledgeRequest = AlertAcknowledgeRequest(),
    current_user: dict = Depends(require_roles([UserRole.MEDICAL_OFFICER, UserRole.ADMINISTRATOR])),
    db = Depends(get_db)
):
    """
    Flight Surgeon / Admin acknowledges an active alert.
    Updates alert status to 'acknowledged' or 'investigating' with notes.
    """
    try:
        obj_id = ObjectId(alert_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alert ID format.")

    now = datetime.utcnow()
    update_fields = {
        "status": AlertStatus.ACKNOWLEDGED.value,
        "acknowledged_by": current_user.get("full_name", current_user.get("username")),
        "acknowledged_at": now
    }
    if ack_in.notes:
        update_fields["details.investigation_notes"] = ack_in.notes

    result = await db.health_alerts.find_one_and_update(
        {"_id": obj_id},
        {"$set": update_fields},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found.")

    # Audit log
    await db.audit_logs.insert_one({
        "timestamp": now,
        "action": "ALERT_ACKNOWLEDGED",
        "user_id": current_user.get("id"),
        "details": {"alert_id": alert_id, "notes": ack_in.notes}
    })

    result["id"] = str(result["_id"])
    return HealthAlertResponse(**result)


@router.post("/{alert_id}/resolve", response_model=HealthAlertResponse)
async def resolve_alert(
    alert_id: str,
    resolution_notes: str = Query(..., description="Clinical explanation of resolution and decision taken"),
    current_user: dict = Depends(require_roles([UserRole.MEDICAL_OFFICER, UserRole.ADMINISTRATOR])),
    db = Depends(get_db)
):
    """
    Flight Surgeon / Admin officially resolves an alert with recorded clinical justification.
    """
    try:
        obj_id = ObjectId(alert_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alert ID format.")

    now = datetime.utcnow()
    update_fields = {
        "status": AlertStatus.RESOLVED.value,
        "resolved_by": current_user.get("full_name", current_user.get("username")),
        "resolved_at": now,
        "resolution_notes": resolution_notes
    }

    result = await db.health_alerts.find_one_and_update(
        {"_id": obj_id},
        {"$set": update_fields},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found.")

    # Audit log
    await db.audit_logs.insert_one({
        "timestamp": now,
        "action": "ALERT_RESOLVED",
        "user_id": current_user.get("id"),
        "details": {"alert_id": alert_id, "resolution_notes": resolution_notes}
    })

    result["id"] = str(result["_id"])
    return HealthAlertResponse(**result)

