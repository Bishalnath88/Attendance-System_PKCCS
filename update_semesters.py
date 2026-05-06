import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to calculate current semester based on admission batch
def get_current_semester(admission_year):
    """
    Academic year structure: Aug-Jul
    Aug-Dec: Odd semesters (1, 3, 5)
    Jan-Jul: Even semesters (2, 4, 6)
    """
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # Calculate complete academic years since admission (assuming admitted in August)
    if current_month < 8:
        # If before August, we haven't completed the current academic year
        complete_years = current_year - admission_year - 1
    else:
        # If August or later, we've completed one more year
        complete_years = current_year - admission_year
    
    # Each complete year = 2 semesters
    semesters_completed = complete_years * 2
    
    # Determine which semester of the current academic year
    if current_month >= 8 or current_month < 1:  # Aug-Dec: odd semester
        current_semester = semesters_completed + 1
    else:  # Jan-Jul: even semester
        current_semester = semesters_completed + 2
    
    # Cap at 6 for 3-year programs
    return min(6, current_semester)

# Get all students
students = db.collection('students').stream()
updated_count = 0

print("Current student semester values:")
for student in students:
    student_data = student.to_dict()
    admission_year = student_data.get('admission_year')
    current_sem = get_current_semester(admission_year) if admission_year else 1
    old_sem = student_data.get('semester')
    
    if old_sem != current_sem:
        db.collection('students').document(student.id).update({
            'semester': current_sem
        })
        updated_count += 1
        print(f"  {student_data.get('name')}: Batch {admission_year} → Semester {old_sem} → {current_sem}")
    else:
        print(f"  {student_data.get('name')}: Batch {admission_year}, Semester {current_sem} ✓")

print(f"\nTotal students updated: {updated_count}")
