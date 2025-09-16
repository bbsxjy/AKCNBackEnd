"""
Auto-create PostgreSQL databases and user for AKCN system
Tries common passwords or uses environment variable
"""

import psycopg2
from psycopg2 import sql
import sys
import os


def try_create_databases(password):
    """Try to create databases with given password."""
    try:
        # Connect to PostgreSQL as postgres user
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=password,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'akcn_user'")
        if not cursor.fetchone():
            print("Creating user 'akcn_user'...")
            cursor.execute("CREATE USER akcn_user WITH PASSWORD 'akcn_password'")
            print("[OK] User created")
        else:
            print("[INFO] User 'akcn_user' already exists")
            cursor.execute("ALTER USER akcn_user WITH PASSWORD 'akcn_password'")
            print("[OK] User password updated")

        # Create development database
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'akcn_dev_db'")
        if not cursor.fetchone():
            print("Creating database 'akcn_dev_db'...")
            cursor.execute(sql.SQL("CREATE DATABASE {} WITH OWNER = {}").format(
                sql.Identifier('akcn_dev_db'),
                sql.Identifier('akcn_user')
            ))
            print("[OK] Development database created")
        else:
            print("[INFO] Database 'akcn_dev_db' already exists")

        # Create test database
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'akcn_test_db'")
        if not cursor.fetchone():
            print("Creating database 'akcn_test_db'...")
            cursor.execute(sql.SQL("CREATE DATABASE {} WITH OWNER = {}").format(
                sql.Identifier('akcn_test_db'),
                sql.Identifier('akcn_user')
            ))
            print("[OK] Test database created")
        else:
            print("[INFO] Database 'akcn_test_db' already exists")

        # Grant privileges
        print("Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE akcn_dev_db TO akcn_user")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE akcn_test_db TO akcn_user")
        print("[OK] Privileges granted")

        cursor.close()
        conn.close()

        # Connect to development database to create extensions
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=password,
            database="akcn_dev_db"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Create extensions
        print("Creating extensions...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\"")
        print("[OK] Extensions created")

        # Grant schema permissions
        cursor.execute("GRANT ALL ON SCHEMA public TO akcn_user")
        print("[OK] Schema permissions granted")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError:
        return False
    except Exception as e:
        print(f"Error with password: {e}")
        return False


def main():
    """Main function to create databases."""

    print("============================================================")
    print("PostgreSQL Database Auto-Setup for AKCN System")
    print("============================================================\n")

    # Try environment variable first
    postgres_password = os.environ.get('POSTGRES_PASSWORD')

    if postgres_password:
        print(f"Trying password from POSTGRES_PASSWORD environment variable...")
        if try_create_databases(postgres_password):
            print("\n[SUCCESS] Databases created with environment password!")
            return True

    # Try common passwords
    common_passwords = [
        'postgres',
        'password',
        'admin',
        '123456',
        'root',
        '',  # Empty password
        'postgresql',
        'Password123',
        'Postgres123',
        'postgres123'
    ]

    for pwd in common_passwords:
        print(f"Trying password: {'(empty)' if pwd == '' else '*' * len(pwd)}...")
        if try_create_databases(pwd):
            print("\n" + "=" * 60)
            print("[SUCCESS] PostgreSQL databases created successfully!")
            print("=" * 60)
            print("\nDatabase Details:")
            print("  Development database: akcn_dev_db")
            print("  Test database: akcn_test_db")
            print("  User: akcn_user")
            print("  Password: akcn_password")
            print("  Host: localhost")
            print("  Port: 5432")
            print("\nNow you can run: python init_postgresql.py")
            return True

    print("\n[ERROR] Could not connect to PostgreSQL with common passwords.")
    print("\nPlease try one of these options:")
    print("1. Set POSTGRES_PASSWORD environment variable:")
    print("   set POSTGRES_PASSWORD=yourpassword")
    print("   python auto_create_postgresql_db.py")
    print("\n2. Run the interactive script:")
    print("   python create_postgresql_db.py")
    print("\n3. Manually create databases using psql:")
    print("   psql -U postgres -f setup_postgresql.sql")

    return False


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)