#!/usr/bin/env python3

import mysql.connector
from pathlib import Path
import os
import sys

def load_env_file():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found!")
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
    
    return True

def get_db_config():
    return {
        "host": os.environ.get("ATTENDANCE_DB_HOST", "localhost"),
        "user": os.environ.get("ATTENDANCE_DB_USER", "root"),
        "password": os.environ.get("ATTENDANCE_DB_PASSWORD"),
        "database": os.environ.get("ATTENDANCE_DB_NAME", "railway"),
        "port": int(os.environ.get("ATTENDANCE_DB_PORT", "3306")),
    }

def initialize_database():
    if not load_env_file():
        return False

    config = get_db_config()
    
    print(f"🔄 Connecting to Railway MySQL database...")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   Database: {config['database']}")
    
    conn = cursor = None
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id INT AUTO_INCREMENT PRIMARY KEY,
          email VARCHAR(255) NOT NULL UNIQUE,
          password VARCHAR(255) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Created 'users' table")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          roll VARCHAR(50) NOT NULL UNIQUE,
          class VARCHAR(100) NOT NULL,
          email VARCHAR(255) NOT NULL UNIQUE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_roll (roll),
          INDEX idx_email (email),
          INDEX idx_class (class)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Created 'students' table")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
          id INT AUTO_INCREMENT PRIMARY KEY,
          student_id INT NOT NULL,
          date DATE NOT NULL,
          subject VARCHAR(255) NOT NULL,
          status ENUM('present', 'absent', 'late') NOT NULL DEFAULT 'absent',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
          UNIQUE KEY unique_attendance (student_id, date, subject),
          INDEX idx_date (date),
          INDEX idx_subject (subject),
          INDEX idx_student_id (student_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Created 'attendance' table")
        conn.commit()
        print("\n✨ Database initialization successful!")
        return True
        
    except mysql.connector.Error as err:
        # Handle database-specific errors
        print(f"\n❌ Database Error: {err}")
        return False
    except Exception as err:
        # Handle unexpected errors
        print(f"\n❌ Unexpected Error: {err}")
        return False
    finally:
        # Always close connections
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    """
    Entry point - Run database initialization
    Exit with status code 0 (success) or 1 (failure)
    """
    success = initialize_database()
    sys.exit(0 if success else 1)
