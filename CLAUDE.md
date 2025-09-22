# CLAUDE.md - AKCN Project Management System Backend

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AK Cloud Native Transformation Management System - Backend API Service**

A production-ready FastAPI-based backend for managing enterprise application transformation from traditional architecture to AK/Cloud Native platforms. The system provides comprehensive tracking of transformation progress across multiple applications and their subtasks, with real-time status calculation, comprehensive audit logging, and role-based access control.

## Tech Stack

### Core Technologies
- **Framework**: FastAPI 0.115+ (Python 3.8+)
- **Database**: PostgreSQL 14+ (primary) with asyncpg driver
- **Cache**: Redis 5.2+ (optional, for performance optimization)
- **ORM**: SQLAlchemy 2.0+ with async support
- **Migration**: Alembic 1.14+
- **Authentication**: JWT tokens with SSO integration support

### Development & Testing
- **Testing**: pytest 8.3+ with pytest-asyncio
- **Code Quality**: black, isort, flake8, mypy
- **API Documentation**: Auto-generated OpenAPI/Swagger (/docs)
- **Excel Processing**: openpyxl 3.1+, pandas 2.2+

## Quick Start

### Prerequisites
1. Python 3.8 or higher
2. PostgreSQL 14+ installed and running
3. Git for version control
4. Virtual environment tool (venv/virtualenv)

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd AKCNBackEnd

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL database with test data
python setup_postgresql.py

# Or setup without test data
python setup_postgresql.py --no-data

# Create .env file from example
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://akcn_user:akcn_password@localhost:5432/akcn_dev_db
DB_HOST=localhost
DB_PORT=5432
DB_USER=akcn_user
DB_PASSWORD=akcn_password
DB_NAME=akcn_dev_db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# SSO (if using)
SSO_BASE_URL=https://sso.company.com
SSO_CLIENT_ID=your-client-id
SSO_CLIENT_SECRET=your-client-secret

# Application
APP_NAME=AKCN Project Management
APP_VERSION=1.0.0
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server (Windows/Linux)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Access API documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

## Project Structure

```
AKCNBackEnd/
├── app/                        # Main application package
│   ├── api/                    # API layer
│   │   ├── deps.py            # Dependency injection (auth, db, etc.)
│   │   └── v1/                # API version 1
│   │       ├── endpoints/     # API endpoints
│   │       │   ├── applications.py    # Application CRUD & management
│   │       │   ├── subtasks.py       # SubTask CRUD & batch operations
│   │       │   ├── auth.py           # Authentication & authorization
│   │       │   ├── audit.py          # Audit log & rollback
│   │       │   ├── calculation.py    # Progress calculation service
│   │       │   ├── dashboard.py      # Dashboard statistics & analytics
│   │       │   ├── excel.py          # Excel import/export operations
│   │       │   ├── notifications.py  # User notifications
│   │       │   └── reports.py        # Report generation
│   │       └── api.py         # API router aggregation
│   ├── core/                  # Core configuration & utilities
│   │   ├── config.py         # Settings management (pydantic-settings)
│   │   ├── database.py       # Database configuration
│   │   ├── exceptions.py     # Custom exception classes
│   │   └── security.py       # JWT & security utilities
│   ├── db/                    # Database layer
│   │   └── session.py        # Async session management
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── __init__.py       # Model exports
│   │   ├── base.py           # Base model with timestamps
│   │   ├── application.py    # Application model
│   │   ├── subtask.py        # SubTask model
│   │   ├── user.py           # User model with roles
│   │   ├── audit_log.py      # Audit logging model
│   │   └── notification.py   # Notification model
│   ├── schemas/               # Pydantic validation schemas
│   │   ├── application.py    # Application DTOs
│   │   ├── subtask.py        # SubTask DTOs
│   │   ├── auth.py           # Authentication DTOs
│   │   ├── audit.py          # Audit log DTOs
│   │   ├── dashboard.py      # Dashboard DTOs
│   │   ├── excel.py          # Excel operation DTOs
│   │   ├── notification.py   # Notification DTOs
│   │   └── reports.py        # Report DTOs
│   ├── services/              # Business logic layer
│   │   ├── application_service.py    # Application business logic
│   │   ├── subtask_service.py       # SubTask business logic
│   │   ├── calculation_service.py   # Progress calculation algorithms
│   │   ├── excel_service.py         # Excel processing logic
│   │   ├── audit_service.py         # Audit operations
│   │   ├── notification_service.py  # Notification management
│   │   ├── reports_service.py       # Report generation
│   │   └── sso_service.py           # SSO integration
│   └── main.py               # FastAPI app initialization
├── tests/                     # Test suite
│   ├── conftest.py           # Pytest fixtures
│   ├── test_applications.py  # Application tests
│   ├── test_subtasks.py      # SubTask tests
│   ├── test_auth.py          # Authentication tests
│   ├── test_calculation.py   # Calculation tests
│   └── test_excel.py         # Excel operations tests
├── alembic/                   # Database migrations
│   ├── versions/             # Migration files
│   ├── alembic.ini          # Alembic configuration
│   └── env.py               # Migration environment
├── docs/                      # Documentation
│   ├── API.md               # API documentation
│   ├── DEPLOYMENT.md        # Deployment guide
│   ├── DEVELOPMENT.md       # Developer guide
│   └── TESTING.md           # Testing guide
├── scripts/                   # Utility scripts
│   ├── backup_db.py         # Database backup
│   └── restore_db.py        # Database restore
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── setup_postgresql.py      # Database setup script
├── production_server.py     # Standalone test server
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker compose configuration
└── README.md               # Project readme
```

