"""
Clean up Firestore Courses Collection
Keep only valid courses (BSC, BVOC-IT, BCA) and delete all others
"""

from firebase_config import get_db
from datetime import datetime

def cleanup_courses():
    """Delete unwanted courses and keep only valid ones"""
    
    db = get_db()
    
    print("[*] Cleaning up Courses Collection...")
    print()
    
    # ============================================
    # 1. GET ALL COURSES
    # ============================================
    print("[*] Fetching all courses...")
    
    courses_ref = db.collection("courses")
    docs = list(courses_ref.stream())
    
    print("    [INFO] Total {} course(s) found".format(len(docs)))
    print()
    
    # ============================================
    # 2. IDENTIFY DUPLICATES AND KEEP ONE EACH
    # ============================================
    valid_codes = {"BSC", "BVOC-IT", "BCA"}
    courses_by_code = {}
    invalid_courses = []
    
    for doc in docs:
        data = doc.to_dict()
        code = data.get("code", "UNKNOWN")
        name = data.get("name", "UNKNOWN")
        
        if code in valid_codes:
            if code not in courses_by_code:
                # Keep first occurrence
                courses_by_code[code] = {
                    "id": doc.id,
                    "code": code,
                    "name": name
                }
                print("    [KEEP] {} - {}".format(code, name))
            else:
                # Mark duplicate for deletion
                invalid_courses.append({
                    "id": doc.id,
                    "code": code,
                    "name": name
                })
                print("    [DELETE DUPLICATE] {} - {} (ID: {})".format(code, name, doc.id))
        else:
            # Invalid code
            invalid_courses.append({
                "id": doc.id,
                "code": code,
                "name": name
            })
            print("    [DELETE INVALID] {} - {} (ID: {})".format(code, name, doc.id))
    
    print()
    print("[*] Summary:")
    print("    Valid courses (keeping): {}".format(len(courses_by_code)))
    print("    Courses to delete: {}".format(len(invalid_courses)))
    print()
    
    # ============================================
    # 3. DELETE DUPLICATES AND INVALID COURSES
    # ============================================
    if invalid_courses:
        print("[*] Deleting {} unwanted course(s)...".format(len(invalid_courses)))
        print()
        
        for course in invalid_courses:
            db.collection("courses").document(course["id"]).delete()
            print("    [OK] Deleted {} (ID: {})".format(course["code"], course["id"]))
        
        print()
    else:
        print("[*] No unwanted courses to delete!")
        print()
    
    # ============================================
    # 4. FINAL SUMMARY
    # ============================================
    print("=" * 50)
    print("SUCCESS! CLEANUP COMPLETE!")
    print("=" * 50)
    print()
    print("[*] Valid Courses Remaining (One Each):")
    for code in sorted(courses_by_code.keys()):
        course = courses_by_code[code]
        print("    {} - {} (ID: {})".format(course["code"], course["name"], course["id"]))
    print()

if __name__ == "__main__":
    try:
        cleanup_courses()
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
