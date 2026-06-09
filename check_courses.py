"""
Check existing courses in Firebase
"""
from firebase_config import get_courses_ref

def check_courses():
    courses_ref = get_courses_ref()
    courses = courses_ref.stream()
    
    print("Existing courses:")
    for course in courses:
        print(f"  - {course.get('name')} (ID: {course.id})")

if __name__ == "__main__":
    check_courses()
