"""
Test attendance endpoints
"""
from datetime import date

def test_list_attendance_requires_auth(client):
    """Test that listing attendance requires authentication"""
    response = client.get("/api/v1/attendance")
    assert response.status_code == 401

def test_list_attendance_with_auth(client, auth_headers):
    """Test listing attendance with authentication"""
    response = client.get("/api/v1/attendance", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_attendance_summary(client, auth_headers):
    """Test getting attendance summary"""
    response = client.get("/api/v1/attendance/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert "total_records" in data
    assert "attendance_rate" in data

def test_record_attendance_requires_auth(client):
    """Test that recording attendance requires authentication"""
    attendance_data = {
        "student_id": "test-student",
        "date": date.today().isoformat(),
        "status": "present"
    }
    response = client.post("/api/v1/attendance", json=attendance_data)
    assert response.status_code == 401
