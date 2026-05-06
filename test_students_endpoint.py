"""
Quick test to check what's wrong with the /students endpoint
"""
import sys
sys.path.insert(0, r'd:\CODE PLAYGROUND\6th_Sem_Project\Main')

from firebase_config import get_db, get_students_ref, get_courses_ref
from datetime import date

def test_students():
    try:
        print("[*] Testing /students endpoint logic...")
        
        db = get_db()
        students_ref = get_students_ref()
        
        print("[*] Fetching all students...")
        query = students_ref
        docs = list(query.stream())
        print(f"    [OK] Found {len(docs)} students")
        
        for doc in docs[:2]:  # Just test first 2
            student_dict = doc.to_dict()
            print(f"\n[*] Processing student: {student_dict.get('name')}")
            
            # Get course info
            course_id = student_dict.get('course_id')
            print(f"    Course ID: {course_id}")
            
            courses_ref = get_courses_ref()
            course_doc = courses_ref.document(course_id).get()
            
            if course_doc.exists:
                course_data = course_doc.to_dict()
                print(f"    Course found: {course_data.get('name')}")
            else:
                print(f"    ERROR: Course {course_id} not found!")
        
        print("\n[SUCCESS] Endpoint logic appears to work!")
        
    except Exception as error:
        print(f"\n[ERROR] {error}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_students()
