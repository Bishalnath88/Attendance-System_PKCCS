"""
Update BCA Papers in Firestore
Add all BCA course papers semester-wise
"""

from firebase_config import get_db
from datetime import datetime

def update_bca_papers():
    """Delete old BCA papers and add new ones"""
    
    db = get_db()
    
    print("[*] Updating BCA Papers...")
    print()
    
    # ============================================
    # 1. GET BCA COURSE ID
    # ============================================
    print("[*] Finding BCA course ID...")
    
    courses_ref = db.collection("courses")
    docs = courses_ref.where("code", "==", "BCA").stream()
    
    bca_id = None
    for doc in docs:
        bca_id = doc.id
        print("    [OK] BCA Course ID: {}".format(bca_id))
        break
    
    if not bca_id:
        print("    [ERROR] BCA course not found!")
        return
    
    print()
    
    # ============================================
    # 2. DELETE OLD BCA PAPERS
    # ============================================
    print("[*] Deleting old BCA papers...")
    
    papers_ref = db.collection("papers")
    docs = papers_ref.where("course_id", "==", bca_id).stream()
    
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    
    print("    [OK] {} old paper(s) deleted".format(count))
    print()
    
    # ============================================
    # 3. ADD NEW BCA PAPERS
    # ============================================
    print("[*] Adding new BCA papers...")
    
    papers_data = [
        # Semester 1
        {
            "name": "Computer Fundamentals",
            "code": "BCA101",
            "course_id": bca_id,
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Introduction to C - Programming",
            "code": "BCA102",
            "course_id": bca_id,
            "semester": 1,
            "created_at": datetime.now()
        },
        {
            "name": "Mathematics I",
            "code": "BCA103",
            "course_id": bca_id,
            "semester": 1,
            "created_at": datetime.now()
        },
        # Semester 2
        {
            "name": "Data Structures & Algorithms Using C",
            "code": "BCA201",
            "course_id": bca_id,
            "semester": 2,
            "created_at": datetime.now()
        },
        {
            "name": "Digital Logic Fundamentals",
            "code": "BCA202",
            "course_id": bca_id,
            "semester": 2,
            "created_at": datetime.now()
        },
        {
            "name": "Mathematics II",
            "code": "BCA203",
            "course_id": bca_id,
            "semester": 2,
            "created_at": datetime.now()
        },
        # Semester 3
        {
            "name": "Computer Organization and Architecture",
            "code": "BCA301",
            "course_id": bca_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        {
            "name": "System Software",
            "code": "BCA302",
            "course_id": bca_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        {
            "name": "Object Oriented Programming through C++",
            "code": "BCA303",
            "course_id": bca_id,
            "semester": 3,
            "created_at": datetime.now()
        },
        # Semester 4
        {
            "name": "Database Management System",
            "code": "BCA401",
            "course_id": bca_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Operating system",
            "code": "BCA402",
            "course_id": bca_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Automata Theory and Languages",
            "code": "BCA403",
            "course_id": bca_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        {
            "name": "Python Programming",
            "code": "BCA404",
            "course_id": bca_id,
            "semester": 4,
            "created_at": datetime.now()
        },
        # Semester 5
        {
            "name": "Software Engineering",
            "code": "BCA501",
            "course_id": bca_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        {
            "name": "Web Technologies",
            "code": "BCA502",
            "course_id": bca_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        {
            "name": "Java Programming",
            "code": "BCA503",
            "course_id": bca_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        {
            "name": "Computer Networks",
            "code": "BCA504",
            "course_id": bca_id,
            "semester": 5,
            "created_at": datetime.now()
        },
        # Semester 6
        {
            "name": "Computer graphics",
            "code": "BCA601",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Information Security and Cyber Laws",
            "code": "BCA602",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Computer Oriented Numerical and Statistical Methods",
            "code": "BCA603",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Artificial Intelligence",
            "code": "BCA604",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Advanced Web Programming",
            "code": "BCA605",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Data Mining and Warehousing",
            "code": "BCA606",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Optimization Techniques",
            "code": "BCA607",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Mobile Application Development",
            "code": "BCA608",
            "course_id": bca_id,
            "semester": 6,
            "created_at": datetime.now()
        },
        {
            "name": "Graph Theory",
            "code": "BCA609",
            "course_id": bca_id,
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
    print("SUCCESS! BCA PAPERS UPDATED!")
    print("=" * 50)
    print()
    print("[*] Total {} papers added".format(len(papers_data)))
    print()

if __name__ == "__main__":
    try:
        update_bca_papers()
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
