# Testing Guide

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/api/test_students.py::test_list_students_with_auth
```

### Frontend Tests (To be implemented)

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## Test Structure

### Backend

```
tests/
├── conftest.py              # Fixtures and configuration
├── test_main.py             # Main app tests
└── api/
    ├── test_students.py     # Student endpoint tests
    ├── test_fees.py         # Fee endpoint tests
    └── test_attendance.py   # Attendance endpoint tests
```

### Writing Tests

#### Backend Example

```python
def test_create_student(client, auth_headers):
    """Test creating a new student"""
    student_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "2010-01-01",
        "gender": "male"
    }
    
    response = client.post(
        "/api/v1/students",
        json=student_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert "id" in data
```

## Test Coverage Goals

- Minimum 80% code coverage
- All API endpoints tested
- Authentication/authorization tested
- Error cases tested
- Edge cases covered

## Manual Testing Checklist

### Authentication
- [ ] User registration
- [ ] User login
- [ ] Token refresh
- [ ] Logout
- [ ] Invalid credentials
- [ ] Expired token

### Student Management
- [ ] List students
- [ ] Create student
- [ ] View student details
- [ ] Update student
- [ ] Delete student
- [ ] Search students
- [ ] Filter by grade/class

### Fee Management
- [ ] Create invoice
- [ ] Record payment
- [ ] View invoices
- [ ] Payment history
- [ ] Overdue invoices

### Attendance
- [ ] Record attendance
- [ ] Bulk attendance
- [ ] View attendance
- [ ] Attendance summary
- [ ] Chronic absentees

### Mobile Testing
- [ ] Responsive layout
- [ ] Touch interactions
- [ ] Navigation
- [ ] Forms
- [ ] Tables

## Performance Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

## Security Testing

- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Authentication bypass attempts
- [ ] Authorization checks
- [ ] Sensitive data exposure
