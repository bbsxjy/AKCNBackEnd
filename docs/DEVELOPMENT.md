# Development Guide

This guide provides comprehensive instructions for setting up and working with the AKCN Project Management System backend.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Database Management](#database-management)
6. [Testing](#testing)
7. [Debugging](#debugging)
8. [Common Tasks](#common-tasks)

## Prerequisites

### Required Software
- **Python 3.8+** (3.10 recommended)
- **PostgreSQL 14+**
- **Git**
- **Redis** (optional, for caching)
- **VS Code** or **PyCharm** (recommended IDEs)

### Recommended VS Code Extensions
- Python
- Pylance
- Black Formatter
- SQLTools
- Thunder Client (API testing)
- GitLens

## Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd AKCNBackEnd
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # if available
```

### 4. PostgreSQL Setup

#### Option A: Using Setup Script
```bash
# Full setup with test data
python setup_postgresql.py

# Schema only (no test data)
python setup_postgresql.py --no-data

# Reset existing database
python setup_postgresql.py --reset
```

#### Option B: Manual Setup
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create user and database
CREATE USER akcn_user WITH PASSWORD 'akcn_password';
CREATE DATABASE akcn_dev_db WITH OWNER = akcn_user;
GRANT ALL PRIVILEGES ON DATABASE akcn_dev_db TO akcn_user;
\q
```

### 5. Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Key variables to configure:
DATABASE_URL=postgresql+asyncpg://akcn_user:akcn_password@localhost:5432/akcn_dev_db
JWT_SECRET_KEY=your-secret-key-for-development
DEBUG=True
```

### 6. Run Database Migrations
```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 7. Start Development Server
```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With custom settings
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 8. Verify Installation
- Open http://localhost:8000/docs for API documentation
- Test health endpoint: http://localhost:8000/health
- Login with test credentials:
  - Username: admin@test.com
  - Token: token_1_admin_full_access_test_2024

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... edit files ...

# Run tests
pytest

# Format code
black app/ tests/
isort app/ tests/

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/your-feature-name
```

### 2. Code Review Process
1. Create Pull Request on GitHub/GitLab
2. Ensure all tests pass
3. Request review from team members
4. Address feedback
5. Merge after approval

### 3. Git Commit Convention
Use conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build process or auxiliary tool changes

## Code Standards

### Python Style Guide
```python
# Follow PEP 8
# Use type hints
from typing import List, Optional, Dict
from datetime import datetime

async def process_application(
    app_id: str,
    data: Dict[str, any],
    user_id: Optional[str] = None
) -> ApplicationResponse:
    """
    Process application with given data.

    Args:
        app_id: Application identifier
        data: Application data dictionary
        user_id: Optional user identifier

    Returns:
        ApplicationResponse object

    Raises:
        ValueError: If app_id is invalid
    """
    # Implementation here
    pass
```

### Project Structure Best Practices
```python
# app/api/v1/endpoints/feature.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.feature import FeatureCreate, FeatureResponse
from app.services.feature_service import FeatureService

router = APIRouter()

@router.post("/", response_model=FeatureResponse)
async def create_feature(
    *,
    db: AsyncSession = Depends(deps.get_db),
    feature_in: FeatureCreate,
    current_user = Depends(deps.get_current_user)
) -> FeatureResponse:
    """Create new feature."""
    return await FeatureService.create(db, feature_in, current_user)
```

### Async/Await Patterns
```python
# Correct async pattern
async def get_application_with_tasks(db: AsyncSession, app_id: str):
    # Use async query execution
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.subtasks))
        .where(Application.id == app_id)
    )
    return result.scalar_one_or_none()

# Avoid blocking operations
# Wrong
import time
time.sleep(1)  # Blocks event loop

# Correct
import asyncio
await asyncio.sleep(1)  # Non-blocking
```

## Database Management

### Working with SQLAlchemy Models
```python
# app/models/feature.py
from sqlalchemy import Column, String, Boolean
from app.models.base import Base

class Feature(Base):
    __tablename__ = "features"

    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

    # Add indexes for performance
    __table_args__ = (
        Index('ix_feature_name', 'name'),
    )
```

### Creating Migrations
```bash
# After model changes
alembic revision --autogenerate -m "Add feature table"

# Review generated migration
# Edit alembic/versions/xxx_add_feature_table.py if needed

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Database Queries Best Practices
```python
# Use select() for queries
from sqlalchemy import select

# Efficient query with join
stmt = select(Application).join(SubTask).where(
    SubTask.status == SubTaskStatus.COMPLETED
)
result = await db.execute(stmt)
applications = result.scalars().all()

# Use bulk operations
await db.execute(
    update(Application)
    .where(Application.status == ApplicationStatus.PENDING)
    .values(status=ApplicationStatus.ACTIVE)
)
```

## Testing

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

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Writing Tests
```python
# tests/test_feature.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature import Feature

@pytest.mark.asyncio
async def test_create_feature(
    client: AsyncClient,
    db: AsyncSession,
    admin_token: str
):
    """Test feature creation."""
    response = await client.post(
        "/api/v1/features/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Test Feature"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Feature"

    # Verify in database
    feature = await db.get(Feature, data["id"])
    assert feature is not None
    assert feature.name == "Test Feature"
```

### Test Fixtures
```python
# tests/conftest.py
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.session import async_session

@pytest.fixture
async def db() -> Generator[AsyncSession, None, None]:
    """Create database session for testing."""
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)
```

## Debugging

### Using VS Code Debugger
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--port", "8000"
            ],
            "jinja": true,
            "justMyCode": false
        }
    ]
}
```

### Logging
```python
import logging
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use in code
logger.debug("Processing application: %s", app_id)
logger.info("Application created successfully")
logger.error("Failed to process application", exc_info=True)
```

### Performance Profiling
```python
# Using cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = await expensive_operation()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## Common Tasks

### Adding New API Endpoint
1. Create schema in `app/schemas/`
2. Add model in `app/models/` (if needed)
3. Create service in `app/services/`
4. Add endpoint in `app/api/v1/endpoints/`
5. Include router in `app/api/v1/api.py`
6. Write tests in `tests/`
7. Update API documentation

### Updating Dependencies
```bash
# Update specific package
pip install --upgrade package-name

# Update requirements.txt
pip freeze > requirements.txt

# Or use pip-tools
pip-compile requirements.in
```

### Database Backup and Restore
```bash
# Backup
pg_dump -U akcn_user -d akcn_dev_db > backup.sql

# Restore
psql -U akcn_user -d akcn_dev_db < backup.sql
```

### Running Production Server Locally
```bash
# Using gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using production settings
export ENVIRONMENT=production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Database Connection Issues
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Test connection
psql -h localhost -U akcn_user -d akcn_dev_db

# Check .env file
cat .env | grep DATABASE_URL
```

#### Async Context Errors
```python
# Error: "greenlet_spawn has not been called"
# Solution: Use datetime.now(timezone.utc) instead of datetime.utcnow()

from datetime import datetime, timezone
# Wrong
created_at = datetime.utcnow()
# Correct
created_at = datetime.now(timezone.utc)
```

## Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [DBeaver](https://dbeaver.io/) - Database management
- [pgAdmin](https://www.pgadmin.org/) - PostgreSQL administration

### Learning Resources
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Async Python](https://realpython.com/async-io-python/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/14/orm/tutorial.html)

---
*Last Updated: December 2024*