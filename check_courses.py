import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Get all students and their courses
batch_courses = {}
for doc in db.collection('students').stream():
    data = doc.to_dict()
    batch = data.get('admission_year')
    course_id = data.get('course_id')
    
    if batch not in batch_courses:
        batch_courses[batch] = set()
    batch_courses[batch].add(course_id)

# Get course names
courses_map = {}
for doc in db.collection('courses').stream():
    courses_map[doc.id] = doc.to_dict().get('name')

# Print results
print("Students by Batch and Course:")
for batch in sorted(batch_courses.keys()):
    print(f"\nBatch {batch}:")
    for course_id in batch_courses[batch]:
        course_name = courses_map.get(course_id, "Unknown")
        # Count students
        query = db.collection('students').where('admission_year', '==', batch).where('course_id', '==', course_id)
        count = len(list(query.stream()))
        print(f"  {course_name}: {count} students (ID: {course_id})")
