# -*- coding: utf-8 -*-
"""
Firestore Collections Setup Script
Automatically creates all collections and documents
"""

from firebase_config import get_db
from datetime import datetime

def setup_firestore():
    """Setup all Firestore collections with sample data"""
    
    db = get_db()
    
    print("[*] Starting Firestore Setup...")
    print()
    
    # ============================================
    # 1. COURSES COLLECTION
    # ============================================
    print("[+] Setting up COURSES collection...")
    
    courses_data = [
        {
            "name": "Bachelor of Science",
            "code": "BSC",
            "created_at": datetime.now()
        },
        {
            "name": "Bachelor of Vocational - IT",
            "code": "BVOC-IT",
            "created_at": datetime.now()
        },
        {
            "name": "Bachelor of Computer Applications",
            "code": "BCA",
            "created_at": datetime.now()
        }
    ]
    
    course_ids = {}
    for course in courses_data:
        doc_ref = db.collection("courses").add(course)
        course_id = doc_ref[1].id
        course_ids[course["code"]] = course_id
        print("    [OK] {} -> ID: {}".format(course['name'], course_id))
    
    print()
    
    # ============================================
    # 2. COURSE_SEMESTERS COLLECTION
    # ============================================
    print("[+] Setting up COURSE_SEMESTERS collection...")
    
    semester_config = {
        "BSC": 8,
        "BVOC-IT": 6,
        "BCA": 6
    }
    
    for course_code, num_semesters in semester_config.items():
        course_id = course_ids[course_code]
        for sem in range(1, num_semesters + 1):
            semester_data = {
                "course_id": course_id,
                "semester": sem,
                "created_at": datetime.now()
            }
            db.collection("course_semesters").add(semester_data)
        print("    [OK] {}: {} semesters added".format(course_code, num_semesters))
    
    print()
    
    # ============================================
    # 3. PAPERS COLLECTION
    # ============================================
    print("[+] Setting up PAPERS collection...")
    
    papers_data = [
        # BSC Papers
        {
            "name": "Mathematics",
            "code": "MA101",
            "course_id": course_ids["BSC"],
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Physics",
            "code": "PH101",
            "course_id": course_ids["BSC"],
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Chemistry",
            "code": "CH101",
            "course_id": course_ids["BSC"],
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Calculus",
            "code": "MA102",
            "course_id": course_ids["BSC"],
            "semester": 2,
            "created_at": datetime.now()
        },
        {
            "name": "Modern Physics",
            "code": "PH102",
            "course_id": course_ids["BSC"],
            "semester": 2,
            "created_at": datetime.now()
        },
        # BVOC-IT Papers
        {
            "name": "Web Development",
            "code": "WD101",
            "course_id": course_ids["BVOC-IT"],
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Database Design",
            "code": "DB101",
            "course_id": course_ids["BVOC-IT"],
            "semester": 1,
            "created_at": datetime.now()
        },
        # BCA Papers
        {
            "name": "Programming in C",
            "code": "CS101",
            "course_id": course_ids["BCA"],
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Web Design",
            "code": "WD101",
            "course_id": course_ids["BCA"],
            "semester": 1,
            "created_at": datetime.now()
        }
    ]
    
    for paper in papers_data:
        db.collection("papers").add(paper)
        print("    [OK] {} - {}".format(paper['code'], paper['name']))
    
    print()
    
    # ============================================
    # 4. USERS COLLECTION
    # ============================================
    print("[+] Setting up USERS collection...")
    
    user_data = {
        "email": "admin@example.com",
        "password": "",  # Will be set through registration
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    db.collection("users").add(user_data)
    print("    [OK] User: {}".format(user_data['email']))
    
    print()
    
    # ============================================
    # 5. STUDENTS COLLECTION (Empty - will auto-create)
    # ============================================
    print("[+] STUDENTS collection ready (empty - will be populated through app)")
    print()
    
    # ============================================
    # 6. ATTENDANCE COLLECTION (Empty - will auto-create)
    # ============================================
    print("[+] ATTENDANCE collection ready (empty - will be populated through app)")
    print()
    
    print("=" * 50)
    print("SUCCESS! FIRESTORE SETUP COMPLETE!")
    print("=" * 50)
    print()
    print("[*] Course IDs (Save this for reference):")
    for code, id_ in course_ids.items():
        print("   {}: {}".format(code, id_))
    print()
    print("[*] Ready to run: python app.py")
    print()

if __name__ == "__main__":
    try:
        setup_firestore()
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
