"""
Add BCA Students (Batch 2024, Semester 1)
"""
from firebase_config import get_db
from datetime import datetime

def add_students():
    db = get_db()
    
    students_data = [
        {
            "name": "SHAHID ALAM HOQUE",
            "roll": "UT-241-033-0001",
            "email": "shahid.alam@bca2024.edu",
            "phone": "9876543210"
        },
        {
            "name": "KRISHNAMANI RABHA",
            "roll": "UT-241-033-0002",
            "email": "krishnamani.rabha@bca2024.edu",
            "phone": "9876543211"
        },
        {
            "name": "KANKAN RAJBONGSHI",
            "roll": "UT-241-033-0004",
            "email": "kankan.rajbongshi@bca2024.edu",
            "phone": "9876543212"
        },
        {
            "name": "ARJUN BORO",
            "roll": "UT-241-033-0005",
            "email": "arjun.boro@bca2024.edu",
            "phone": "9876543213"
        },
        {
            "name": "KAUSHIK RAJBONGSHI",
            "roll": "UT-241-033-0006",
            "email": "kaushik.rajbongshi@bca2024.edu",
            "phone": "9876543214"
        }
    ]
    
    print("[*] Adding BCA Students (Batch 2024, Semester 1)...\n")
    
    # Find BCA course
    print("[*] Finding Bachelor of Computer Applications course...")
    courses = list(db.collection("courses").where("name", "==", "Bachelor of Computer Applications").limit(1).stream())
    if not courses:
        print("ERROR: BCA course not found!")
        return
    
    bca_course_id = courses[0].id
    print(f"    [OK] BCA Course ID: {bca_course_id}")
    
    # Get Semester 1 papers
    print("\n[*] Getting papers for Semester 1...")
    papers_query = db.collection("papers").where("course_id", "==", bca_course_id).where("semester", "==", 1)
    paper_docs = list(papers_query.stream())
    paper_ids = [doc.id for doc in paper_docs]
    
    print(f"    [OK] Found {len(paper_ids)} papers for Semester 1")
    for i, doc in enumerate(paper_docs, 1):
        print(f"        {i}. {doc.get('name')}")
    
    # Add students
    print("\n[*] Adding students...")
    students_ref = db.collection("students")
    
    for student in students_data:
        doc_ref = students_ref.add({
            "name": student["name"],
            "roll": student["roll"],
            "course_id": bca_course_id,
            "semester": 1,
            "admission_year": 2024,
            "papers": paper_ids,
            "email": student["email"],
            "phone": student["phone"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        print(f"    [OK] {student['name']} (Roll: {student['roll']})")
    
    # Summary
    print("\n" + "="*60)
    print("SUCCESS! 5 Students Added!")
    print("="*60 + "\n")
    print(f"Course: Bachelor of Computer Applications")
    print(f"Admission Year: 2024")
    print(f"Semester: 1")
    print(f"Papers Assigned: {len(paper_ids)}\n")
    print("Students Added:")
    for i, student in enumerate(students_data, 1):
        print(f"  {i}. {student['name']}")
        print(f"     Roll: {student['roll']}")

if __name__ == "__main__":
    add_students()
