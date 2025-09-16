"""
Create PostgreSQL databases and user for AKCN system
"""

import psycopg2
from psycopg2 import sql
import sys
import getpass


def create_databases():
    """Create databases and user for AKCN system."""

    # Get postgres password
    print("============================================================")
    print("PostgreSQL Database Setup for AKCN System")
    print("============================================================")
    print("\nThis script will create the PostgreSQL databases and user.")

    postgres_password = getpass.getpass("Enter postgres user password: ")

    try:
        # Connect to PostgreSQL as postgres user
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=postgres_password,
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
            # Update password
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

        # Connect to development database to create extensions
        cursor.close()
        conn.close()

        print("\nConnecting to akcn_dev_db to create extensions...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=postgres_password,
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

        return True

    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Could not connect to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. The postgres user password is correct")
        print("3. PostgreSQL is listening on localhost:5432")
        return False
    except Exception as e:
        print(f"\n[ERROR] Database setup failed: {e}")
        return False


if __name__ == "__main__":
    if create_databases():
        print("\nNow you can run: python init_postgresql.py")
        sys.exit(0)
    else:
        sys.exit(1)