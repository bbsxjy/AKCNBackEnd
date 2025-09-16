# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AK Cloud Native Transformation Management System - Backend API Service

This is a FastAPI-based backend for managing enterprise application transformation from traditional architecture to AK/Cloud Native. The system tracks transformation progress across multiple applications and their subtasks, with automatic status calculation and comprehensive audit logging.

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (main) + Redis (cache)
- **Authentication**: SSO integration with JWT tokens
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Testing**: pytest + pytest-asyncio
- **API Docs**: Auto-generated via FastAPI (/docs)

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Database Operations
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_applications.py

# Run tests in parallel
pytest -n auto
```

### Code Quality
```bash
# Format code with black
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/

# All quality checks
make lint
```

## Project Structure

```
AKCNBackEnd/
├── app/
│   ├── api/
│   │   ├── deps.py           # Dependency injection (auth, db, etc.)
│   │   └── v1/
│   │       ├── endpoints/     # API endpoints
│   │       │   ├── applications.py  # Application CRUD endpoints
│   │       │   ├── subtasks.py      # SubTask CRUD endpoints
│   │       │   ├── auth.py          # Authentication endpoints
│   │       │   ├── audit.py         # Audit log endpoints
│   │       │   ├── calculation.py   # Progress calculation endpoints
│   │       │   ├── dashboard.py     # Dashboard statistics endpoints
│   │       │   ├── excel.py         # Excel import/export endpoints
│   │       │   ├── notifications.py # Notification endpoints
│   │       │   └── reports.py       # Report generation endpoints
│   │       └── api.py        # API router aggregation
│   ├── core/
│   │   ├── config.py         # Settings and configuration
│   │   ├── database.py       # Database connection & session
│   │   ├── exceptions.py     # Custom exception classes
│   │   └── security.py       # JWT and security utilities
│   ├── db/
│   │   └── session.py        # Database session management
│   ├── models/               # SQLAlchemy models
│   │   ├── __init__.py       # Model exports
│   │   ├── application.py    # Application model with hybrid properties
│   │   ├── audit_log.py      # Audit logging model
│   │   ├── base.py           # Base model with timestamps
│   │   ├── notification.py   # Notification model
│   │   ├── subtask.py        # SubTask model
│   │   └── user.py           # User model with roles
│   ├── schemas/              # Pydantic schemas
│   │   ├── application.py    # Application request/response schemas
│   │   ├── audit.py          # Audit log schemas
│   │   ├── auth.py           # Authentication schemas
│   │   ├── calculation.py    # Calculation schemas
│   │   ├── dashboard.py      # Dashboard schemas
│   │   ├── excel.py          # Excel import/export schemas
│   │   ├── notification.py   # Notification schemas
│   │   ├── reports.py        # Report schemas
│   │   └── subtask.py        # SubTask schemas
│   ├── services/             # Business logic
│   │   ├── application_service.py  # Application business logic
│   │   ├── audit_service.py        # Audit operations
│   │   ├── calculation_service.py  # Progress calculations
│   │   ├── excel_service.py        # Excel processing logic
│   │   ├── notification_service.py # Notification management
│   │   ├── reports_service.py      # Report generation
│   │   ├── sso_service.py          # SSO integration
│   │   └── subtask_service.py      # SubTask business logic
│   └── main.py              # FastAPI app initialization
├── tests/                    # Test files (structure TBD)
├── alembic/                  # Database migrations
│   ├── versions/             # Migration files
│   └── env.py               # Alembic configuration
├── init_db.py               # Database initialization script
├── production_server.py     # Standalone production server
├── setup_postgresql_complete.py # Complete DB setup with test data
├── requirements.txt
└── .env.example
```

## Key Business Logic

### Application Status Calculation
- Status automatically updates based on subtask progress
- States: 待启动 → 研发进行中 → 业务上线中 → 全部完成
- Progress percentage calculated from weighted subtask completion

### Role-Based Access Control
- **Admin**: Full system access
- **Manager**: Department-level data management
- **Editor**: Edit assigned applications/tasks
- **Viewer**: Read-only access

### Audit System
- All data changes logged with before/after values
- Supports rollback to previous state
- No limit on audit log retention (no 1000 record cap)

## API Overview

Base URL: `http://localhost:8000/api/v1`

### Main Endpoints

#### Authentication
- `POST /auth/sso/verify` - Verify SSO token
- `POST /auth/login` - Standard login with credentials
- `POST /auth/refresh` - Refresh JWT token
- `GET /auth/me` - Get current user profile
- `GET /auth/permissions` - Get user permissions

#### Application Management
- `GET /applications/` - List applications (paginated, filterable)
- `POST /applications/` - Create new application
- `PUT /applications/{app_id}` - Update application by ID
- `GET /applications/{app_id}` - Get single application
- `GET /applications/l2/{l2_id}` - Get application by L2 ID
- `DELETE /applications/{app_id}` - Delete application
- `GET /applications/statistics` - Application statistics
- `GET /applications/delayed` - Get delayed applications
- `GET /applications/team/{team_name}` - Applications by team
- `POST /applications/bulk/recalculate` - Bulk recalculate status

