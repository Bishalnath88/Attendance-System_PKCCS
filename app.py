"""
========================================
STUDENT ATTENDANCE SYSTEM - BACKEND API
========================================
Flask-based REST API for managing student attendance records.

Features:
- User authentication and session management
- Student CRUD operations  
- Attendance tracking
- Firebase Firestore database integration
- CORS support for frontend

Author: Your Name
Version: 2.0 (Firebase Migration)
========================================
"""

from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
import json
import os
import re
import secrets
import jwt

from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

# Import Firebase configuration
from firebase_config import (
    get_db, get_users_ref, get_courses_ref, 
    get_course_semesters_ref, get_papers_ref, 
    get_students_ref, get_attendance_ref
)


def load_env_file():
    # Load environment variables from .env file for secure credential storage
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# Load environment variables at startup
load_env_file()

# Initialize Flask app with CORS support for frontend communication
app = Flask(__name__, static_folder='.', static_url_path='')  
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
)

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return json_error("Endpoint not found.", 404)

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors"""
    return json_error("Method not allowed for this endpoint.", 405)

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors with detailed logging"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"500 ERROR: {error_trace}", flush=True)
    return json_error("Internal server error. Please check server logs.", 500)

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"UNHANDLED ERROR: {error_trace}", flush=True)
    return json_error("An unexpected error occurred. Please try again later.", 500)

# EMAIL REGEX PATTERN - validates email format
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Session timeout duration in hours
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "24"))
# JWT secret key - use environment variable or generate random one for testing
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))


def json_error(message, status_code=400):
    """
    Create standardized JSON error response
    Args:
        message: Error message string
        status_code: HTTP status code (default 400 Bad Request)
    Returns: Tuple of (JSON response, status code)
    """
    return jsonify({"message": message}), status_code


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


def add_batch_to_student(student, courses_cache=None):
    """Add batch information and current semester to a student record"""
    try:
        if 'admission_year' not in student:
            return student
            
        student = student.copy()
        admission_year = student.get('admission_year')
        course_id = student.get('course_id')
        
        # Use cached course or query if no cache provided
        if courses_cache and course_id in courses_cache:
            course = courses_cache[course_id]
        else:
            # Fallback: Query course if not in cache
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
        
        # Add current semester (auto-calculated based on admission year and course type)
        student['current_semester'] = calculate_current_semester(admission_year, is_bsc)
        
        return student
    except:
        return student


def calculate_current_semester(admission_year, is_bsc=False):
    """Calculate current semester based on admission year and course type
    
    Academic Calendar (Aug-Jul batches):
    - Year 1: Sem 1 + 2 (Aug-Jul)
    - Year 2: Sem 3 + 4 (Aug-Jul)
    - Year 3: Sem 5 + 6 (Aug-Jul)
    - Year 4 (BSc only): Sem 7 + 8 (Aug-Jul)
    
    Total Semesters:
    - BSc: 8 semesters (4 years)
    - Other: 6 semesters (3 years)
    
    Returns: Current semester number (capped at max for course type)
    """
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # Determine which academic year we're in
    if current_month < 8:  # Jan-Jul: same academic year as last August
        academic_year_start = current_year - 1
    else:  # Aug-Dec: current academic year
        academic_year_start = current_year
    
    # How many years since admission?
    years_since_admission = academic_year_start - admission_year
    
    # Calculate current semester
    if current_month < 8:  # Jan-Jul = even semester (2, 4, 6, 8...)
        semester = years_since_admission * 2 + 2
    else:  # Aug-Dec = odd semester (1, 3, 5, 7...)
        semester = years_since_admission * 2 + 1
    
    # Cap at max semesters based on course type
    max_semester = 8 if is_bsc else 6
    semester = min(semester, max_semester)
    
    return max(1, semester)  # Ensure at least semester 1


# ========== DATA VALIDATION FUNCTIONS ==========
def normalize_email(raw_email):
    """Normalize email: lowercase and strip whitespace"""
    return str(raw_email or "").strip().lower()


def is_valid_email(email):
    """Validate email format using regex pattern"""
    return bool(EMAIL_PATTERN.match(email))


def normalize_text(value):
    """Normalize text: strip whitespace"""
    return str(value or "").strip()


def is_hashed_password(password):
    # Check if password is already hashed (uses werkzeug hash format)
    return str(password).startswith(("pbkdf2:", "scrypt:", "argon2:"))


# ========== SESSION & TOKEN MANAGEMENT ==========
def issue_token(user):
    """Generate JWT token for user"""
    payload = {
        "user_id": user.get("id"),
        "email": user["email"],
        "exp": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def get_bearer_token():
    """Extract Bearer token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(view):
    """Decorator to require authentication for protected endpoints"""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return json_error("Authentication required.", 401)
        
        payload = verify_token(token)
        if not payload:
            return json_error("Invalid or expired token.", 401)
        
        g.auth_token = token
        g.user_id = payload.get("user_id")
        g.user_email = payload["email"]
        return view(*args, **kwargs)

    return wrapped_view


