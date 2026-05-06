# 📊 Data Migration Guide - MySQL to Firestore

Agar aapka pehle se MySQL database mein data hai, to yahan se migrate kar sakte ho.

---

## 🔄 Option A: Automatic Migration (Best)

### A.1 Export MySQL Data

Agar aapka Railway (MySQL) database running hai:

```bash
# Step 1: MySQL dump lao
mysqldump -h your_host -u your_user -p attendance_system > backup.sql

# Or use GUI tool jaise DBeaver/MySQL Workbench:
# 1. Database right-click
# 2. Export → Export as SQL
# 3. File save karo: backup.sql
```

### A.2 Parse SQL to JSON

Create a Python script `migrate.py`:

```python
import json
import mysql.connector
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase setup
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# MySQL setup
conn = mysql.connector.connect(
    host='your_railway_host',
    user='your_user',
    password='your_password',
    database='attendance_system'
)
cursor = conn.cursor(dictionary=True)

def migrate_users():
    print("📝 Migrating users...")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    for user in users:
        db.collection('users').add({
            'email': user['email'],
            'password': user['password'],
            'created_at': user['created_at'],
            'updated_at': user['updated_at'],
        })
    print(f"✅ Migrated {len(users)} users")

def migrate_courses():
    print("📝 Migrating courses...")
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    
    course_mapping = {}  # Store old ID -> new ID mapping
    
    for course in courses:
        new_doc = db.collection('courses').add({
            'name': course['name'],
            'code': course['code'],
            'created_at': course['created_at'],
        })
        course_mapping[course['id']] = new_doc[1].id
    
    print(f"✅ Migrated {len(courses)} courses")
    return course_mapping

def migrate_course_semesters(course_mapping):
    print("📝 Migrating course semesters...")
    cursor.execute("SELECT * FROM course_semesters")
    semesters = cursor.fetchall()
    
    for sem in semesters:
        if sem['course_id'] in course_mapping:
            db.collection('course_semesters').add({
                'course_id': course_mapping[sem['course_id']],
                'semester': sem['semester'],
                'created_at': sem['created_at'],
            })
    
    print(f"✅ Migrated {len(semesters)} course semesters")

def migrate_papers(course_mapping):
    print("📝 Migrating papers...")
    cursor.execute("SELECT * FROM papers")
    papers = cursor.fetchall()
    
    paper_mapping = {}
    
    for paper in papers:
        if paper['course_id'] in course_mapping:
            new_doc = db.collection('papers').add({
                'name': paper['name'],
                'code': paper['code'],
                'course_id': course_mapping[paper['course_id']],
                'semester': paper['semester'],
                'created_at': paper['created_at'],
            })
            paper_mapping[paper['id']] = new_doc[1].id
    
    print(f"✅ Migrated {len(papers)} papers")
    return paper_mapping

def migrate_students(course_mapping, paper_mapping):
    print("📝 Migrating students...")
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    
    student_mapping = {}
    
    for student in students:
        if student['course_id'] in course_mapping:
            # Parse papers JSON array
            papers = []
            if student['papers']:
                try:
                    old_paper_ids = json.loads(student['papers'])
                    papers = [paper_mapping.get(pid) for pid in old_paper_ids if pid in paper_mapping]
                except:
                    papers = []
            
            new_doc = db.collection('students').add({
                'name': student['name'],
                'roll': student['roll'],
                'email': student['email'],
                'phone': student['phone'],
                'course_id': course_mapping[student['course_id']],
                'semester': student['semester'],
                'admission_year': student.get('admission_year', 2024),
                'papers': papers,
                'created_at': student['created_at'],
                'updated_at': student['updated_at'],
            })
            student_mapping[student['id']] = new_doc[1].id
    
    print(f"✅ Migrated {len(students)} students")
    return student_mapping

def migrate_attendance(student_mapping):
    print("📝 Migrating attendance...")
    cursor.execute("SELECT * FROM attendance")
    attendance = cursor.fetchall()
    
    for record in attendance:
        if record['student_id'] in student_mapping:
            db.collection('attendance').add({
                'student_id': student_mapping[record['student_id']],
                'date': record['date'],
                'subject': record['subject'],
                'status': record['status'],
                'created_at': record['created_at'],
            })
    
    print(f"✅ Migrated {len(attendance)} attendance records")

# Run migration
if __name__ == '__main__':
    print("\n🔄 Starting Migration: MySQL → Firestore\n")
    
    try:
        course_map = migrate_courses()
        migrate_course_semesters(course_map)
        paper_map = migrate_papers(course_map)
        student_map = migrate_students(course_map, paper_map)
        migrate_attendance(student_map)
        
        print("\n✅ Migration Complete!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
    finally:
        cursor.close()
        conn.close()
```

### A.3 Run Migration

```bash
cd "d:\CODE PLAYGROUND\6th_Sem_Project\Main"
python migrate.py
```

---

## 🔄 Option B: Manual Migration (UI Method)

