"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
def mock_admin_token():
    """Mock admin JWT token"""
    from app.core.security import create_access_token
    return create_access_token({
        "sub": "test-admin-id",
        "email": "admin@test.com",
        "role": "principal",
        "school_id": "test-school-id"
    })

@pytest.fixture
def mock_teacher_token():
    """Mock teacher JWT token"""
    from app.core.security import create_access_token
    return create_access_token({
        "sub": "test-teacher-id",
        "email": "teacher@test.com",
        "role": "teacher",
        "school_id": "test-school-id"
    })

@pytest.fixture
def auth_headers(mock_admin_token):
    """Authorization headers with admin token"""
    return {"Authorization": f"Bearer {mock_admin_token}"}
