"""
Update BVOC-IT Papers in Firestore
Add all B.Voc IT course papers semester-wise
"""

from firebase_config import get_db
from datetime import datetime

def update_bvoc_it_papers():
    """Delete old BVOC-IT papers and add new ones"""
    
    db = get_db()
    
    print("[*] Updating B.Voc IT Papers...")
    print()
    
    # ============================================
    # 1. GET BVOC-IT COURSE ID
    # ============================================
    print("[*] Finding B.Voc IT course ID...")
    
    courses_ref = db.collection("courses")
    docs = courses_ref.where("code", "==", "BVOC-IT").stream()
    
    bvoc_it_id = None
    for doc in docs:
        bvoc_it_id = doc.id
        print("    [OK] B.Voc IT Course ID: {}".format(bvoc_it_id))
        break
    
    if not bvoc_it_id:
        print("    [ERROR] B.Voc IT course not found!")
        return
    
    print()
    
    # ============================================
    # 2. DELETE OLD BVOC-IT PAPERS
    # ============================================
    print("[*] Deleting old B.Voc IT papers...")
    
    papers_ref = db.collection("papers")
    docs = papers_ref.where("course_id", "==", bvoc_it_id).stream()
    
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    
    print("    [OK] {} old paper(s) deleted".format(count))
    print()
    
    # ============================================
    # 3. ADD NEW BVOC-IT PAPERS
    # ============================================
    print("[*] Adding new B.Voc IT papers...")
    
    papers_data = [
        # Semester 1
        {
            "name": "Fundamentals of Computer",
            "code": "BIT101",
            "course_id": bvoc_it_id,
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Office Automation & Desktop Publishing",
            "code": "BIT102",
            "course_id": bvoc_it_id,
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Introduction to Computer Programming",
            "code": "BIT103",
            "course_id": bvoc_it_id,
            "semester": 1,
            "created_at": datetime.now()
        },
        # Semester 2
        {
            "name": "Introduction to Database Management System",
            "code": "BIT201",
            "course_id": bvoc_it_id,
            "semester": 2,
            "created_at": datetime.now()
        },
        {
            "name": "Computer Application in Printing & Graphics",
            "code": "BIT202",
            "course_id": bvoc_it_id,
            "semester": 2,
            "created_at": datetime.now()
        },
        {
            "name": "Internet & Web Technology",
            "code": "BIT203",
            "course_id": bvoc_it_id,
            "semester": 2,
            "created_at": datetime.now()
        },
        # Semester 3
        {
            "name": "Data Structure and Algorithm",
            "code": "BIT301",
            "course_id": bvoc_it_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        {
            "name": "Software Engineering",
            "code": "BIT302",
            "course_id": bvoc_it_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        {
            "name": "Object Oriented Programming using C++",
            "code": "BIT303",
            "course_id": bvoc_it_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        {
            "name": "Basics of Computer & Office Automation",
            "code": "BIT304",
            "course_id": bvoc_it_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        # Semester 4
        {
            "name": "Operating System",
            "code": "BIT401",
            "course_id": bvoc_it_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Programming in JAVA",
            "code": "BIT402",
            "course_id": bvoc_it_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Discrete Mathematics",
            "code": "BIT403",
            "course_id": bvoc_it_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "E-Commerce Technologies",
            "code": "BIT404",
            "course_id": bvoc_it_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        # Semester 5
        {
            "name": "Animation and Media Design",
            "code": "BIT501",
            "course_id": bvoc_it_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        {
            "name": "Computer Network",
            "code": "BIT502",
            "course_id": bvoc_it_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        {
            "name": "System Administration Using Linux",
            "code": "BIT503",
            "course_id": bvoc_it_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        # Semester 6
        {
            "name": "Information Security and Cyber Laws",
            "code": "BIT601",
            "course_id": bvoc_it_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Android Application Development",
            "code": "BIT602",
            "course_id": bvoc_it_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Database Design & Programming",
            "code": "BIT603",
            "course_id": bvoc_it_id,
            "semester": 6,
            "created_at": datetime.now()
        }
    ]
    
    semester_data = {}
    
    for paper in papers_data:
        db.collection("papers").add(paper)
        sem = paper["semester"]
        
        if sem not in semester_data:
            semester_data[sem] = []
        semester_data[sem].append(paper["name"])
    
    print()
    for sem in sorted(semester_data.keys()):
        print("    [OK] Semester {}: {} papers added".format(sem, len(semester_data[sem])))
        for paper in semester_data[sem]:
            print("         - {}".format(paper))
    
    print()
    print("=" * 50)
    print("SUCCESS! B.VOC IT PAPERS UPDATED!")
    print("=" * 50)
    print()
    print("[*] Total {} papers added".format(len(papers_data)))
    print()

if __name__ == "__main__":
    try:
        update_bvoc_it_papers()
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
