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
│   │   └── v1/
│   │       ├── endpoints/     # API endpoints
│   │       │   ├── applications.py
│   │       │   ├── subtasks.py
│   │       │   ├── auth.py
│   │       │   ├── audit.py
│   │       │   └── reports.py
│   │       └── api.py        # API router aggregation
│   ├── core/
│   │   ├── config.py         # Settings and configuration
│   │   ├── security.py       # JWT and security utilities
│   │   └── database.py       # Database connection
│   ├── models/               # SQLAlchemy models
│   │   ├── application.py
│   │   ├── subtask.py
│   │   ├── user.py
│   │   └── audit_log.py
│   ├── schemas/              # Pydantic schemas
│   │   ├── application.py
│   │   ├── subtask.py
│   │   └── auth.py
│   ├── services/             # Business logic
│   │   ├── application_service.py
│   │   ├── subtask_service.py
│   │   ├── audit_service.py
│   │   └── sso_service.py
│   ├── middleware/           # Custom middleware
│   │   ├── auth.py
│   │   └── logging.py
│   └── main.py              # FastAPI app initialization
├── tests/
├── alembic/                  # Database migrations
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
- `POST /sso/verify` - Verify SSO token
- `GET /applications` - List applications (paginated, filterable)
- `POST /applications` - Create application
- `PUT /applications/{id}` - Update application
- `GET /subtasks` - List subtasks
- `PUT /subtasks/{id}` - Update subtask (triggers status recalc)
- `POST /subtasks/batch-update` - Batch update subtasks
- `GET /audit/logs` - View audit trail
- `POST /audit/rollback/{log_id}` - Rollback changes
- `GET /reports/export` - Export to Excel
- `POST /batch/import` - Import Excel data

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

### Phase 1: Project Foundation (Completed)
- ✅ Project setup and architecture design
- ✅ Database schema design
- ✅ API specification

### Phase 2: Core Backend Features (High Priority)

#### T2.1 SSO Authentication Integration (5 days)
**Deliverables:**
- SSO SDK integration with JWT token validation
- Authentication middleware with <100ms response time
- User info synchronization from SSO system
- RBAC permission mapping (Admin/Manager/Editor/Viewer)
- Redis-based session management
- Token refresh mechanism with error handling

**Acceptance Criteria:**
- SSO login success rate >99%
- Token validation response time <100ms
- Accurate permission control
- Automatic session timeout handling

#### T2.2 Application Management Module (8 days)
**Deliverables:**
- Complete CRUD APIs for applications
- Advanced query optimization with proper indexing
- Data validation for all required fields
- Optimistic locking for concurrent updates
- Pagination, filtering, and sorting support

**Acceptance Criteria:**
- List loading time <2sec (1000 records)
- L2 ID uniqueness constraint enforced
- Full data validation coverage
- No data conflicts in concurrent updates

#### T2.3 Subtask Management Module (7 days)
**Deliverables:**
- Subtask CRUD operations
- Batch status update (100+ records)
- Progress percentage calculation
- Block status management
- Date validation logic

**Acceptance Criteria:**
- Batch update supports 100+ records
- Progress calculation 100% accuracy
- Real-time status updates

#### T2.4 Auto-Calculation Engine (6 days)
**Deliverables:**
- Database triggers for status aggregation
- Status rollup algorithms
- Weighted progress calculation
- Delay days calculation
- Async task queue (Celery) integration

**Acceptance Criteria:**
- Trigger response time <500ms
- 100% calculation accuracy
- Supports 1000+ subtask aggregation

#### T2.5 Audit Log System (5 days)
**Deliverables:**
- Automatic operation logging
- JSON diff for change tracking
- Audit log query APIs
- Data rollback functionality
- Log archival strategy

**Acceptance Criteria:**
- 100% data change recording
- 90-day rollback capability
- Log query response <1sec
- Unlimited storage (no 1000 record limit)

### Phase 3: Extended Features

#### T3.1 Excel Import/Export (7 days)
**Deliverables:**
- OpenPyXL integration
- Template parsing engine
- Data mapping configuration
- Batch data validation
- Error reporting with cell-level precision
- Large file chunked processing

**Acceptance Criteria:**
- Supports 10MB+ files
- 10,000 rows import <30sec
- Precise error location to cell
- Export format matches original Excel

#### T3.2 Report Generation System (6 days) - Medium Priority
**Deliverables:**
- Progress summary reports
- Department comparison reports
- Delayed project reports
- Trend analysis charts
- Custom report configuration

**Acceptance Criteria:**
- Report generation <5sec
- PDF/Excel export support
- Smooth chart interactions

#### T3.3 Notification Service (5 days) - Medium Priority
**Deliverables:**
- Delay warning notifications (Email/Internal)
- Status change notifications
- Periodic progress reports
- Custom rule configuration

**Acceptance Criteria:**
- Notification delay <1min
- Email delivery rate >95%
- Batch notification support

### Phase 4: Testing & Quality Assurance

#### T4.1 Unit Testing (5 days)
**Deliverables:**
- 100% API endpoint coverage
- Business logic tests
- Data validation tests
- Exception handling tests

**Acceptance Criteria:**
- Code coverage >80%
- All P0 defects fixed
- 100% test case pass rate

### Performance Targets
- Page load time <3sec
- API response time 95% <2sec
- Support 500+ concurrent users
- System availability >99.5%
- Database connections <100
- Memory usage <80%

### Implementation Priority Order
1. **Phase 2 (Core)**: T2.1 → T2.2 → T2.3 → T2.4 → T2.5
2. **Phase 3 (Extended)**: T3.1 → T3.2 → T3.3
3. **Phase 4 (Testing)**: T4.1

### Key Technical Dependencies
- FastAPI 0.104+
- PostgreSQL 14+
- Redis 7.0+
- Docker 20+ / Kubernetes 1.25+
- Celery for async tasks
- OpenPyXL for Excel processing