#### SubTask Management
- `GET /subtasks/` - List subtasks (paginated, filterable)
- `POST /subtasks/` - Create new subtask
- `PUT /subtasks/{task_id}` - Update subtask
- `GET /subtasks/{task_id}` - Get single subtask
- `DELETE /subtasks/{task_id}` - Delete subtask
- `GET /subtasks/my-tasks` - User's assigned tasks
- `POST /subtasks/batch-update` - Batch update subtasks
- `POST /subtasks/batch/recalculate` - Bulk recalculate progress

#### Dashboard & Analytics
- `GET /dashboard/stats` - Dashboard statistics summary
- `GET /dashboard/progress-trend` - Progress trend over time
- `GET /dashboard/department-distribution` - Applications by department

#### Excel Operations
- `POST /excel/applications/import` - Import applications from Excel
- `POST /excel/subtasks/import` - Import subtasks from Excel
- `POST /excel/export/applications` - Export applications to Excel
- `GET /excel/subtasks/export` - Export subtasks to Excel
- `GET /excel/template` - Generate Excel import template
- `POST /excel/preview` - Preview Excel file before import
- `POST /excel/validate` - Validate Excel file
- `GET /excel/import/history` - Excel import history
- `GET /excel/export/formats` - Available export formats
- `GET /excel/mapping/templates` - Excel mapping templates
- `GET /excel/health` - Excel service health check

#### Calculation Services
- `POST /calculation/calculate` - Calculate application progress
- `POST /calculation/bulk-calculate` - Bulk calculate multiple applications
- `GET /calculation/status` - Calculation service status

#### Audit & Compliance
- `GET /audit/logs` - View audit trail
- `POST /audit/rollback/{log_id}` - Rollback changes
- `GET /audit/export` - Export audit logs

#### Reports
- `GET /reports/progress` - Progress summary report
- `GET /reports/delayed` - Delayed applications report
- `GET /reports/department` - Department performance report
- `GET /reports/export` - Export reports to various formats

#### Notifications
- `GET /notifications/` - Get user notifications
- `PUT /notifications/{id}/read` - Mark notification as read
- `POST /notifications/mark-all-read` - Mark all as read
- `POST /notifications/create` - Create notification (admin)

### Authentication Flow
1. User logs in via SSO
2. SSO token verified with `/sso/verify`
3. JWT token issued for API access
4. Token included in Authorization header: `Bearer {token}`
5. Permissions checked per endpoint based on user role

## Database Schema

### Core Tables
- `users` - System users synced from SSO
- `applications` - Main application records (L2 ID unique)
- `sub_tasks` - Detailed tasks per application
- `audit_logs` - Complete change history

### Key Relationships
- Application → SubTasks (1:N)
- User → Applications (created_by, updated_by)
- All tables → AuditLogs (polymorphic)

## Environment Variables