## Core Features & Business Logic

### 1. Application Management
- **CRUD Operations**: Full create, read, update, delete for applications
- **Status Tracking**: Automatic status calculation based on subtask progress
- **Progress Calculation**: Real-time percentage calculation from subtasks
- **Delay Detection**: Automatic detection and calculation of delays
- **Bulk Operations**: Batch status recalculation for multiple applications

### 2. SubTask Management
- **Hierarchical Structure**: Tasks linked to parent applications
- **Status Workflow**: NOT_STARTED → REQUIREMENT_ANALYSIS → DEV_IN_PROGRESS → TESTING → TECH_ONLINE → BIZ_ONLINE → COMPLETED
- **Progress Tracking**: Individual task progress contributes to application progress
- **Batch Updates**: Update multiple subtasks in single operation
- **Assignment Management**: Track assigned users and reviewers

### 3. Authentication & Authorization
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**:
  - **Admin**: Full system access, all operations
  - **Manager**: Department-level management, can edit/view
  - **Editor**: Can edit assigned applications and tasks
  - **Viewer**: Read-only access to all data
- **SSO Integration**: Support for enterprise SSO systems
- **Test Mode**: Built-in test tokens for development

### 4. Progress Calculation Engine
- **Automatic Calculation**: Real-time progress updates
- **Status Aggregation**:
  - 待启动 (Not Started): All subtasks not started
  - 研发进行中 (Dev In Progress): Any subtask in development
  - 业务上线中 (Biz Online): Some tasks online, others pending
  - 全部完成 (Completed): All subtasks completed
- **Weighted Progress**: Calculate based on task importance/priority
- **Delay Calculation**: Compare planned vs actual dates

### 5. Excel Import/Export
- **Bulk Import**: Import applications and subtasks from Excel
- **Template Generation**: Generate import templates with validation
- **Export Formats**: Multiple export formats (XLSX, CSV)
- **Data Validation**: Pre-import validation and preview
- **Error Handling**: Detailed error reporting for failed imports

### 6. Audit System
- **Complete Audit Trail**: Log all data changes
- **Before/After Values**: Store complete change history
- **User Tracking**: Track user, IP, and user agent
- **Rollback Support**: Revert changes to previous state
- **No Retention Limit**: Keep all audit logs indefinitely

### 7. Dashboard & Analytics
- **Real-time Statistics**: Live data aggregation
- **Progress Trends**: Historical progress analysis
- **Department Distribution**: Compare department performance
- **Delay Analysis**: Identify and analyze delayed projects

### 8. Notification System
- **User Notifications**: Personal notification inbox
- **Notification Types**: INFO, WARNING, ERROR, SUCCESS
- **Read Status**: Track read/unread notifications
- **Bulk Operations**: Mark all as read functionality

## API Reference

### Base URL
```
Development: http://localhost:8000/api/v1
Production: https://your-domain.com/api/v1
```

### Authentication
All API requests (except login) require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

### Main Endpoint Groups

#### Authentication (`/auth`)
```
POST /auth/login              # Login with credentials
POST /auth/sso/verify         # Verify SSO token
POST /auth/refresh            # Refresh JWT token
GET  /auth/me                 # Get current user info
GET  /auth/permissions        # Get user permissions
POST /auth/logout             # Logout (invalidate token)
```

#### Applications (`/applications`)
```
GET    /applications/                    # List all (paginated)
POST   /applications/                    # Create new
GET    /applications/{app_id}           # Get by ID
PUT    /applications/{app_id}           # Update
DELETE /applications/{app_id}           # Delete
GET    /applications/l2/{l2_id}         # Get by L2 ID
GET    /applications/statistics         # Get statistics
GET    /applications/delayed            # Get delayed apps
GET    /applications/team/{team_name}   # Filter by team
POST   /applications/bulk/recalculate   # Bulk recalculate
```

