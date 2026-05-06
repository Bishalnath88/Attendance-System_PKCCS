"""
Add BVOC-IT Students (Batch 2023, Semester 1)
"""
from firebase_config import get_db
from datetime import datetime

def add_students():
    db = get_db()
    
    students_data = [
        {
            "name": "MANJUL ANOWAR",
            "roll": "UV-231-033-0014",
            "email": "manjul.anowar@bvoc2023.edu",
            "phone": "9876543201"
        },
        {
            "name": "RAKIBUL HUSSAIN",
            "roll": "UV-231-033-0015",
            "email": "rakibul.hussain@bvoc2023.edu",
            "phone": "9876543202"
        },
        {
            "name": "JAHIR ALI",
            "roll": "UV-231-033-0016",
            "email": "jahir.ali@bvoc2023.edu",
            "phone": "9876543203"
        },
        {
            "name": "SIMANTA RAJ SARMA",
            "roll": "UV-231-033-0018",
            "email": "simanta.raj@bvoc2023.edu",
            "phone": "9876543204"
        }
    ]
    
    print("[*] Adding BVOC Students (Batch 2023, Semester 1)...\n")
    
    # Find BVOC-IT course
    print("[*] Finding BVOC-IT course...")
    courses = list(db.collection("courses").where("name", "==", "Bachelor of Vocational - IT").limit(1).stream())
    if not courses:
        print("ERROR: BVOC-IT course not found!")
        return
    
    bvoc_course_id = courses[0].id
    print(f"    [OK] BVOC-IT Course ID: {bvoc_course_id}")
    
    # Get Semester 1 papers
    print("\n[*] Getting papers for Semester 1...")
    papers_query = db.collection("papers").where("course_id", "==", bvoc_course_id).where("semester", "==", 1)
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
            "course_id": bvoc_course_id,
            "semester": 1,
            "admission_year": 2023,
            "papers": paper_ids,
            "email": student["email"],
            "phone": student["phone"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        print(f"    [OK] {student['name']} (Roll: {student['roll']})")
    
    # Summary
    print("\n" + "="*60)
    print("SUCCESS! 4 Students Added!")
    print("="*60 + "\n")
    print(f"Course: Bachelor of Vocational - IT")
    print(f"Admission Year: 2023")
    print(f"Semester: 1")
    print(f"Papers Assigned: {len(paper_ids)}\n")
    print("Students Added:")
    for i, student in enumerate(students_data, 1):
        print(f"  {i}. {student['name']}")
        print(f"     Roll: {student['roll']}")

if __name__ == "__main__":
    add_students()
