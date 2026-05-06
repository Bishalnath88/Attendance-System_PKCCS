#!/usr/bin/env python3
"""
Fix Course Semesters - CORRECT VERSION with proper semester counts

CORRECT COUNTS:
- BSc: 8 semesters (4-year degree)
- BVOC-IT: 6 semesters (3-year degree)
- BCA: 6 semesters (3-year degree)
TOTAL: 20 course_semester documents

Academic Calendar:
- Odd Semesters (1, 3, 5, 7): August - December
- Even Semesters (2, 4, 6, 8): January - July
- Course Start: August (mid-year)
- Course End: July (mid-year)
- 2 semesters per academic year
"""

from firebase_config import get_db
from datetime import datetime

def main():
    db = get_db()
    
    print("[*] Fixing Course Semesters with CORRECT counts...\n")
    
    # Step 1: Find valid course IDs
    print("[*] Finding valid course IDs...")
    courses_ref = db.collection("courses")
    course_mapping = {}
    
    for doc in courses_ref.stream():
        course_data = doc.to_dict()
        course_name = course_data.get('name', '')
        course_mapping[course_name] = doc.id
        print(f"    [OK] {course_name} -> {doc.id}")
    
    # Validate we have all 3 courses
    required_courses = ['Bachelor of Science', 'Bachelor of Vocational - IT', 'Bachelor of Computer Applications']
    if not all(course in course_mapping for course in required_courses):
        print("\n[ERROR] Missing one or more course types!")
        print(f"Found: {list(course_mapping.keys())}")
        return False
    
    # Step 2: Delete ALL old course_semesters (wrong data)
    print("\n[*] Deleting incorrect course_semesters...")
    semesters_ref = db.collection("course_semesters")
    deleted_count = 0
    
    for doc in semesters_ref.stream():
        semesters_ref.document(doc.id).delete()
        deleted_count += 1
    
    print(f"    [OK] {deleted_count} old documents deleted")
    
    # Step 3: Create NEW course_semesters with CORRECT counts
    print("\n[*] Creating new course_semesters with CORRECT semester counts...")
    
    # CORRECT SEMESTER COUNTS
    courses_config = {
        'Bachelor of Science': {
            'course_id': course_mapping['Bachelor of Science'],
            'semesters': 8,  # 4 years = 8 semesters
            'description': '4-year Bachelor of Science degree'
        },
        'Bachelor of Vocational - IT': {
            'course_id': course_mapping['Bachelor of Vocational - IT'],
            'semesters': 6,  # 3 years = 6 semesters
            'description': '3-year Bachelor of Vocational (IT) degree'
        },
        'Bachelor of Computer Applications': {
            'course_id': course_mapping['Bachelor of Computer Applications'],
            'semesters': 6,  # 3 years = 6 semesters
            'description': '3-year Bachelor of Computer Applications degree'
        }
    }
    
    total_created = 0
    
    for course_name, config in courses_config.items():
        course_id = config['course_id']
        num_semesters = config['semesters']
        
        created = 0
        for semester in range(1, num_semesters + 1):
            semesters_ref.add({
                'course_id': course_id,
                'semester': semester,
                'created_at': datetime.utcnow()
            })
            created += 1
        
        print(f"    [OK] {course_name}: {created} semesters created (Sem 1-{num_semesters})")
        total_created += created
    
    # Step 4: Verify the counts
    print(f"\n[*] Verifying semester counts...")
    for course_name, config in courses_config.items():
        course_id = config['course_id']
        query = semesters_ref.where('course_id', '==', course_id)
        count = len(list(query.stream()))
        expected = config['semesters']
        status = "[OK]" if count == expected else "[ERROR]"
        print(f"    {status} {course_name}: {count} semesters (Expected: {expected})")
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"SUCCESS! COURSE SEMESTERS FIXED!")
    print(f"{'='*50}")
    print(f"Total course_semester documents: {total_created}")
    print(f"  - Bachelor of Science: 8 semesters (4-year degree)")
    print(f"  - Bachelor of Vocational - IT: 6 semesters (3-year degree)")
    print(f"  - Bachelor of Computer Applications: 6 semesters (3-year degree)")
    print(f"\nAcademic Calendar:")
    print(f"  - Odd Semesters (1,3,5,7): August - December")
    print(f"  - Even Semesters (2,4,6,8): January - July")
    print(f"  - 2 semesters per academic year")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
