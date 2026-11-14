"""
AstroHealth Phase 1 Test Suite
Direct async tests for MongoDB connectivity, authentication, JWT tokens, RBAC, and seed data.
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import DatabaseManager, get_db
from seed import seed_database
from models.schemas import UserLogin, UserCreate, UserRole, UserBase
from routers import auth, users
from auth.security import verify_password, get_password_hash, create_access_token, require_roles
import main

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database has seed data and indexes before running tests."""
    seed_database()

@pytest.mark.anyio
async def test_health_check():
    """Verify system health endpoint."""
    res = await main.health_check()
    assert res["status"] == "operational"
    assert res["database"]["type"] == "MongoDB"
    assert res["database"]["database_name"] == "astrohealth_db"
    assert res["offline_storage"]["type"] == "SQLite"

@pytest.mark.anyio
async def test_system_info():
    """Verify mission and sensors info endpoint."""
    res = await main.system_info()
    assert "Ares-V" in res["mission"]
    assert any("MAX30102" in s for s in res["supported_sensors"])

@pytest.mark.anyio
async def test_login_success_admin():
    """Verify admin login returns JWT access token."""
    db = await get_db()
    login_data = UserLogin(username="admin", password="AdminPassword123!")
    res = await auth.login_user(login_data, db)
    assert "access_token" in res
    assert res["token_type"] == "bearer"
    assert res["user"]["role"] == "admin"
    assert res["user"]["username"] == "admin"

@pytest.mark.anyio
async def test_login_success_astronaut():
    """Verify astronaut login returns correct role and callsign."""
    db = await get_db()
    login_data = UserLogin(username="astro_alex", password="AstroPassword123!")
    res = await auth.login_user(login_data, db)
    assert res["user"]["role"] == "astronaut"
    assert res["user"]["callsign"] == "Pioneer-1"

@pytest.mark.anyio
async def test_login_invalid_password():
    """Verify login failure raises HTTPException 401."""
    from fastapi import HTTPException
    db = await get_db()
    login_data = UserLogin(username="admin", password="WrongPassword!")
    with pytest.raises(HTTPException) as exc_info:
        await auth.login_user(login_data, db)
    assert exc_info.value.status_code == 401

@pytest.mark.anyio
async def test_current_user_me():
    """Verify profile response matches user object."""
    mock_user = {
        "id": "mock_id_123",
        "username": "dr_vance",
        "email": "vance@astrohealth.space",
        "full_name": "Dr. Marcus Vance, MD",
        "role": "medical_officer",
        "callsign": "Caduceus-1",
        "rank": "Chief Medical Officer",
        "mission_id": "ARES-V",
        "is_active": True
    }
    res = await auth.get_current_user_profile(mock_user)
    assert res["username"] == "dr_vance"
    assert res["role"] == "medical_officer"
    assert res["rank"] == "Chief Medical Officer"

@pytest.mark.anyio
async def test_user_registration():
    """Verify creating a new user through registration endpoint."""
    db = await get_db()
    test_username = f"astro_pilot_{int(asyncio.get_event_loop().time())}"
    new_user = UserCreate(
        username=test_username,
        email=f"{test_username}@astrohealth.space",
        password="PilotPassword123!",
        full_name="Major Tom Davis",
        role=UserRole.ASTRONAUT,
        callsign="Star-9",
        rank="Test Pilot",
        mission_id="ARES-V"
    )
    reg_res = await auth.register_user(new_user, db)
    assert reg_res["username"] == test_username
    assert reg_res["role"] == "astronaut"

    # Verify user can login
    login_res = await auth.login_user(
        UserLogin(username=test_username, password="PilotPassword123!"),
        db
    )
    assert login_res["user"]["username"] == test_username

@pytest.mark.anyio
async def test_rbac_access_restriction():
    """Verify role-based access control prevents astronauts from accessing admin functions."""
    from fastapi import HTTPException
    admin_checker = require_roles([UserRole.ADMINISTRATOR])
    
    # Astronaut user attempting admin access
    astronaut_user = {"id": "1", "username": "astro_alex", "role": "astronaut"}
    with pytest.raises(HTTPException) as exc_info:
        await admin_checker(astronaut_user)
    assert exc_info.value.status_code == 403

    # Admin user permitted
    admin_user = {"id": "2", "username": "admin", "role": "admin"}
    allowed = await admin_checker(admin_user)
    assert allowed["username"] == "admin"
