"""
Detailed test to find the exact error in /students endpoint
"""
import sys
sys.path.insert(0, r'd:\CODE PLAYGROUND\6th_Sem_Project\Main')

from firebase_config import get_db, get_students_ref, get_courses_ref
from datetime import date, datetime

def serialize_value(value):
    """Convert Python objects to JSON-serializable format"""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value

def serialize_doc(doc):
    """Convert Firestore document to JSON-serializable format"""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['id'] = doc.id  # Add document ID
    # Serialize all values
    for key, value in data.items():
        data[key] = serialize_value(value)
    return data

def add_batch_to_student(student):
    """Add batch information and current semester to a student record"""
    try:
        if 'admission_year' not in student:
            return student
            
        student = student.copy()
        admission_year = student.get('admission_year')
        course_id = student.get('course_id')
        
        # Query course to check if BSc (4 years) or other (3 years)
        db = get_db()
        course_doc = db.collection("courses").document(course_id).get()
        
        if not course_doc.exists:
            return student
        
        course = course_doc.to_dict()
        
        # Check for both "BSc" and "Bachelor of Science"
        is_bsc = 'BSc' in course.get('name', '') or 'Bachelor of Science' in course.get('name', '')
        duration = 4 if is_bsc else 3
        end_year = admission_year + duration
        student['batch'] = f"{admission_year}-{end_year}"
        
        return student
    except Exception as e:
        print(f"ERROR in add_batch_to_student: {e}")
        import traceback
        traceback.print_exc()
        return student

def get_course_end_date(admission_year, course_duration):
    """Calculate course end date (July of final year)"""
    end_year = admission_year + course_duration
    return date(end_year, 7, 31)

def has_course_ended(admission_year, course_duration):
    """Check if a student's course has ended based on today's date"""
    end_date = get_course_end_date(admission_year, course_duration)
    today = date.today()
    return today > end_date

def test_get_students():
    try:
        print("[*] Testing get_students() logic...\n")
        
        db = get_db()
        students_ref = get_students_ref()
        
        # Test query
        print("[*] Querying all students...")
        query = students_ref
        docs = list(query.stream())
        print(f"    [OK] Found {len(docs)} students\n")
        
        data = []
        for i, doc in enumerate(docs, 1):
            print(f"[{i}] Processing {doc.get('name')}...")
            
            try:
                # Serialize document
                student_dict = serialize_doc(doc)
                print(f"    [OK] Serialized")
                
                # Add batch info
                student_dict = add_batch_to_student(student_dict)
                print(f"    [OK] Added batch info")
                
                # Get course info
                courses_ref = get_courses_ref()
                course_id = student_dict.get('course_id')
                course_doc = courses_ref.document(course_id).get()
                print(f"    [OK] Fetched course doc")
                
                if course_doc.exists:
                    course_name = course_doc.to_dict().get('name', '')
                    is_bsc = 'BSc' in course_name or 'Bachelor of Science' in course_name
                    duration = 4 if is_bsc else 3
                    print(f"    [OK] Course: {course_name}, Duration: {duration}")
                    
                    # Calculate course end date
                    student_admission_year = student_dict.get('admission_year')
                    if student_admission_year:
                        course_end_date = get_course_end_date(student_admission_year, duration)
                        course_is_active = not has_course_ended(student_admission_year, duration)
                        student_dict['course_end_date'] = course_end_date.isoformat()
                        student_dict['course_active'] = course_is_active
                        print(f"    [OK] End date: {course_end_date}, Active: {course_is_active}")
                    
                    student_dict['course_duration'] = duration
                    print(f"    [OK] Added duration")
                
                data.append(student_dict)
                print(f"    [OK] Student added to list\n")
                
            except Exception as e:
                print(f"    [ERROR] Failed to process student {i}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Sort
        print("[*] Sorting students...")
        data.sort(key=lambda x: (x.get('name', ''), x.get('roll', '')))
        print(f"    [OK] Sorted {len(data)} students\n")
        
        # Convert to JSON
        print("[*] Converting to JSON...")
        import json
        json_output = json.dumps(data)
        print(f"    [OK] JSON output length: {len(json_output)} bytes\n")
        
        print("[SUCCESS] get_students() logic works correctly!")
        print(f"\nTotal students processed: {len(data)}")
        
    except Exception as error:
        print(f"\n[FATAL ERROR] {error}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_students()