def parse_json_body(expected_type=dict):
    # Parse and validate JSON request body
    data = request.get_json(silent=True)
    if not isinstance(data, expected_type):
        return None
    return data


def validate_login_payload(data):
    # Validate login request payload
    email = normalize_email(data.get("email"))
    password = normalize_text(data.get("password"))

    if not email or not password:
        return None, None, "Email and password are required."

    if not is_valid_email(email):
        return None, None, "Please enter a valid email address."

    return email, password, None


def validate_student_payload(data):
    # Validate student creation/update payload
    name = normalize_text(data.get("name"))
    roll = normalize_text(data.get("roll"))
    course_id = data.get("course_id")
    semester = data.get("semester")
    admission_year = data.get("admission_year")
    papers = data.get("papers", [])
    email = normalize_email(data.get("email"))
    phone = normalize_text(data.get("phone", ""))

    # Core required fields (name, roll, course_id, semester, email are mandatory)
    if not all([name, roll, course_id, semester, email]):
        return None, "All student fields (name, roll, course, semester, email) are required."

    if not is_valid_email(email):
        return None, "Please enter a valid student email address."

    # Validate phone number format only if provided (optional field)
    if phone and not re.match(r"^[\d\s+\-()]{10,15}$", phone):
        return None, "Please enter a valid phone number (10-15 digits)."

    try:
        course_id = str(course_id)
        semester = int(semester)
        # admission_year is optional - use current year as default if not provided
        if admission_year:
            admission_year = int(admission_year)
        else:
            admission_year = datetime.now().year
    except (TypeError, ValueError):
        return None, "Course ID, semester, and admission year must be valid numbers."

    # Validate admission year is reasonable (within last 20 years or next 2 years)
    current_year = datetime.now().year
    if admission_year < current_year - 20 or admission_year > current_year + 2:
        return None, f"Admission year must be between {current_year - 20} and {current_year + 2}."

    # Validate semester is in reasonable range (1-8 for any course)
    # Actual validation happens in endpoint when checking against course_semesters collection
    if semester < 1 or semester > 8:
        return None, "Semester must be between 1 and 8."

    if not isinstance(papers, list) or len(papers) < 1 or len(papers) > 4:
        return None, "You must select between 1 and 4 papers."

    return {
        "name": name,
        "roll": roll,
        "course_id": course_id,
        "semester": semester,
        "admission_year": admission_year,
        "papers": papers,
        "email": email,
        "phone": phone,
    }, None


