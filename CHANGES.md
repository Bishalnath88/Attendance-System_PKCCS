# Student Management System - Recent Changes

## Overview
The student management system has been updated to replace the simple "class" field with a more comprehensive course, semester, and papers system. Students can now select from multiple courses (BSc, BCA, Bvoc IT, Bvoc Food, etc.), choose a semester (1-8), and select 1-4 papers for each course/semester combination.

---

## Database Changes

### New Tables Created

#### 1. `courses`
Stores available courses in the system.
```sql
- id (INT, Primary Key)
- name (VARCHAR(100), Unique)
- code (VARCHAR(50), Unique)
- created_at (TIMESTAMP)
```

#### 2. `course_semesters`
Links courses with their available semesters (1-8).
```sql
- id (INT, Primary Key)
- course_id (INT, Foreign Key → courses.id)
- semester (INT)
- created_at (TIMESTAMP)
- Unique: (course_id, semester)
```

#### 3. `papers`
Stores individual papers/subjects for each course and semester.
```sql
- id (INT, Primary Key)
- course_id (INT, Foreign Key → courses.id)
- semester (INT)
- name (VARCHAR(255))
- code (VARCHAR(50))
- created_at (TIMESTAMP)
- Unique: (course_id, semester, name)
```

### Modified Table

#### `students`
Replaced the `class` field with course/semester/papers structure.

**Old Schema:**
```sql
- id, name, roll, class, email, created_at, updated_at
```

**New Schema:**
```sql
- id, name, roll, course_id (FK), semester, papers (JSON), email, created_at, updated_at
```

**Key Changes:**
- Removed: `class` (VARCHAR(100))
- Added: `course_id` (INT, Foreign Key → courses.id)
- Added: `semester` (INT)
- Added: `papers` (JSON array of paper IDs)

---

## Backend API Changes

### New Endpoints

#### 1. Get All Courses
```
GET /courses
Response: Array of courses with id, name, code
```

#### 2. Get Semesters for a Course
```
GET /courses/{course_id}/semesters
Response: Array of semester numbers (e.g., [1, 2, 3, 4, 5, 6, 7, 8])
```

#### 3. Get Papers for a Course and Semester
```
GET /courses/{course_id}/semesters/{semester}/papers
Response: Array of papers with id, name, code
```

### Modified Endpoints

#### Student Creation/Update
**Request Body:**
```json
{
  "name": "String",
  "roll": "String",
  "course_id": Number,
  "semester": Number,
  "papers": [Number, Number, ...],
  "email": "String"
}
```

**Validation:**
- `course_id`: Must reference an existing course
- `semester`: Must exist in course_semesters for the given course
- `papers`: Must be an array of 1-4 paper IDs that exist for the course/semester
- All fields are required

---

## Frontend Changes

### Students List Page (students.html)

#### Form: "Add/Edit Student"

**New Form Fields:**

1. **Course** (Required)
   - Type: Dropdown select
   - Populated from API: `/courses`
   - Triggers: Dynamic update of semester options

2. **Semester** (Required)
   - Type: Dropdown select
   - Populated from API: `/courses/{courseId}/semesters`
   - Initially disabled until a course is selected
   - Triggers: Dynamic update of paper options

3. **Papers** (Required)
   - Type: Checkbox list (1-4 selection required)
   - Dynamically populated from API: `/courses/{courseId}/semesters/{semester}/papers`
   - Shows label with current selection count: "Papers (Select 1-4) - Selected: X"
   - Initially hidden until course and semester are selected
   - Each paper checkbox shows: Paper Name (Paper Code)

**Removed Fields:**
- Class (text input)

#### Table: "All Students"

**Column Changes:**
- Removed: Class column
- Added: Course column (shows course name)
- Added: Semester column (shows semester number)

**Columns Order:**
1. Name
2. Roll No
3. Course
4. Semester
5. Email
6. Actions

**Search Enhancement:**
- Now searches by: name, roll number, **course name**, email
- Updated placeholder: "Search by name, roll number, course, or email"

---

## Sample Data Initialization

The `init_db.py` script now initializes the database with sample data:

### Sample Courses (4 total)
1. **Bachelor of Science** (BSc)
2. **Bachelor of Computer Applications** (BCA)
3. **Bachelor of Vocational Studies - Information Technology** (Bvoc IT)
4. **Bachelor of Vocational Studies - Food Technology** (Bvoc Food)

### Sample Semesters
- Each course has 8 semesters (1-8)

### Sample Papers
Each course and semester has 4 sample papers with codes:

**Example - BSc Semester 1:**
- Physics I (PHY101)
- Chemistry I (CHE101)
- Mathematics I (MAT101)
- English (ENG101)

**Example - BCA Semester 2:**
- Object Oriented Programming (CS201)
- Database Management (CS202)
- Web Technologies (CS203)
- Data Structures (CS204)

---

## How to Use

### 1. Initialize Database
```bash
python init_db.py
```
This creates all tables and inserts sample courses, semesters, and papers.

### 2. Add a New Student
1. Click "Add Student" button
2. Fill in Name and Roll Number
3. Select a Course from dropdown
4. Select a Semester (available semesters for the course)
5. Select 1-4 Papers from checkboxes
6. Enter Email address
7. Click "Save Student"

### 3. Edit a Student
1. Click edit icon next to student
2. Form auto-loads with current selections
3. Semesters and papers refresh based on selected course
4. Modify as needed and save

### 4. Display
- Students table shows Course name and Semester number
- Search filters by course name

---

## Validation Rules

### Papers Selection
- **Minimum**: 1 paper
- **Maximum**: 4 papers
- All selected papers must exist for the chosen course/semester
- Error message if selection is outside 1-4 range

### Course and Semester
- Course must exist in the courses table
- Semester must exist in course_semesters for the selected course
- Semester must be between 1-8

### Email and Roll
- Email must be unique
- Roll number must be unique
- Email format validation applied

---

## File Changes Summary

### Created Files
- CHANGES.md (this file)

### Modified Files
- `schema.sql` - New table definitions
- `app.py` - New endpoints, updated validation, json import
- `students.html` - Form redesign, table columns, search, JavaScript
- `init_db.py` - New table creation, sample data insertion

---

## Testing Checklist

- [ ] Database initialization runs without errors
- [ ] Courses appear in the Course dropdown
- [ ] Selecting a course populates semesters
- [ ] Selecting a semester populates papers
- [ ] Can add a student with course, semester, 1-4 papers
- [ ] Student displays correctly in table with course and semester
- [ ] Can edit a student and modify course/semester/papers
- [ ] Search filters by course name
- [ ] Cannot save with 0 or 5+ papers
- [ ] Cannot save if any field is empty
- [ ] Paper count shows correctly in label

---

## Notes

- Papers are stored as JSON array in the students table for flexibility
- Each course can have up to 8 semesters
- Each semester can have 4 papers per student selection
- The system maintains referential integrity through foreign keys
- Old class field has been completely removed from the system

