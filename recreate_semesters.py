"""
Recreate Course Semesters with Valid Course IDs
Delete old course_semesters and create new ones with current course IDs
"""

from firebase_config import get_db
from datetime import datetime

def recreate_semesters():
    """Recreate course_semesters with current valid course IDs"""
    
    db = get_db()
    
    print("[*] Recreating Course Semesters...")
    print()
    
    # ============================================
    # 1. GET VALID COURSE IDs
    # ============================================
    print("[*] Finding valid course IDs...")
    
    courses_ref = db.collection("courses")
    courses_doc = list(courses_ref.stream())
    
    course_ids = {}
    for doc in courses_doc:
        data = doc.to_dict()
        code = data.get("code", "UNKNOWN")
        course_ids[code] = doc.id
        print("    [OK] {} -> {}".format(code, doc.id))
    
    print()
    
    # ============================================
    # 2. DELETE OLD COURSE_SEMESTERS
    # ============================================
    print("[*] Deleting old course_semesters...")
    
    semesters_ref = db.collection("course_semesters")
    semesters_docs = list(semesters_ref.stream())
    
    count = 0
    for doc in semesters_docs:
        doc.reference.delete()
        count += 1
    
    print("    [OK] {} semester(s) deleted".format(count))
    print()
    
    # ============================================
    # 3. CREATE NEW COURSE_SEMESTERS
    # ============================================
    print("[*] Creating new course_semesters...")
    
    semester_config = {
        "BSC": 6,
        "BVOC-IT": 6,
        "BCA": 6
    }
    
    for course_code, num_semesters in semester_config.items():
        if course_code not in course_ids:
            print("    [ERROR] Course {} not found!".format(course_code))
            continue
        
        course_id = course_ids[course_code]
        
        for sem in range(1, num_semesters + 1):
            semester_data = {
                "course_id": course_id,
                "semester": sem,
                "created_at": datetime.now()
            }
            db.collection("course_semesters").add(semester_data)
        
        print("    [OK] {}: {} semesters created".format(course_code, num_semesters))
    
    print()
    print("=" * 50)
    print("SUCCESS! COURSE SEMESTERS RECREATED!")
    print("=" * 50)
    print()

if __name__ == "__main__":
    try:
        recreate_semesters()
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
