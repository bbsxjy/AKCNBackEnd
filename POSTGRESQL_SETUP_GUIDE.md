# PostgreSQL Setup Guide for AKCN System

## Manual Database Setup Required

The automatic setup scripts cannot connect to your PostgreSQL server. Please follow these steps to manually create the databases and user.

## Step 1: Open PostgreSQL Command Line

Choose one of these methods:

### Option A: Using psql command line
```bash
psql -U postgres
```

### Option B: Using pgAdmin
1. Open pgAdmin
2. Connect to your PostgreSQL server
3. Right-click on "Databases" → "Query Tool"

### Option C: Using SQL Shell (psql) from Start Menu
1. Open Start Menu
2. Search for "SQL Shell (psql)"
3. Press Enter for defaults, enter postgres password when prompted

## Step 2: Create User and Databases

Run these SQL commands:

```sql
-- Create user
CREATE USER akcn_user WITH PASSWORD 'akcn_password';

-- Create development database
CREATE DATABASE akcn_dev_db
    WITH OWNER = akcn_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8';

-- Create test database
CREATE DATABASE akcn_test_db
    WITH OWNER = akcn_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8';

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE akcn_dev_db TO akcn_user;
GRANT ALL PRIVILEGES ON DATABASE akcn_test_db TO akcn_user;

-- Connect to development database
\c akcn_dev_db

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO akcn_user;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Verify setup
\du  -- List users
\l   -- List databases
```

## Step 3: Verify Connection

After creating the databases, test the connection:

```bash
python simple_pg_setup.py
```

## Step 4: Initialize Database Tables

Once the connection test passes:

```bash
python init_postgresql.py
```

## Step 5: Start the API Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 6: Run Complete Test Suite

```bash
python test_postgresql_api.py
```

## Troubleshooting

### Connection Issues

If you're getting "connection was closed in the middle of operation":

1. **Check PostgreSQL is running:**
   ```bash
   tasklist | findstr postgres
   ```

2. **Check PostgreSQL configuration (postgresql.conf):**
   - Ensure `listen_addresses = '*'` or `listen_addresses = 'localhost'`
   - Default location: `C:\Program Files\PostgreSQL\[version]\data\postgresql.conf`

3. **Check pg_hba.conf:**
   Add these lines if missing:
   ```
   # IPv4 local connections:
   host    all             all             127.0.0.1/32            md5
   host    all             akcn_user       127.0.0.1/32            md5
   ```
   Default location: `C:\Program Files\PostgreSQL\[version]\data\pg_hba.conf`

4. **Restart PostgreSQL after configuration changes:**
   - Windows Services: Restart "postgresql-x64-[version]"
   - Or use: `net stop postgresql-x64-14 && net start postgresql-x64-14`

### Alternative: Use Default postgres Database

If you cannot create new databases, you can temporarily use the default postgres database:

1. Update `.env` file:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:[your_password]@localhost:5432/postgres
   TEST_DATABASE_URL=postgresql+asyncpg://postgres:[your_password]@localhost:5432/postgres
   ```

2. Run initialization:
   ```bash
   python init_postgresql.py
   ```

## Database Connection Details

Once setup is complete:

- **Host:** localhost
- **Port:** 5432
- **User:** akcn_user
- **Password:** akcn_password
- **Development DB:** akcn_dev_db
- **Test DB:** akcn_test_db

## Verification Checklist

- [ ] PostgreSQL service is running
- [ ] User `akcn_user` created
- [ ] Database `akcn_dev_db` created
- [ ] Database `akcn_test_db` created
- [ ] Extensions installed (uuid-ossp, pgcrypto)
- [ ] Connection test passes (`python simple_pg_setup.py`)
- [ ] Tables initialized (`python init_postgresql.py`)
- [ ] API server starts without errors
- [ ] API endpoints respond correctly
- [ ] Frontend can connect without CORS errors