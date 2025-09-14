# AK Cloud Native Transformation Management System - Backend

Backend API service for managing enterprise application transformation from traditional architecture to AK/Cloud Native.

## Features

- 🔐 SSO Authentication with JWT tokens
- 📊 Application and subtask management
- 🔄 Automatic status calculation
- 📝 Comprehensive audit logging
- 📁 Excel import/export functionality
- 📈 Progress reporting and analytics
- 🔔 Notification system
- 🚀 Async task processing with Celery

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7.0+
- **ORM**: SQLAlchemy 2.0 with Alembic
- **Task Queue**: Celery with Redis broker
- **Testing**: pytest with asyncio support
- **Deployment**: Docker & Kubernetes ready

## Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd AKCNBackEnd

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# At minimum, set:
# - DATABASE_URL
# - REDIS_URL
# - JWT_SECRET_KEY
# - SSO configuration
```

### 3. Database Setup

```bash
# Start PostgreSQL and Redis (using Docker)
docker-compose up -d db redis

# Run database migrations
alembic upgrade head
```

### 4. Run Application

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Make
make run
```

Visit http://localhost:8000/docs for API documentation.

### 5. Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Development

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Database Operations

```bash
# Create new migration
make migrate-create

# Apply migrations
make migrate

# Rollback migration
make migrate-rollback
```

### API Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/api/test_applications.py

# Run tests in parallel
pytest -n auto
```

## Project Structure

```
AKCNBackEnd/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Core configuration
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── middleware/       # Custom middleware
│   └── main.py          # Application entry point
├── tests/               # Test suite
├── alembic/            # Database migrations
├── docker-compose.yml  # Docker services
├── Dockerfile         # Application container
├── requirements.txt   # Python dependencies
└── Makefile          # Development commands
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Main Endpoints

- `POST /api/v1/sso/verify` - Verify SSO token
- `GET /api/v1/applications` - List applications
- `POST /api/v1/applications` - Create application
- `GET /api/v1/subtasks` - List subtasks
- `PUT /api/v1/subtasks/{id}` - Update subtask
- `GET /api/v1/audit/logs` - Audit logs
- `GET /api/v1/reports/export` - Export data

## Performance Targets

- API response time: 95% < 2 seconds
- Concurrent users: 500+
- System availability: >99.5%
- Excel import: 10,000 rows < 30 seconds

## Contributing

1. Create feature branch from `main`
2. Make changes following coding standards
3. Add tests for new functionality
4. Run quality checks: `make lint test`
5. Create pull request for review

## Monitoring

- **Health Check**: `GET /health`
- **Celery Monitoring**: http://localhost:5555 (Flower)
- **Logs**: Structured JSON logging with request IDs
- **Error Tracking**: Sentry integration

## License

Internal company project - All rights reserved.