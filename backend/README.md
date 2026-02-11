# EduCore Backend

FastAPI backend for EduCore SaaS multi-tenant school management platform.

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

## Project Structure

```
app/
├── api/v1/          # API endpoints
├── core/            # Config, security, permissions
├── models/          # Pydantic schemas
├── services/        # Business logic
├── db/              # Database connection & tenant context
└── main.py          # FastAPI app entry
```
