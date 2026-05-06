"""
Update BSC Papers in Firestore
Add all BSC course papers semester-wise
"""

from firebase_config import get_db
from datetime import datetime

def update_bsc_papers():
    """Delete old BSC papers and add new ones"""
    
    db = get_db()
    
    print("[*] Updating BSC Papers...")
    print()
    
    # ============================================
    # 1. GET BSC COURSE ID
    # ============================================
    print("[*] Finding BSC course ID...")
    
    courses_ref = db.collection("courses")
    docs = courses_ref.where("code", "==", "BSC").stream()
    
    bsc_id = None
    for doc in docs:
        bsc_id = doc.id
        print("    [OK] BSC Course ID: {}".format(bsc_id))
        break
    
    if not bsc_id:
        print("    [ERROR] BSC course not found!")
        return
    
    print()
    
    # ============================================
    # 2. DELETE OLD BSC PAPERS
    # ============================================
    print("[*] Deleting old BSC papers...")
    
    papers_ref = db.collection("papers")
    docs = papers_ref.where("course_id", "==", bsc_id).stream()
    
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    
    print("    [OK] {} old paper(s) deleted".format(count))
    print()
    
    # ============================================
    # 3. ADD NEW BSC PAPERS
    # ============================================
    print("[*] Adding new BSC papers...")
    
    papers_data = [
        # Semester 1
        {
            "name": "Introduction to C-Programming",
            "code": "CS101",
            "course_id": bsc_id,
            "semester": 1,
            "created_at": datetime.now()
        },
        # Semester 2
        {
            "name": "Computer Organization Minor-1",
            "code": "CS201",
            "course_id": bsc_id,
            "semester": 2,
            "created_at": datetime.now()
        },
        # Semester 3
        {
            "name": "Object Oriented Programming using C++",
            "code": "CS301",
            "course_id": bsc_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        {
            "name": "Data Structure",
            "code": "CS302",
            "course_id": bsc_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        # Semester 4
        {
            "name": "Database Management System",
            "code": "CS401",
            "course_id": bsc_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Mathematical Foundation of Computer Science",
            "code": "CS402",
            "course_id": bsc_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Operating System",
            "code": "CS403",
            "course_id": bsc_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Java Programming",
            "code": "CS404",
            "course_id": bsc_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Python Programming",
            "code": "CS405",
            "course_id": bsc_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        # Semester 5
        {
            "name": "Computer Networks",
            "code": "CS501",
            "course_id": bsc_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        {
            "name": "Software Engineering",
            "code": "CS502",
            "course_id": bsc_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        {
            "name": "Web Technologies",
            "code": "CS503",
            "course_id": bsc_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        # Semester 6
        {
            "name": "Automata Theory and Languages",
            "code": "CS601",
            "course_id": bsc_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Cloud Computing",
            "code": "CS602",
            "course_id": bsc_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Artificial Intelligence",
            "code": "CS603",
            "course_id": bsc_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Compiler Design",
            "code": "CS604",
            "course_id": bsc_id,
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
    print("SUCCESS! BSC PAPERS UPDATED!")
    print("=" * 50)
    print()
    print("[*] Total {} papers added".format(len(papers_data)))
    print()

if __name__ == "__main__":
    try:
        update_bsc_papers()
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