#### SubTasks (`/subtasks`)
```
GET    /subtasks/                  # List all (paginated)
POST   /subtasks/                  # Create new
GET    /subtasks/{task_id}        # Get by ID
PUT    /subtasks/{task_id}        # Update
DELETE /subtasks/{task_id}        # Delete
GET    /subtasks/my-tasks         # User's assigned tasks
POST   /subtasks/batch-update     # Batch update
POST   /subtasks/batch/recalculate # Bulk recalculate
```

#### Dashboard (`/dashboard`)
```
GET /dashboard/stats                      # Summary statistics
GET /dashboard/progress-trend             # Progress over time
GET /dashboard/department-distribution    # By department
GET /dashboard/delayed-summary            # Delayed projects
```

#### Excel Operations (`/excel`)
```
POST /excel/applications/import      # Import applications
POST /excel/subtasks/import         # Import subtasks
POST /excel/export/applications     # Export applications
GET  /excel/subtasks/export         # Export subtasks
GET  /excel/template                # Download template
POST /excel/preview                 # Preview import
POST /excel/validate                # Validate file
GET  /excel/import/history          # Import history
```

#### Reports (`/reports`)
```
GET /reports/progress              # Progress report
GET /reports/delayed               # Delayed projects
GET /reports/department            # Department report
GET /reports/export                # Export report
```

#### Audit (`/audit`)
```
GET  /audit/logs                   # View audit trail
POST /audit/rollback/{log_id}     # Rollback change
GET  /audit/export                 # Export logs
```

#### Notifications (`/notifications`)
```
GET  /notifications/               # Get user notifications
PUT  /notifications/{id}/read      # Mark as read
POST /notifications/mark-all-read  # Mark all read
POST /notifications/create         # Create (admin only)
```

## Database Schema

### Core Tables

#### users
```sql
- id: UUID (PK)
- sso_user_id: String (unique)
- username: String (unique)
- email: String (unique)
- full_name: String
- department: String
- role: Enum (ADMIN, MANAGER, EDITOR, VIEWER)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

#### applications
```sql
- id: UUID (PK)
- l2_id: String (unique, business key)
- app_name: String
- supervision_year: Integer
- transformation_target: Enum (AK, CLOUD_NATIVE)
- is_ak_completed: Boolean
- is_cloud_native_completed: Boolean
- current_stage: String
- overall_status: Enum
- responsible_team: String
- responsible_person: String
- progress_percentage: Float
- planned_*_date: Date (requirement, release, tech_online, biz_online)
- actual_*_date: Date (requirement, release, tech_online, biz_online)
- is_delayed: Boolean
- delay_days: Integer
- notes: Text
- created_by: UUID (FK users.id)
- updated_by: UUID (FK users.id)
- created_at: DateTime
- updated_at: DateTime
```

#### sub_tasks
```sql
- id: UUID (PK)
- application_id: UUID (FK applications.id)
- module_name: String
- sub_target: String
- version_name: String
- task_status: Enum
- progress_percentage: Float
- is_blocked: Boolean
- planned_*_date: Date (requirement, release, tech_online, biz_online)
- actual_*_date: Date (requirement, release, tech_online, biz_online)
- requirements: Text
- technical_notes: Text
- assigned_to: String
- reviewer: String
- priority: Integer (1-5)
- estimated_hours: Integer
- actual_hours: Integer
- created_by: UUID (FK users.id)
- updated_by: UUID (FK users.id)
- created_at: DateTime
- updated_at: DateTime
```

#### audit_logs
```sql
- id: UUID (PK)
- table_name: String
- record_id: UUID
- operation: Enum (INSERT, UPDATE, DELETE)
- old_values: JSONB
- new_values: JSONB
- user_id: UUID (FK users.id)
- user_ip: String
- user_agent: String
- created_at: DateTime
```

#### notifications
```sql
- id: UUID (PK)
- user_id: UUID (FK users.id)
- title: String
- message: Text
- type: Enum (INFO, WARNING, ERROR, SUCCESS)
- is_read: Boolean
- read_at: DateTime
- created_at: DateTime
```

### Relationships
- Application ↔ SubTasks: One-to-Many
- User ↔ Applications: Many-to-Many (created_by, updated_by)
- User ↔ SubTasks: Many-to-Many (created_by, updated_by, assigned_to)
- All tables → AuditLogs: Polymorphic relationship

## Development Guidelines

### Code Standards
1. **Python Style**: Follow PEP 8, use black formatter
2. **Type Hints**: Use type hints for all functions
3. **Docstrings**: Document all classes and public methods
4. **Imports**: Sort with isort, group by standard/third-party/local
5. **Async/Await**: Use async patterns consistently

### API Design Principles
1. **RESTful**: Follow REST conventions
2. **Consistent Naming**: Use snake_case for Python, camelCase for JSON
3. **Error Handling**: Return appropriate HTTP status codes
4. **Pagination**: Use limit/offset pattern
5. **Filtering**: Support query parameters for filtering

### Database Best Practices
1. **Migrations**: Always use Alembic for schema changes
2. **Indexes**: Add indexes for frequently queried columns
3. **Transactions**: Use transactions for multi-table updates
4. **Connection Pooling**: Configure appropriate pool size
5. **Async Queries**: Use async SQLAlchemy patterns

### Testing Requirements
1. **Unit Tests**: Cover all service methods
2. **Integration Tests**: Test API endpoints
3. **Test Coverage**: Maintain >80% coverage
4. **Fixtures**: Use pytest fixtures for test data
5. **Mocking**: Mock external dependencies

### Security Considerations
1. **Authentication**: Always validate JWT tokens
2. **Authorization**: Check permissions for each endpoint
3. **Input Validation**: Use Pydantic for all inputs
4. **SQL Injection**: Use parameterized queries
5. **Secrets**: Never commit secrets to repository

## Common Development Tasks

### Adding a New Endpoint
```python
# 1. Create Pydantic schema (app/schemas/feature.py)
class FeatureCreate(BaseModel):
    name: str
    description: Optional[str]

