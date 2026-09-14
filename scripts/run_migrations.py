#!/usr/bin/env python3
"""
Run database migrations.

Reads .sql files from migrations/ and executes them in order.
Tracks applied migrations in schema_migrations to prevent re-execution.
Creates the database if it does not exist.

Usage:
    python scripts/run_migrations.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import mysql.connector
from mysql.connector import Error

from app.config import settings


def validate_db_name(name: str) -> str:
    """Validate database name to prevent SQL injection."""
    if not name or not name.strip():
        raise ValueError("Database name cannot be empty")
    if not re.match(r"^[A-Za-z0-9_]+$", name):
        raise ValueError(
            f"Invalid database name '{name}'. "
            "Only alphanumeric characters and underscores are allowed."
        )
    if len(name) > 64:
        raise ValueError(f"Database name '{name}' exceeds 64 characters")
    return name


def get_server_connection():
    """Connect to MySQL server without specifying a database."""
    return mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        charset="utf8mb4",
        autocommit=False,
    )


def create_database_if_not_exists(connection, db_name: str) -> None:
    """Create the database if it doesn't exist."""
    validated_name = validate_db_name(db_name)
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{validated_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        connection.commit()
        print(f"Database '{validated_name}' ready")
    except Error as exc:
        print(f"Error creating database: {exc}")
        raise
    finally:
        cursor.close()


def get_connection(db_name: str):
    """Get a database connection to a specific database."""
    return mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=db_name,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        autocommit=False,
    )


def ensure_schema_migrations_table(cursor):
    """Ensure the schema_migrations table exists."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)


def get_applied_migrations(cursor) -> set[str]:
    """Get set of already applied migration filenames."""
    cursor.execute("SELECT filename FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def record_migration(cursor, filename: str):
    """Record a migration as applied."""
    cursor.execute(
        "INSERT INTO schema_migrations (filename) VALUES (%s)",
        (filename,),
    )


def get_migration_files() -> list[Path]:
    """Get sorted list of migration files."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        return []
    return sorted(migrations_dir.glob("*.sql"))


def strip_sql_comments(sql_content: str) -> str:
    """Remove SQL comments from content before processing."""
    lines = []
    for line in sql_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if "--" in line:
            line = line[: line.index("--")]
        lines.append(line)
    return "\n".join(lines)


def run_migration(cursor, conn, filepath: Path):
    """Execute a migration file. Idempotent — safe to run multiple times."""
    print(f"  Running: {filepath.name}")

    sql = filepath.read_text(encoding="utf-8")
    cleaned_sql = strip_sql_comments(sql)
    statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]

    for statement in statements:
        if not statement:
            continue
        try:
            cursor.execute(statement)
            try:
                if getattr(cursor, "with_rows", False):
                    cursor.fetchall()
                while cursor.nextset():
                    if getattr(cursor, "with_rows", False):
                        cursor.fetchall()
            except Exception:
                pass
            conn.commit()
        except Error as e:
            error_msg = str(e).lower()
            is_expected = (
                e.errno == 1050
                or e.errno == 1060
                or e.errno == 1061
                or e.errno == 1062
                or e.errno == 1091
                or e.errno == 1826
                or e.errno == 1022
                or e.errno == 1068
                or e.errno == 1121
                or e.errno == 1557
                or "already exists" in error_msg
                or "duplicate" in error_msg
            )
            if is_expected:
                print(f"    Skipped (already applied): {statement[:60]}...")
                conn.rollback()
            else:
                print(f"    Failed: {statement[:100]}...")
                conn.rollback()
                raise


def main():
    """Run all pending migrations."""
    print("Order Management System - Database Migrations")
    print("=" * 50)

    db_name = settings.DB_NAME
    try:
        db_name = validate_db_name(db_name)
    except ValueError as exc:
        print(f"Invalid DB_NAME in environment: {exc}")
        sys.exit(1)

    migration_files = get_migration_files()
    if not migration_files:
        print("No migration files found.")
        return

    print(f"Found {len(migration_files)} migration file(s)")
    print(f"Target database: {db_name}")
    print("Creating the database if it does not already exist...")

    try:
        server_conn = get_server_connection()
        create_database_if_not_exists(server_conn, db_name)
        server_conn.close()
    except Error as e:
        print(f"Failed to create database: {e}")
        sys.exit(1)

    try:
        conn = get_connection(db_name)
        cursor = conn.cursor()
        print(f"Connected to database: {db_name}")
    except Error as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        ensure_schema_migrations_table(cursor)
        conn.commit()

        applied = get_applied_migrations(cursor)
        print(f"Already applied: {len(applied)} migration(s)")

        pending = [f for f in migration_files if f.name not in applied]

        if not pending:
            print("\nNo pending migrations. Database is up to date.")
            return

        print(f"\nPending migrations: {len(pending)}")

        for filepath in pending:
            run_migration(cursor, conn, filepath)
            record_migration(cursor, filepath.name)
            conn.commit()
            print(f"  Applied: {filepath.name}")

        print(f"\nSuccessfully applied {len(pending)} migration(s)")

    except Error as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        sys.exit(1)
    except Exception as exc:
        conn.rollback()
        print(f"\nUnexpected error: {exc}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed")


if __name__ == "__main__":
    main()