def parse_attendance_date(raw_date):
    # Parse date string in YYYY-MM-DD format
    try:
        return datetime.strptime(str(raw_date), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def validate_attendance_records(records):
    # Validate attendance records array
    if not records:
        return None, "Attendance payload is empty."

    normalized_records = []
    # Valid attendance status values
    allowed_statuses = {"present", "absent", "late"}

    # Validate each attendance record
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            return None, f"Attendance item {index} is invalid."

        # Parse student ID
        raw_student_id = record.get("student_id", record.get("studentId"))
        student_id = raw_student_id  # In Firestore, student_id is the document ID
        
        # Parse and validate attendance date
        attendance_date = parse_attendance_date(record.get("date"))
        if attendance_date is None:
            return None, f"Attendance item {index} must use YYYY-MM-DD date format."

        # Validate subject and status
        subject = normalize_text(record.get("subject"))
        status = normalize_text(record.get("status")).lower()

        if not subject:
            return None, f"Attendance item {index} is missing a subject."

        if status not in allowed_statuses:
            return None, f"Attendance item {index} has an invalid status."

        normalized_records.append({
            "student_id": student_id,
            "date": attendance_date.isoformat(),
            "subject": subject,
            "status": status,
        })

    return normalized_records, None


def get_course_end_date(admission_year, course_duration):
    """Calculate course end date (July of final year)
    
    Academic Calendar:
    - Batch starts: August (mid-year)
    - Batch ends: July (mid-year)
    - 2 semesters per year = 1 academic year
    
    Course end = admission_year + duration, July 31st
    """
    end_year = admission_year + course_duration
    return date(end_year, 7, 31)


def has_course_ended(admission_year, course_duration):
    """Check if a student's course has ended based on today's date"""
    end_date = get_course_end_date(admission_year, course_duration)
    today = date.today()
    return today > end_date


# ========== AUTHENTICATION ENDPOINTS ==========
@app.route("/register", methods=["POST"])
def register():
    # Register new user account - POST /register
    data = parse_json_body(dict)
    if data is None:
        return json_error("A valid JSON body is required.")

    email, password, error_message = validate_login_payload(data)
    if error_message:
        return json_error(error_message)

    # Validate password length
    if len(password) < 6:
        return json_error("Password must be at least 6 characters long.")

    try:
        db = get_db()
        users_ref = get_users_ref()
        
        # Check if email already exists
        query = users_ref.where("email", "==", email).limit(1)
        docs = list(query.stream())
        
        if docs:
            return json_error("An account with this email already exists.", 409)

        # Hash password and create user
        hashed_password = generate_password_hash(password)
        users_ref.add({
            "email": email,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        
        return jsonify({"message": "Registration successful. Please sign in."}), 201
    except Exception as e:
        print(f"Registration error: {e}", flush=True)
        return json_error("Unable to register right now. Please try again later.", 500)


@app.route("/login", methods=["POST"])
def login():
    # User login - authenticate and issue session token - POST /login
    data = parse_json_body(dict)
    if data is None:
        return json_error("A valid JSON body is required.")

    email, password, error_message = validate_login_payload(data)
    if error_message:
        return json_error(error_message)

    try:
        # Query user by email
        users_ref = get_users_ref()
        query = users_ref.where("email", "==", email).limit(1)
        docs = list(query.stream())

        if not docs:
            return json_error("Invalid email or password.", 401)

        user_doc = docs[0]
        user = user_doc.to_dict()
        user['id'] = user_doc.id

        # Verify password (supports both hashed and plain for migration)
        stored_password = user.get("password", "")
        password_is_valid = (
            check_password_hash(stored_password, password)
            if is_hashed_password(stored_password)
            else stored_password == password
        )

        if not password_is_valid:
            return json_error("Invalid email or password.", 401)

        # Upgrade plain-text password to hashed (backward compatibility)
        if stored_password and not is_hashed_password(stored_password):
            upgraded_password = generate_password_hash(password)
            users_ref.document(user['id']).update({
                "password": upgraded_password,
                "updated_at": datetime.utcnow(),
            })

        # Issue new session token
        token = issue_token(user)
        return jsonify({
            "message": "Login successful.",
            "token": token,
            "email": email,
        })
    except Exception as e:
        print(f"Login error: {e}", flush=True)
        return json_error("Unable to log in right now. Please try again later.", 500)


@app.route("/logout", methods=["POST"])
@require_auth
def logout():
    # User logout - with JWT, nothing to invalidate server-side
    # Client should clear localStorage token
    return jsonify({"message": "Logged out successfully."})


@app.route("/me", methods=["GET"])
@require_auth
def me():
    # Current user info - retrieve authenticated user details - GET /me
    return jsonify({"email": g.user_email})


# ========== STUDENTS ENDPOINTS ==========
@app.route("/students", methods=["GET"])
@require_auth
def get_students():
    # Get all students - retrieve complete student roster - GET /students
    # Optional query parameter: admission_year (to filter by batch)
    admission_year = request.args.get("admission_year", type=int)
    
    try:
        db = get_db()
        students_ref = get_students_ref()
        
        # Fetch all courses ONCE for batch calculation
        courses_cache = {}
        for course_doc in get_courses_ref().stream():
            course_data = course_doc.to_dict()
            course_data['id'] = course_doc.id
            courses_cache[course_doc.id] = course_data
        
        if admission_year:
            # Fetch students with the specified admission year
            query = students_ref.where("admission_year", "==", admission_year)
        else:
            # Retrieve all students
            query = students_ref
        
        docs = list(query.stream())
        data = []
        
        for doc in docs:
            student_dict = serialize_doc(doc)
            
            # Add batch info using cached courses (avoid N+1 query problem)
            student_dict = add_batch_to_student(student_dict, courses_cache)
            
            data.append(student_dict)
        
        # Sort client-side by name and roll
        data.sort(key=lambda x: (x.get('name', ''), x.get('roll', '')))
        
        return jsonify(data)
    except Exception as error:
        print(f"Error in get_students: {error}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        return json_error("Unable to load students. Please try again later.", 500)


@app.route("/students", methods=["POST"])
@require_auth
def add_student():
    # Add new student - create new student record - POST /students
    data = parse_json_body(dict)
    if data is None:
        return json_error("A valid JSON body is required.")

    student, error_message = validate_student_payload(data)
    if error_message:
        return json_error(error_message)

    try:
        db = get_db()
        
        # Verify course exists
        course_doc = get_courses_ref().document(student["course_id"]).get()
        if not course_doc.exists:
            return json_error("Selected course does not exist.", 404)
        
        # Verify semester exists for this course
        query = get_course_semesters_ref().where("course_id", "==", student["course_id"]).where("semester", "==", student["semester"]).limit(1)
        if not list(query.stream()):
            return json_error("Selected semester is not available for this course.", 404)
        
        # Verify all papers exist for this course/semester
        if student["papers"]:
            papers_docs = []
            for paper_id in student["papers"]:
                paper_doc = get_papers_ref().document(paper_id).get()
                if paper_doc.exists:
                    paper_data = paper_doc.to_dict()
                    if paper_data.get("course_id") == student["course_id"] and paper_data.get("semester") == student["semester"]:
                        papers_docs.append(paper_doc)
            
            if len(papers_docs) != len(student["papers"]):
                return json_error("One or more selected papers do not exist for this course/semester.", 404)
        
        # Check if roll or email already exists
        query = get_students_ref().where("roll", "==", student["roll"]).limit(1)
        if list(query.stream()):
            return json_error("Roll number already exists.", 409)
        
        query = get_students_ref().where("email", "==", student["email"]).limit(1)
        if list(query.stream()):
            return json_error("Email already exists.", 409)

        # Create student document
        doc_ref = get_students_ref().add({
            "name": student["name"],
            "roll": student["roll"],
            "course_id": student["course_id"],
            "semester": student["semester"],
            "admission_year": student["admission_year"],
            "papers": student["papers"],
            "email": student["email"],
            "phone": student["phone"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        # Fetch and return created student
        created_doc = get_students_ref().document(doc_ref[1].id).get()
        created_student = add_batch_to_student(serialize_doc(created_doc))
        return jsonify({
            "message": "Student added successfully.",
            "student": created_student,
        }), 201
    except Exception as e:
        print(f"Add student error: {e}", flush=True)
        return json_error("Unable to add the student right now.", 500)


@app.route("/students/<student_id>", methods=["PUT"])
@require_auth
def update_student(student_id):
    # Update student - modify existing student record - PUT /students/{student_id}
    data = parse_json_body(dict)
    if data is None:
        return json_error("A valid JSON body is required.")

    student, error_message = validate_student_payload(data)
    if error_message:
        return json_error(error_message)

    try:
        # Check if student exists
        student_doc = get_students_ref().document(student_id).get()
        if not student_doc.exists:
            return json_error("Student not found.", 404)

        # Verify course exists
        course_doc = get_courses_ref().document(student["course_id"]).get()
        if not course_doc.exists:
            return json_error("Selected course does not exist.", 404)
        
        # Verify semester exists for this course
        query = get_course_semesters_ref().where("course_id", "==", student["course_id"]).where("semester", "==", student["semester"]).limit(1)
        if not list(query.stream()):
            return json_error("Selected semester is not available for this course.", 404)
        
        # Verify all papers exist for this course/semester
        if student["papers"]:
            papers_docs = []
            for paper_id in student["papers"]:
                paper_doc = get_papers_ref().document(paper_id).get()
                if paper_doc.exists:
                    paper_data = paper_doc.to_dict()
                    if paper_data.get("course_id") == student["course_id"] and paper_data.get("semester") == student["semester"]:
                        papers_docs.append(paper_doc)
            
            if len(papers_docs) != len(student["papers"]):
                return json_error("One or more selected papers do not exist for this course/semester.", 404)

        # Ensure new roll/email don't conflict with other students
        query = get_students_ref().where("roll", "==", student["roll"]).limit(1)
        existing_docs = [doc for doc in query.stream() if doc.id != student_id]
        if existing_docs:
            return json_error("Roll number already belongs to another student.", 409)
        
        query = get_students_ref().where("email", "==", student["email"]).limit(1)
        existing_docs = [doc for doc in query.stream() if doc.id != student_id]
        if existing_docs:
            return json_error("Email already belongs to another student.", 409)

        # Update student
        get_students_ref().document(student_id).update({
            "name": student["name"],
            "roll": student["roll"],
            "course_id": student["course_id"],
            "semester": student["semester"],
            "admission_year": student["admission_year"],
            "papers": student["papers"],
            "email": student["email"],
            "phone": student["phone"],
            "updated_at": datetime.utcnow(),
        })

        # Fetch and return updated student
        updated_doc = get_students_ref().document(student_id).get()
        updated_student = add_batch_to_student(serialize_doc(updated_doc))
        return jsonify({
            "message": "Student updated successfully.",
            "student": updated_student,
        })
    except Exception as e:
        print(f"Update student error: {e}", flush=True)
        return json_error("Unable to update the student right now.", 500)


@app.route("/students/<student_id>", methods=["DELETE"])
@require_auth
def delete_student(student_id):
    # Delete student - remove student record and related attendance - DELETE /students/{student_id}
    try:
        db = get_db()
        
        # Verify student exists before attempting deletion
        student_doc = get_students_ref().document(student_id).get()
        if not student_doc.exists:
            return json_error("Student not found.", 404)

        # Delete all attendance records for this student (cascade delete)
        attendance_query = get_attendance_ref().where("student_id", "==", student_id)
        for doc in attendance_query.stream():
            get_attendance_ref().document(doc.id).delete()
        
        # Delete the student record itself
        get_students_ref().document(student_id).delete()
        
        return jsonify({"message": "Student deleted successfully."})
    except Exception as e:
        print(f"Delete student error: {e}", flush=True)
        return json_error("Unable to delete the student right now.", 500)


# ========== COURSES ENDPOINTS ==========
@app.route("/courses", methods=["GET"])
@require_auth
def get_courses():
    # Get all available courses - GET /courses
    try:
        docs = list(get_courses_ref().order_by("name").stream())
        data = []
        for doc in docs:
            course = serialize_doc(doc)
            data.append(course)
        return jsonify(data)
    except Exception as e:
        print(f"Get courses error: {e}", flush=True)
        return json_error("Unable to load courses right now.", 500)


# ========== COURSE SEMESTERS ENDPOINTS ==========
@app.route("/courses/<course_id>/semesters", methods=["GET"])
@require_auth
def get_semesters(course_id):
    # Get semesters for a specific course - GET /courses/{course_id}/semesters
    try:
        # Verify course exists
        course_doc = get_courses_ref().document(course_id).get()
        if not course_doc.exists:
            return json_error("Course not found.", 404)
        
        query = get_course_semesters_ref().where("course_id", "==", course_id)
        docs = list(query.stream())
        data = [doc.to_dict().get("semester") for doc in docs]
        return jsonify(sorted(set(data)))
    except Exception as e:
        print(f"Get semesters error: {e}", flush=True)
        return json_error("Unable to load semesters right now.", 500)


# ========== PAPERS ENDPOINTS ==========
@app.route("/courses/<course_id>/semesters/<int:semester>/papers", methods=["GET"])
@require_auth
def get_papers(course_id, semester):
    # Get papers for a specific course and semester - GET /courses/{course_id}/semesters/{semester}/papers
    try:
        # Verify course exists
        course_doc = get_courses_ref().document(course_id).get()
        if not course_doc.exists:
            return json_error("Course not found.", 404)
        
        # Verify semester exists for this course
        query = get_course_semesters_ref().where("course_id", "==", course_id).where("semester", "==", semester).limit(1)
        if not list(query.stream()):
            return json_error("Semester not found for this course.", 404)
        
        query = get_papers_ref().where("course_id", "==", course_id).where("semester", "==", semester)
        docs = list(query.stream())
        data = [serialize_doc(doc) for doc in docs]
        # Sort by name client-side
        data.sort(key=lambda x: x.get('name', ''))
        return jsonify(data)
    except Exception as e:
        print(f"Get papers error: {e}", flush=True)
        return json_error("Unable to load papers right now.", 500)


@app.route("/admission-years", methods=["GET"])
@require_auth
def get_admission_years():
    # Get list of admission years for dropdown - GET /admission-years
    current_year = datetime.now().year
    # Generate years from 20 years ago to 2 years in future
    years = list(range(current_year - 20, current_year + 3))
    # Reverse to show newest first
    years.reverse()
    return jsonify(years)


@app.route("/batches", methods=["GET"])
@require_auth
def get_batches():
    """Get all available batches using 4-year duration (BSc standard)
    
    Returns only 4-year batch ranges: 2023-2027, 2024-2028, etc.
    Each batch contains:
    - BSc students: attendance until 4th year
    - Other courses: attendance until 3rd year (then stop)
    """
    try:
        # Get all unique admission years that have students
        students_ref = get_students_ref()
        docs = list(students_ref.stream())
        
        admission_years = set()
        for doc in docs:
            admission_year = doc.to_dict().get('admission_year')
            if admission_year:
                admission_years.add(admission_year)
        
        batches = []
        for admission_year in sorted(admission_years, reverse=True):
            # Calculate batch using 4-year duration (BSc standard)
            end_year = admission_year + 4
            batches.append({
                "batch": f"{admission_year}-{end_year}",
                "admission_year": admission_year,
                "end_year": end_year,
                "duration": 4
            })
        
        return jsonify(batches)
    except Exception as e:
        print(f"Error fetching batches: {e}")
        return jsonify([]), 500


@app.route("/attendance", methods=["POST"])
@require_auth
def save_attendance():
    # Save attendance records - create or update attendance entries - POST /attendance
    records = parse_json_body(list)
    if records is None:
        return json_error("Attendance must be sent as a JSON array.")

    normalized_records, error_message = validate_attendance_records(records)
    if error_message:
        return json_error(error_message)

    try:
        db = get_db()

        # Extract and validate all student IDs
        student_ids = sorted({record["student_id"] for record in normalized_records})
        valid_student_ids = set()
        
        students_ref = get_students_ref()
        for student_id in student_ids:
            if students_ref.document(student_id).get().exists:
                valid_student_ids.add(student_id)

        # Check for any invalid student IDs
        missing_student_ids = sorted(set(student_ids) - valid_student_ids)
        if missing_student_ids:
            return json_error(
                f"Unknown student IDs: {', '.join(str(sid) for sid in missing_student_ids)}.",
                404,
            )

        # Process each attendance record: create if new, update if exists
        created_count = 0
        updated_count = 0
        attendance_ref = get_attendance_ref()

        for record in normalized_records:
            # Check if attendance record already exists for this student/date/subject
            query = attendance_ref.where("student_id", "==", record["student_id"]).where("date", "==", record["date"]).where("subject", "==", record["subject"]).limit(1)
            existing_docs = list(query.stream())

            if existing_docs:
                # Record exists - update the status
                attendance_ref.document(existing_docs[0].id).update({"status": record["status"]})
                updated_count += 1
            else:
                # Record doesn't exist - create new entry
                attendance_ref.add({
                    "student_id": record["student_id"],
                    "date": record["date"],
                    "subject": record["subject"],
                    "status": record["status"],
                    "created_at": datetime.utcnow(),
                })
                created_count += 1

        return jsonify({
            "message": "Attendance saved successfully.",
            "created": created_count,
            "updated": updated_count,
        })
    except Exception as e:
        print(f"Save attendance error: {e}", flush=True)
        return json_error("Unable to save attendance right now.", 500)


@app.route("/attendance", methods=["GET"])
@require_auth
def get_attendance():
    """
    Get attendance records - retrieve and filter attendance history
    GET /attendance?start_date=2024-01-01&end_date=2024-01-31&subject=Math (requires authentication)
    Query Parameters:
        - start_date (optional): Filter records from this date (YYYY-MM-DD)
        - end_date (optional): Filter records until this date (YYYY-MM-DD)
        - subject (optional): Filter by subject name
    Returns: 200 OK with filtered array of attendance records, 500 on database error
    """
    start_date = normalize_text(request.args.get("start_date"))
    end_date = normalize_text(request.args.get("end_date"))
    subject_filter = normalize_text(request.args.get("subject"))

    try:
        # Fetch all attendance records from Firestore
        attendance_ref = get_attendance_ref()
        docs = list(attendance_ref.stream())
        
        # Deduplicate records by (student_id, date, subject) key
        deduplicated_records = {}
        for doc in docs:
            serialized = serialize_doc(doc)
            key = (
                serialized.get("student_id"),
                serialized.get("date"),
                serialized.get("subject"),
            )
            deduplicated_records[key] = serialized

        records = list(deduplicated_records.values())

        # Apply optional filters
        if start_date:
            records = [record for record in records if record["date"] >= start_date]
        if end_date:
            records = [record for record in records if record["date"] <= end_date]
        if subject_filter:
            records = [record for record in records if record["subject"] == subject_filter]

        # Sort by date (descending), subject, and student_id
        records.sort(
            key=lambda record: (
                record.get("date", ""),
                record.get("subject", ""),
                record.get("student_id", ""),
            ),
            reverse=True,
        )
        return jsonify(records)
    except Exception as e:
        print(f"Get attendance error: {e}", flush=True)
        return json_error("Unable to load attendance records right now.", 500)


# ========== STATIC FILE SERVING ==========
@app.route('/')
def index():
    """
    Serve index.html - entry point for web application
    GET /
    Returns: HTML index page which handles client-side routing
    """
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """
    Serve static files and HTML pages - generic file serving endpoint
    GET /<path:path>
    Returns: Requested file if it exists, 404 Not Found otherwise
    """
    if os.path.exists(os.path.join('.', path)):
        return send_from_directory('.', path)
    # Try to serve as HTML file if extension missing
    if os.path.exists(os.path.join('.', path + '.html')):
        return send_from_directory('.', path + '.html')
    return json_error("Not found", 404)


# ========== APPLICATION ENTRY POINT ==========
if __name__ == "__main__":
    """
    Flask application entry point - start web server
    
    Initializes and runs the Flask development or production server with
    configuration from environment variables:
    - PORT or FLASK_PORT: Server port (default 5000)
    - FLASK_HOST: Server host/address (default 0.0.0.0 = all interfaces)
    - FLASK_DEBUG: Enable debug mode with auto-reload (default is off)
    
    Environment variables are read from .env file (if present) or system environment.
    """
    port = int(os.environ.get("PORT", os.environ.get("FLASK_PORT", "5000")))
    app.run(
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=port,
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
