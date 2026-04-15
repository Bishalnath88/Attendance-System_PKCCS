"""
Database Migration Script
Adds missing columns to existing database tables
Run this once to update your production database
"""

import os
import sys
from pathlib import Path
import mysql.connector

# Load environment variables
def load_env_file():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

load_env_file()

def get_db_config():
    return {
        "host": os.environ.get("ATTENDANCE_DB_HOST", "localhost"),
        "user": os.environ.get("ATTENDANCE_DB_USER", "root"),
        "password": os.environ.get("ATTENDANCE_DB_PASSWORD"),
        "database": os.environ.get("ATTENDANCE_DB_NAME", "attendance_system"),
        "port": int(os.environ.get("ATTENDANCE_DB_PORT", "3306")),
    }

def migrate_database():
    """Add admission_year column to students table if it doesn't exist"""
    conn = cursor = None
    try:
        conn = mysql.connector.connect(**get_db_config())
        cursor = conn.cursor(dictionary=True)
        
        # Check if admission_year column exists
        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME='students' AND COLUMN_NAME='admission_year'"
        )
        
        if cursor.fetchone():
            print("✓ admission_year column already exists")
            return True
        
        print("Adding admission_year column to students table...")
        
        # Add the admission_year column
        cursor.execute(
            "ALTER TABLE students ADD COLUMN admission_year INT DEFAULT 2026 AFTER semester"
        )
        
        # Add index on admission_year
        cursor.execute(
            "CREATE INDEX idx_admission_year ON students(admission_year)"
        )
        
        conn.commit()
        print("✓ Successfully added admission_year column")
        print("✓ Successfully created index on admission_year")
        
        # Show table structure
        cursor.execute("DESCRIBE students")
        columns = cursor.fetchall()
        print("\nUpdated table structure:")
        for col in columns:
            print(f"  - {col['Field']}: {col['Type']}")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    
    if migrate_database():
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
