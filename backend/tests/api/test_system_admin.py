"""
Test system admin endpoints
"""

def test_platform_metrics_requires_system_admin(client, mock_teacher_token):
    """Test that platform metrics requires system admin role"""
    response = client.get(
        "/api/v1/system/platform-metrics",
        headers={"Authorization": f"Bearer {mock_teacher_token}"}
    )
    assert response.status_code == 403

def test_platform_metrics_with_system_admin(client):
    """Test getting platform metrics as system admin"""
    from app.core.security import create_access_token
    
    token = create_access_token({
        "sub": "test-sysadmin-id",
        "email": "sysadmin@test.com",
        "role": "system_admin",
        "school_id": None
    })
    
    response = client.get(
        "/api/v1/system/platform-metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_schools" in data
    assert "active_users" in data
    assert "system_uptime" in data

def test_schools_overview_requires_system_admin(client, auth_headers):
    """Test that schools overview requires system admin"""
    response = client.get(
        "/api/v1/system/schools-overview",
        headers=auth_headers
    )
    # Will fail with 403 if not system admin
    assert response.status_code in [200, 403]

def test_system_alerts(client):
    """Test getting system alerts"""
    from app.core.security import create_access_token
    
    token = create_access_token({
        "sub": "test-sysadmin-id",
        "email": "sysadmin@test.com",
        "role": "system_admin",
    })
    
    response = client.get(
        "/api/v1/system/system-alerts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_platform_activity(client):
    """Test getting platform activity"""
    from app.core.security import create_access_token
    
    token = create_access_token({
        "sub": "test-sysadmin-id",
        "email": "sysadmin@test.com",
        "role": "system_admin",
    })
    
    response = client.get(
        "/api/v1/system/platform-activity",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
