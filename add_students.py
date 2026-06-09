"""
Script to add students directly to Firebase Firestore
"""
import sys
from firebase_config import get_students_ref, get_courses_ref
import json

def add_students():
    # Get references
    students_ref = get_students_ref()
    
    # Bachelor of Science course ID
    course_id = "2vJlOSAayNq6QqftzAlz"
    course_name = "Bachelor of Science"
    
    # Student data to add
    students_data = [
        {
            "name": "DEVID SAHARIAH",
            "roll": "US-251-033-0088",
            "admission_year": 2025,
            "course_id": course_id,
            "course_name": "BSc",
            "semester": 1,
            "email": "devid.sahariah@student.edu",
            "phone": ""
        },
        {
            "name": "RIGASHREE PATOWARY",
            "roll": "US-251-033-0127",
            "admission_year": 2025,
            "course_id": course_id,
            "course_name": "BSc",
            "semester": 1,
            "email": "rigashree.patowary@student.edu",
            "phone": ""
        },
        {
            "name": "DURLAV NATH",
            "roll": "US-251-033-0140",
            "admission_year": 2025,
            "course_id": course_id,
            "course_name": "BSc",
            "semester": 1,
            "email": "durlav.nath@student.edu",
            "phone": ""
        },
        {
            "name": "KOUSHIK DEKA",
            "roll": "US-251-033-0141",
            "admission_year": 2025,
            "course_id": course_id,
            "course_name": "BSc",
            "semester": 1,
            "email": "koushik.deka@student.edu",
            "phone": ""
        }
    ]
    
    # Add students to Firestore
    added_count = 0
    for student in students_data:
        try:
            # Add document with auto-generated ID
            doc_ref = students_ref.add(student)
            print(f"✓ Added: {student['name']} ({student['roll']})")
            added_count += 1
        except Exception as e:
            print(f"✗ Failed to add {student['name']}: {str(e)}")
    
    print(f"\n✓ Successfully added {added_count}/{len(students_data)} students")

if __name__ == "__main__":
    try:
        add_students()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
