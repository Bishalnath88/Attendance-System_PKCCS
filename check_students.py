#!/usr/bin/env python3

import mysql.connector
from pathlib import Path
import os
import json

def load_env():
    env_path = Path('.env')
    for line in env_path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

load_env()

config = {
    'host': os.environ.get('ATTENDANCE_DB_HOST'),
    'user': os.environ.get('ATTENDANCE_DB_USER'),
    'password': os.environ.get('ATTENDANCE_DB_PASSWORD'),
    'database': os.environ.get('ATTENDANCE_DB_NAME'),
    'port': int(os.environ.get('ATTENDANCE_DB_PORT', '3306'))
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

# Check student count
cursor.execute('SELECT COUNT(*) as cnt FROM students')
count = cursor.fetchone()['cnt']
print(f'[INFO] Total students in database: {count}')

if count > 0:
    print('\n[INFO] Students found:')
    cursor.execute('SELECT id, roll, name, email, phone FROM students ORDER BY id ASC LIMIT 15')
    for row in cursor.fetchall():
        print(f'  ID:{row["id"]:<3} {row["roll"]:<15} {row["name"]:<20} {row["email"]:<30} {row["phone"]}')
else:
    print('[INFO] No students in database - inserting sample data...')
    
    # Get course IDs
    cursor.execute('SELECT id, name FROM courses')
    courses = {row['name']: row['id'] for row in cursor.fetchall()}
    
    sample_students = [
        ("Rahul Kumar", "BSC001", "Bachelor of Science", 1, ["Physics I", "Chemistry I"], "rahul.kumar@students.com", "9876543210"),
        ("Priya Singh", "BSC002", "Bachelor of Science", 1, ["Physics I", "Biology I"], "priya.singh@students.com", "9876543211"),
        ("Amit Patel", "BSC003", "Bachelor of Science", 2, ["Physics II", "Chemistry II"], "amit.patel@students.com", "9876543212"),
        ("Neha Verma", "BCA001", "Bachelor of Computer Applications", 1, ["Programming Fundamentals", "Digital Logic"], "neha.verma@students.com", "8765432101"),
        ("Sanjay Sharma", "BCA002", "Bachelor of Computer Applications", 1, ["Mathematics I", "Digital Logic"], "sanjay.sharma@students.com", "8765432102"),
        ("Anjali Desai", "BCA003", "Bachelor of Computer Applications", 2, ["Object Oriented Programming", "Database Management"], "anjali.desai@students.com", "8765432103"),
        ("Vikram Singh", "BVOC-IT001", "Bachelor of Vocational Studies - Information Technology", 1, ["IT Fundamentals", "Hardware Basics"], "vikram.singh@students.com", "7654321098"),
        ("Divya Gupta", "BVOC-IT002", "Bachelor of Vocational Studies - Information Technology", 1, ["Networking I", "IT Fundamentals"], "divya.gupta@students.com", "7654321099"),
        ("Karan Reddy", "BVOC-FOOD001", "Bachelor of Vocational Studies - Food Technology", 1, ["Food Science Basics", "Food Safety"], "karan.reddy@students.com", "6543210987"),
        ("Sneha Nair", "BVOC-FOOD002", "Bachelor of Vocational Studies - Food Technology", 1, ["Nutrition I", "Food Safety"], "sneha.nair@students.com", "6543210988"),
    ]
    
    for name, roll, course_name, semester, paper_names, email, phone in sample_students:
        course_id = courses.get(course_name)
        if not course_id:
            continue
        
        # Get paper IDs
        paper_ids = []
        for paper_name in paper_names:
            cursor.execute(
                'SELECT id FROM papers WHERE course_id = %s AND semester = %s AND name = %s',
                (course_id, semester, paper_name)
            )
            result = cursor.fetchone()
            if result:
                paper_ids.append(result['id'])
        
        # Check if student exists
        cursor.execute('SELECT id FROM students WHERE roll = %s OR email = %s', (roll, email))
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO students (name, roll, course_id, semester, papers, email, phone) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (name, roll, course_id, semester, json.dumps(paper_ids), email, phone)
            )
            print(f'  [+] Added: {roll} - {name}')
    
    conn.commit()
    print('[OK] Sample students inserted successfully!')

cursor.close()
conn.close()