# 2. Add endpoint (app/api/v1/endpoints/feature.py)
@router.post("/", response_model=FeatureResponse)
async def create_feature(
    feature: FeatureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await FeatureService.create(db, feature, current_user)

# 3. Implement service (app/services/feature_service.py)
class FeatureService:
    @staticmethod
    async def create(db: AsyncSession, data: FeatureCreate, user: User):
        # Business logic here
        pass

# 4. Add tests (tests/test_feature.py)
async def test_create_feature(client, auth_headers):
    response = await client.post(
        "/api/v1/features/",
        json={"name": "Test"},
        headers=auth_headers
    )
    assert response.status_code == 200
```

### Database Migration
```bash
# Create migration after model changes
alembic revision --autogenerate -m "Add feature table"

# Review generated migration
# Edit alembic/versions/xxx_add_feature_table.py if needed

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_applications.py

# Run specific test
pytest tests/test_applications.py::test_create_application

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v
```

## Deployment

### Production Checklist
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure production database
- [ ] Set DEBUG=False in .env
- [ ] Configure CORS for production domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up database backups
- [ ] Configure rate limiting

### Docker Deployment
```bash
# Build image
docker build -t akcn-backend .

# Run container
docker run -d \
  --name akcn-backend \
  -p 8000:8000 \
  --env-file .env \
  akcn-backend

# Using docker-compose
docker-compose up -d
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start with gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring & Maintenance

### Health Checks
- `/health` - Basic health check
- `/health/db` - Database connectivity
- `/health/redis` - Redis connectivity (if configured)

### Logging
- Application logs: `logs/app.log`
- Access logs: `logs/access.log`
- Error logs: `logs/error.log`

### Performance Metrics
- Response time: Target <2s for 95% requests
- Database connections: Monitor pool usage
- Memory usage: Keep below 80%
- CPU usage: Scale if consistently >70%

### Backup Strategy
- Database: Daily automated backups
- Keep 30 days of backups
- Test restore procedure monthly
- Document restore process

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection settings
psql -h localhost -U akcn_user -d akcn_dev_db

# Verify .env configuration
cat .env | grep DATABASE_URL
```

#### Migration Errors
```bash
# Check current revision
alembic current

# Show migration history
alembic history

# Create missing migration
alembic revision --autogenerate -m "Fix migration"
```

#### Performance Issues
```bash
# Check slow queries
SELECT * FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;

# Check connection pool
SELECT count(*) FROM pg_stat_activity;

# Monitor memory usage
python -m memory_profiler app.main
```

## Support & Resources

### Documentation
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

### Development Resources
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- Pytest: https://docs.pytest.org/

### Contact
- Technical Lead: [Your Contact]
- DevOps Team: [DevOps Contact]
- Database Admin: [DBA Contact]

## License

[Your License Information]

---

*Last Updated: December 2024*
*Version: 1.0.0*