Agar script nahi chalni, manually migrate karo:

### B.1 Export MySQL Data to CSV

**Step 1: Get from MySQL**

```sql
-- Users CSV export
SELECT email, password, created_at, updated_at FROM users;
→ Save as: users.csv

-- Courses CSV export
SELECT id, name, code, created_at FROM courses;
→ Save as: courses.csv

-- Students CSV export
SELECT id, name, roll, email, phone, course_id, semester, admission_year, papers, created_at, updated_at FROM students;
→ Save as: students.csv

-- Attendance CSV export
SELECT student_id, date, subject, status, created_at FROM attendance;
→ Save as: attendance.csv
```

### B.2 Import to Firestore

**Via Firebase Console:**

1. Firestore Database > (Three dots) > Import Collection
2. Upload CSV file
3. Map columns to fields
4. Import

---

## 🔄 Option C: One-by-One Manual Entry

Agar data bahot kam hai, manually enter kar:

1. Firestore Console kholna
2. Each collection mein documents add karna
3. Fields fill karna (text fields directly, arrays carefully)

---

## ⚠️ Important Notes on Migration

### ID Mapping

**MySQL uses:** Integer IDs (1, 2, 3...)
**Firestore uses:** String Document IDs (auto-generated)

Migration script automatically handles this!

### Papers Field

MySQL mein papers JSON array mein tha:
```json
[1, 2, 3]
```

Firestore mein bhi JSON array hoga:
```json
["paper_doc_id_1", "paper_doc_id_2", "paper_doc_id_3"]
```

Script automatically converts!

### Timestamps

MySQL: `2024-01-15 10:30:00`
Firestore: Firestore timestamp or ISO string

Script converts to Firestore timestamp!

---

## ✅ Verification Checklist

Migration ke baad verify karo:

```
☐ Firestore Console mein sabhi collections visible hain
☐ Users count match kar raha hai
☐ Course count match kar raha hai
☐ Students count match kar raha hai
☐ Attendance records saved hain
☐ Papers array IDs valid hain
☐ Timestamps properly set hain
☐ App login kar raha hai successfully
☐ Students list load ho raha hai
☐ Attendance search working hai
```

---

## 🔄 Rollback (Agar galti ho)

Firestore mein data delete karna:

```javascript
// Firebase Console > Firestore
// Select collection
// Three dots > Delete collection
// OR select specific documents and delete
```

Dobara migration chalao!

---

## 📈 Migration Progress

```
Step 1: Courses (no dependencies)
        └─> 2 minutes
        
Step 2: Course Semesters (depends on courses)
        └─> 1 minute
        
Step 3: Papers (depends on courses)
        └─> 2 minutes
        
Step 4: Users (no dependencies)
        └─> 1 minute
        
Step 5: Students (depends on courses, papers)
        └─> 5 minutes
        
Step 6: Attendance (depends on students)
        └─> 3 minutes

Total: 14 minutes for ~1000 records
```

---

## 💡 Tips

1. **Backup lena:** Migration se pehle MySQL backup lelo
2. **Test environment:** First test server par try karo
3. **Incremental:** Chhote batches mein migrate karo agar data bahot hai
4. **Verify:** Har step ke baad count match karo

---

## 🆘 If Migration Fails

### Problem: "Connection refused" (MySQL)
```
→ Railway database running hai?
→ Credentials correct hain?
→ IP whitelisted hai?
→ Network connection hai?
```

### Problem: "Quota exceeded"
```
→ Firestore free tier limit exceed ho gaya
→ Wait 24 hours OR
→ Upgrade to paid plan OR
→ Reduce data volume
```

### Problem: "Field type mismatch"
```
→ CSV format incorrect hai
→ Firestore console mein field type manually set karo
→ Data re-import karo
```

### Problem: "Duplicate key error"
```
→ Email/Roll number duplicates ho sakti hain
→ MySQL mein check karo:
  SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;
→ Duplicates remove karo
→ Dobara migrate karo
```

---

## 📝 Migration Checklist

Before migration:
- [ ] MySQL backup liya
- [ ] Firebase setup complete
- [ ] serviceAccountKey.json ready
- [ ] Firestore collections created (atleast empty)
- [ ] migrate.py script ready

During migration:
- [ ] migrate.py execution status check karo
- [ ] Terminal mein errors dekho
- [ ] Firestore Console mein data verify karo

After migration:
- [ ] App restart karo
- [ ] Login test karo
- [ ] Students list load karo
- [ ] Attendance mark karo
- [ ] Reports generate karo

---

## ✅ Success Criteria

Migration successful jab:
1. ✅ Firestore mein same data count
2. ✅ All collections properly populated
3. ✅ IDs properly mapped
4. ✅ Arrays (papers) properly migrated
5. ✅ App working perfectly
6. ✅ No data loss

---

**Migration dene ke baad, MySQL database ko retire kar sakte ho!** 🎉

Happy migrating! 🚀
