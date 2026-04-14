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
        cursor = conn.cursor(dictionary=True)
        
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
        CREATE TABLE IF NOT EXISTS courses (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100) NOT NULL UNIQUE,
          code VARCHAR(50) NOT NULL UNIQUE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Created 'courses' table")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_semesters (
          id INT AUTO_INCREMENT PRIMARY KEY,
          course_id INT NOT NULL,
          semester INT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
          UNIQUE KEY unique_course_semester (course_id, semester)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Created 'course_semesters' table")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
          id INT AUTO_INCREMENT PRIMARY KEY,
          course_id INT NOT NULL,
          semester INT NOT NULL,
          name VARCHAR(255) NOT NULL,
          code VARCHAR(50),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
          UNIQUE KEY unique_paper (course_id, semester, name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Created 'papers' table")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          roll VARCHAR(50) NOT NULL UNIQUE,
          course_id INT NOT NULL,
          semester INT NOT NULL,
          papers JSON,
          email VARCHAR(255) NOT NULL UNIQUE,
          phone VARCHAR(20),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
          INDEX idx_roll (roll),
          INDEX idx_email (email),
          INDEX idx_course_id (course_id),
          INDEX idx_semester (semester)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Created 'students' table")
        
        # Check and add missing columns to students table
        columns_to_check = {
            'course_id': 'ALTER TABLE students ADD COLUMN course_id INT NOT NULL DEFAULT 1, ADD FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT',
            'semester': 'ALTER TABLE students ADD COLUMN semester INT NOT NULL DEFAULT 1',
            'papers': 'ALTER TABLE students ADD COLUMN papers JSON',
            'phone': 'ALTER TABLE students ADD COLUMN phone VARCHAR(20)'
        }
        
        for col_name, alter_query in columns_to_check.items():
            cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'students' AND COLUMN_NAME = %s
            """, (col_name,))
            if not cursor.fetchone():
                try:
                    cursor.execute(alter_query)
                    print(f"✅ Added '{col_name}' column to students table")
                except Exception as e:
                    print(f"⚠️  Could not add '{col_name}' column: {str(e)}")
            else:
                print(f"ℹ️  '{col_name}' column already exists in students table")
        
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
        
        # Insert sample courses
        cursor.execute("SELECT COUNT(*) as count FROM courses")
        if cursor.fetchone()['count'] == 0:
            sample_courses = [
                ("Bachelor of Science", "BSc"),
                ("Bachelor of Computer Applications", "BCA"),
                ("Bachelor of Vocational Studies - Information Technology", "Bvoc IT"),
                ("Bachelor of Vocational Studies - Food Technology", "Bvoc Food"),
            ]
            cursor.executemany(
                "INSERT INTO courses (name, code) VALUES (%s, %s)",
                sample_courses
            )
            print("✅ Inserted sample courses")
        
        # Get course IDs for inserting semesters and papers
        cursor.execute("SELECT id, name FROM courses ORDER BY name")
        courses = {row['name']: row['id'] for row in cursor.fetchall()}
        
        # Insert sample semesters for each course
        for course_name, course_id in courses.items():
            cursor.execute(
                "SELECT COUNT(*) as count FROM course_semesters WHERE course_id = %s",
                (course_id,)
            )
            if cursor.fetchone()['count'] == 0:
                semesters = [(course_id, i) for i in range(1, 9)]
                cursor.executemany(
                    "INSERT INTO course_semesters (course_id, semester) VALUES (%s, %s)",
                    semesters
                )
        print("✅ Inserted sample semesters (1-8 for each course)")
        
        # Insert sample papers
        sample_papers = {
            "Bachelor of Science": {
                1: [("Physics I", "PHY101"), ("Chemistry I", "CHE101"), ("Mathematics I", "MAT101"), ("English", "ENG101")],
                2: [("Physics II", "PHY102"), ("Chemistry II", "CHE102"), ("Mathematics II", "MAT102"), ("Computer Science Basics", "CS101")],
                3: [("Thermodynamics", "PHY201"), ("Organic Chemistry", "CHE201"), ("Linear Algebra", "MAT201"), ("Data Structures", "CS201")],
                4: [("Quantum Mechanics", "PHY301"), ("Physical Chemistry", "CHE301"), ("Calculus", "MAT301"), ("Algorithms", "CS301")],
            },
            "Bachelor of Computer Applications": {
                1: [("Programming Fundamentals", "CS101"), ("Digital Logic", "CS102"), ("Mathematics I", "MAT101"), ("English", "ENG101")],
                2: [("Object Oriented Programming", "CS201"), ("Database Management", "CS202"), ("Web Technologies", "CS203"), ("Data Structures", "CS204")],
                3: [("Web Development", "CS301"), ("Software Engineering", "CS302"), ("Network Security", "CS303"), ("Cloud Computing", "CS304")],
                4: [("AI and Machine Learning", "CS401"), ("DevOps", "CS402"), ("Capstone Project", "CS403"), ("Professional Ethics", "CS404")],
            },
            "Bachelor of Vocational Studies - Information Technology": {
                1: [("IT Fundamentals", "IT101"), ("Hardware Basics", "IT102"), ("Networking I", "IT103"), ("Communication Skills", "COM101")],
                2: [("Software Installation", "IT201"), ("System Administration", "IT202"), ("Networking II", "IT203"), ("Database Basics", "IT204")],
                3: [("IT Support", "IT301"), ("Security Essentials", "IT302"), ("Cloud Services", "IT303"), ("Project Management", "PM301")],
                4: [("Virtualization", "IT401"), ("Enterprise IT", "IT402"), ("Internship & Capstone", "IT403"), ("Industry Exposure", "IT404")],
            },
            "Bachelor of Vocational Studies - Food Technology": {
                1: [("Food Science Basics", "FT101"), ("Food Safety", "FT102"), ("Nutrition I", "FT103"), ("Communication Skills", "COM101")],
                2: [("Food Processing", "FT201"), ("Quality Control", "FT202"), ("Nutrition II", "FT203"), ("Food Analysis", "FT204")],
                3: [("Advanced Processing", "FT301"), ("Food Microbiology", "FT302"), ("Product Development", "FT303"), ("Food Entrepreneurship", "ENT301")],
                4: [("Packaging & Labeling", "FT401"), ("Food Law & Standards", "FT402"), ("Internship & Capstone", "FT403"), ("Industry Exposure", "FT404")],
            },
        }
        
        for course_name, semesters in sample_papers.items():
            course_id = courses.get(course_name)
            if course_id:
                for semester, papers in semesters.items():
                    for paper_name, paper_code in papers:
                        cursor.execute(
                            "SELECT COUNT(*) as count FROM papers WHERE course_id = %s AND semester = %s AND name = %s",
                            (course_id, semester, paper_name)
                        )
                        if cursor.fetchone()['count'] == 0:
                            cursor.execute(
                                "INSERT INTO papers (course_id, semester, name, code) VALUES (%s, %s, %s, %s)",
                                (course_id, semester, paper_name, paper_code)
                            )
        print("✅ Inserted sample papers")
        
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
