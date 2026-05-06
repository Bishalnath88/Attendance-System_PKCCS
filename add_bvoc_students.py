#!/usr/bin/env python3
"""
Add BVOC Students - Batch 2025, Semester 1

Students:
1. AKHIRUL HAQUE (Roll: UV-251-033-0016)
2. SUMAN DAS (Roll: UV-251-033-0017)
3. ASHIM JYOTI DEKA (Roll: UV-251-033-0028)
4. MANASH JYOTI NATH (Roll: UV-251-033-0029)
"""

from firebase_config import get_db
from datetime import datetime

def main():
    db = get_db()
    
    print("[*] Adding BVOC Students (Batch 2025, Semester 1)...\n")
    
    # Step 1: Find BVOC-IT course
    print("[*] Finding BVOC-IT course...")
    courses = list(db.collection("courses").where("name", "==", "Bachelor of Vocational - IT").limit(1).stream())
    
    if not courses:
        print("[ERROR] BVOC-IT course not found!")
        return False
    
    bvoc_course_id = courses[0].id
    print(f"    [OK] BVOC-IT Course ID: {bvoc_course_id}")
    
    # Step 2: Get papers for Semester 1
    print("\n[*] Getting papers for Semester 1...")
    papers_query = db.collection("papers").where("course_id", "==", bvoc_course_id).where("semester", "==", 1)
    papers = list(papers_query.stream())
    
    paper_ids = [doc.id for doc in papers]
    print(f"    [OK] Found {len(paper_ids)} papers for Semester 1")
    for i, doc in enumerate(papers, 1):
        paper_data = doc.to_dict()
        print(f"        {i}. {paper_data.get('name', 'Unknown')}")
    
    # Step 3: Student data
    students_data = [
        {
            "name": "AKHIRUL HAQUE",
            "roll": "UV-251-033-0016",
            "email": "akhirul.haque@student.example.com",
            "phone": "9876543210"
        },
        {
            "name": "SUMAN DAS",
            "roll": "UV-251-033-0017",
            "email": "suman.das@student.example.com",
            "phone": "9876543211"
        },
        {
            "name": "ASHIM JYOTI DEKA",
            "roll": "UV-251-033-0028",
            "email": "ashim.jyoti.deka@student.example.com",
            "phone": "9876543212"
        },
        {
            "name": "MANASH JYOTI NATH",
            "roll": "UV-251-033-0029",
            "email": "manash.jyoti.nath@student.example.com",
            "phone": "9876543213"
        }
    ]
    
    # Step 4: Add students
    print("\n[*] Adding students...")
    students_ref = db.collection("students")
    added_count = 0
    
    for student in students_data:
        try:
            doc_ref = students_ref.add({
                "name": student["name"],
                "roll": student["roll"],
                "course_id": bvoc_course_id,
                "semester": 1,
                "admission_year": 2025,
                "papers": paper_ids,
                "email": student["email"],
                "phone": student["phone"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            
            print(f"    [OK] {student['name']} (Roll: {student['roll']})")
            added_count += 1
            
        except Exception as e:
            print(f"    [ERROR] Failed to add {student['name']}: {str(e)}")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"SUCCESS! {added_count} Students Added!")
    print(f"{'='*60}")
    print(f"\nCourse: Bachelor of Vocational - IT")
    print(f"Admission Year: 2025")
    print(f"Semester: 1")
    print(f"Papers Assigned: {len(paper_ids)}")
    print(f"\nStudents Added:")
    for i, student in enumerate(students_data[:added_count], 1):
        print(f"  {i}. {student['name']}")
        print(f"     Roll: {student['roll']}")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
