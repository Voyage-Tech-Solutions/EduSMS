# EduCore - School Management SaaS Platform

A modern, multi-tenant school management system built with FastAPI and Next.js.

## Features

- ✅ Multi-tenant architecture with complete data isolation
- ✅ Role-based access control (6 roles)
- ✅ **System Admin Dashboard** - Platform-level management
- ✅ Student management with guardian tracking
- ✅ Fee management and invoicing
- ✅ Attendance tracking with analytics
- ✅ Academic grade management
- ✅ Real-time dashboards
- ✅ Mobile responsive design
- ✅ Secure authentication with Supabase

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- Supabase (PostgreSQL)
- JWT Authentication
- Row-Level Security (RLS)

**Frontend:**
- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- Shadcn UI

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Supabase account

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run development server
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API and Supabase URLs

# Run development server
npm run dev
```

Frontend runs at http://localhost:3000

### Database Setup

1. Create a Supabase project
2. Run the SQL schema from `backend/database/schema.sql`
3. Update `.env` files with your Supabase credentials

## Docker Deployment

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests

```bash
cd frontend
npm test
```

## API Documentation

When running in development mode, API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
EduSMS/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, security, logging
│   │   ├── db/              # Database connections
│   │   ├── models/          # Pydantic schemas
│   │   └── main.py          # FastAPI app
│   ├── tests/               # Backend tests
│   ├── database/            # SQL schemas
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
│   └── package.json
└── docker-compose.yml
```

## Environment Variables

### Backend (.env)

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET_KEY=your_secret_key
DEBUG=true
```

### Frontend (.env)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

## Security Features

- JWT-based authentication
- Row-Level Security (RLS) policies
- Rate limiting (100 req/min in production)
- CORS protection
- Password hashing with bcrypt
- Tenant isolation at database level

## Performance Optimizations

- Database indexes on frequently queried fields
- Connection pooling
- Response caching
- Image optimization
- Code splitting
- Lazy loading

## CI/CD

GitHub Actions workflows are configured for:
- Automated testing
- Code linting
- Build verification
- Deployment to Vercel (frontend)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