Required in `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost/akcn_db
REDIS_URL=redis://localhost:6379
SSO_BASE_URL=https://sso.company.com
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

## Common Development Tasks

### Adding a New Endpoint
1. Create schema in `app/schemas/`
2. Add endpoint in `app/api/v1/endpoints/`
3. Implement service logic in `app/services/`
4. Add tests in `tests/api/`
5. Update API documentation

### Modifying Database Schema
1. Update model in `app/models/`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration
4. Apply: `alembic upgrade head`
5. Update related schemas and services

### Excel Import/Export Format
- Main sheet: Application list with L2 ID as key
- Detail sheet: Subtasks linked by L2 ID
- Date format: YYYY-MM-DD
- Status values must match enum definitions
- UTF-8 encoding for Chinese characters

## Development Work Plan

### Phase 1: Project Foundation (✅ Completed)
- ✅ Project setup and architecture design
- ✅ Database schema design with PostgreSQL
- ✅ API specification and FastAPI framework setup
- ✅ CORS configuration for frontend integration

### Phase 2: Core Backend Features (✅ Completed)

#### T2.1 SSO Authentication Integration (✅ Completed)
**Implemented:**
- ✅ JWT token validation with test token support
- ✅ Authentication middleware and dependencies
- ✅ User role-based access control (Admin/Manager/Editor/Viewer)
- ✅ Permission checking decorators and utilities
- ✅ Authentication endpoints (/auth/login, /auth/me, /auth/permissions)

#### T2.2 Application Management Module (✅ Completed)
**Implemented:**
- ✅ Complete CRUD APIs for applications with async SQLAlchemy
- ✅ Advanced filtering and pagination support
- ✅ L2 ID uniqueness constraint and validation
- ✅ Application status calculation based on subtasks
- ✅ Bulk operations and status recalculation
- ✅ Team-based and delayed application queries

#### T2.3 Subtask Management Module (✅ Completed)
**Implemented:**
- ✅ Subtask CRUD operations with proper validation
- ✅ Batch status updates and progress calculation
- ✅ Task assignment and user task queries
- ✅ Status-based filtering and date validation
- ✅ Real-time progress updates triggering application recalculation

#### T2.4 Auto-Calculation Engine (✅ Completed)
**Implemented:**
- ✅ Automatic status aggregation from subtasks
- ✅ Progress percentage calculation algorithms
- ✅ Delay days calculation based on planned vs actual dates
- ✅ Application status rollup (待启动 → 研发进行中 → 业务上线中 → 全部完成)
- ✅ Async calculation service endpoints

#### T2.5 Audit Log System (✅ Completed)
**Implemented:**
- ✅ Comprehensive audit logging for all data changes
- ✅ Audit log query APIs with filtering
- ✅ Data rollback functionality (basic structure)
- ✅ Unlimited audit log retention
- ✅ User action tracking and request correlation

### Phase 3: Extended Features (✅ Completed)

#### T3.1 Excel Import/Export (✅ Completed)
**Implemented:**
- ✅ OpenPyXL integration for Excel processing
- ✅ Application and subtask import from Excel
- ✅ Direct Excel file export (no intermediate file URLs)
- ✅ Template generation for import formats
- ✅ File validation and preview functionality
- ✅ Import history tracking and health monitoring

#### T3.2 Dashboard & Analytics (✅ Completed)
**Implemented:**
- ✅ Dashboard statistics with real database queries
- ✅ Progress trend analysis over time
- ✅ Department distribution and comparison
- ✅ Real-time data aggregation without mock data

#### T3.3 Report Generation System (✅ Completed)
**Implemented:**
- ✅ Progress summary reports with filtering
- ✅ Delayed projects report with threshold configuration
- ✅ Department performance comparison
- ✅ Export functionality integrated with Excel service

#### T3.4 Notification Service (✅ Completed)
**Implemented:**
- ✅ User notification system with CRUD operations
- ✅ Notification reading status management
- ✅ Bulk notification operations
- ✅ Basic notification structure for future extensions

### Phase 4: Technical Excellence (✅ Completed)

#### T4.1 Database & Performance (✅ Completed)
**Implemented:**
- ✅ Complete PostgreSQL migration with async support
- ✅ Proper connection pooling and session management
- ✅ SQLAlchemy async patterns and greenlet error fixes
- ✅ Hybrid properties for calculated fields
- ✅ Database initialization with comprehensive test data

#### T4.2 API Consistency & Standards (✅ Completed)
**Implemented:**
- ✅ Consistent API parameter naming (app_id, task_id)
- ✅ Standardized response formats across all endpoints
- ✅ Proper HTTP status codes and error handling
- ✅ FastAPI automatic API documentation (/docs)
- ✅ Production-ready server alignment

### Current Status: Production Ready ✅

**System Features:**
- Complete CRUD operations for all entities
- Real-time progress calculation and status updates
- Advanced filtering, pagination, and sorting
- Excel import/export with direct file handling
- Dashboard analytics with live database queries
- Comprehensive audit logging and rollback capability
- Role-based access control and JWT authentication
- PostgreSQL with async operations and proper connection management

### Performance Targets
- Page load time <3sec
- API response time 95% <2sec
- Support 500+ concurrent users
- System availability >99.5%
- Database connections <100
- Memory usage <80%

## Database Setup Instructions

### Prerequisites
- PostgreSQL 14+ installed and running
- Python 3.8+ environment

### Initial Setup
```bash
# Initialize PostgreSQL database with test data
python setup_postgresql_complete.py

# Or use the basic initialization script
python init_db.py

# Run database migrations (if using Alembic)
alembic upgrade head
```

### Configuration
Update `.env` file with your database credentials:
```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/akcn_db
```

## Critical Implementation Notes

### SQLAlchemy Async Patterns
- Always use `datetime.now(timezone.utc)` instead of `datetime.utcnow()` to avoid greenlet errors
- Import all models in `app/main.py` to prevent lazy loading issues
- Use explicit database queries instead of relationship lazy loading in async context
- Hybrid properties should check for loaded relationships to avoid N+1 queries

### API Parameter Consistency
- Use `{app_id}` instead of `{application_id}` for application endpoints
- Use `{task_id}` for subtask endpoints
- Follow RESTful conventions for all endpoints

### Excel File Handling
- Return actual file content with proper MIME type instead of file URLs
- Use `Response` with `Content-Disposition` headers for downloads
- Process Excel files in memory using `openpyxl` and `io.BytesIO`

### Production Deployment Requirements
- FastAPI 0.104+
- PostgreSQL 14+ with asyncpg driver
- Redis 7.0+ (for future caching needs)
- OpenPyXL for Excel processing
- Uvicorn or Gunicorn with uvicorn workers
- Proper CORS configuration for frontend integration

### Testing & Development
- Use the standalone `production_server.py` for quick testing with in-memory data
- Main application connects to PostgreSQL database
- All endpoints support real data operations without mock responses