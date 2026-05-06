#!/usr/bin/env python3
"""
Create Empty Collections for Students and Attendance

This script creates the required Firestore collections:
1. students - Student records with their course, semester, and papers
2. attendance - Daily attendance tracking (student_id, date, subject, status)

These collections start empty and will be populated through the web application UI.
"""

from firebase_config import get_db
from datetime import datetime

def main():
    db = get_db()
    
    print("[*] Setting up Firestore collections for Students and Attendance...\n")
    
    # Step 1: Create a placeholder student document to initialize the collection
    print("[*] Creating 'students' collection...")
    students_ref = db.collection("students")
    
    # Add a placeholder document (will be deleted after initialization)
    placeholder_student = students_ref.add({
        "name": "[PLACEHOLDER - DELETE ME]",
        "roll": "0000",
        "course_id": "placeholder",
        "semester": 0,
        "admission_year": 2026,
        "papers": [],
        "email": "placeholder@example.com",
        "phone": "0000000000",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })
    
    placeholder_id = placeholder_student[1].id
    print(f"    [OK] Created placeholder student (ID: {placeholder_id})")
    
    # Delete the placeholder immediately
    students_ref.document(placeholder_id).delete()
    print(f"    [OK] Placeholder deleted - collection initialized and empty")
    
    # Step 2: Create a placeholder attendance document to initialize the collection
    print("\n[*] Creating 'attendance' collection...")
    attendance_ref = db.collection("attendance")
    
    # Add a placeholder document (will be deleted after initialization)
    placeholder_attendance = attendance_ref.add({
        "student_id": "placeholder",
        "date": "2026-01-01",
        "subject": "[PLACEHOLDER - DELETE ME]",
        "status": "absent",
        "created_at": datetime.utcnow(),
    })
    
    placeholder_id = placeholder_attendance[1].id
    print(f"    [OK] Created placeholder attendance (ID: {placeholder_id})")
    
    # Delete the placeholder immediately
    attendance_ref.document(placeholder_id).delete()
    print(f"    [OK] Placeholder deleted - collection initialized and empty")
    
    # Step 3: Verify collections exist
    print("\n[*] Verifying collections...")
    
    # Check students collection
    students_docs = list(students_ref.limit(1).stream())
    if len(students_docs) == 0:
        print(f"    [OK] 'students' collection: READY (empty)")
    else:
        print(f"    [ERROR] 'students' collection has {len(students_docs)} documents")
    
    # Check attendance collection
    attendance_docs = list(attendance_ref.limit(1).stream())
    if len(attendance_docs) == 0:
        print(f"    [OK] 'attendance' collection: READY (empty)")
    else:
        print(f"    [ERROR] 'attendance' collection has {len(attendance_docs)} documents")
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"SUCCESS! COLLECTIONS CREATED!")
    print(f"{'='*60}")
    print(f"\nCollections Ready:")
    print(f"  1. students - For student records")
    print(f"  2. attendance - For attendance tracking")
    print(f"\nStudent Fields:")
    print(f"  - name: Student's full name")
    print(f"  - roll: Roll number (unique)")
    print(f"  - course_id: Reference to courses collection")
    print(f"  - semester: Current semester (1-8)")
    print(f"  - admission_year: Year of admission (e.g., 2023)")
    print(f"  - papers: Array of paper IDs selected by student")
    print(f"  - email: Student's email (unique)")
    print(f"  - phone: Contact number")
    print(f"  - created_at: Timestamp")
    print(f"  - updated_at: Timestamp")
    print(f"\nAttendance Fields:")
    print(f"  - student_id: Reference to student document")
    print(f"  - date: Attendance date (YYYY-MM-DD format)")
    print(f"  - subject: Paper/Subject name")
    print(f"  - status: 'present', 'absent', or 'late'")
    print(f"  - created_at: Timestamp")
    print(f"\nYou can now add students and attendance through the web app!")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
