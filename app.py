"""
========================================
STUDENT ATTENDANCE SYSTEM - BACKEND API
========================================
Flask-based REST API for managing student attendance records.

Features:
- User authentication and session management
- Student CRUD operations  
- Attendance tracking
- MySQL database integration
- CORS support for frontend

Author: Your Name
Version: 1.0
========================================
"""

from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
import json
import os
import re
import secrets

from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash


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

# EMAIL REGEX PATTERN - validates email format
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Session timeout duration in hours
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "12"))
# In-memory token storage for active sessions
ACTIVE_TOKENS = {}
# Minimum password column size for hashed passwords
PASSWORD_COLUMN_MIN_LENGTH = 255


def get_db_config():
    # Get database configuration from environment variables
    return {
        "host": os.environ.get("ATTENDANCE_DB_HOST", "localhost"),
        "user": os.environ.get("ATTENDANCE_DB_USER", "root"),
        "password": os.environ.get("ATTENDANCE_DB_PASSWORD"),
        "database": os.environ.get("ATTENDANCE_DB_NAME", "attendance_system"),
        "port": int(os.environ.get("ATTENDANCE_DB_PORT", "3306")),
    }


def ensure_database_schema():
    """
    Ensures the database has all required columns and proper configurations.
    This function is called on every database connection to keep schema up-to-date.
    """
    conn = cursor = None
    try:
        conn = mysql.connector.connect(**get_db_config())
        cursor = conn.cursor(dictionary=True)
        
        # Step 1: Fix password column size if needed
        cursor.execute("SHOW COLUMNS FROM users LIKE 'password'")
        password_column = cursor.fetchone()
        
        if password_column:
            column_type = str(password_column.get("Type", "")).lower()
            match = re.search(r"varchar\((\d+)\)", column_type)
            
            # If password column is too small for hashed passwords, enlarge it
            if match and int(match.group(1)) < PASSWORD_COLUMN_MIN_LENGTH:
                cursor.execute(
                    f"ALTER TABLE users MODIFY COLUMN password VARCHAR({PASSWORD_COLUMN_MIN_LENGTH})"
                )
                conn.commit()
        
        # Step 2: Add admission_year column if it's missing from students table
        cursor.execute(
            "SELECT COUNT(*) as col_count FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME='students' AND COLUMN_NAME='admission_year'"
        )
        result = cursor.fetchone()
        
        if result and result['col_count'] == 0:
            # Column doesn't exist, so add it
            cursor.execute(
                "ALTER TABLE students ADD COLUMN admission_year INT DEFAULT 2026 AFTER semester"
            )
            # Also create an index for faster queries
            cursor.execute(
                "CREATE INDEX idx_admission_year ON students(admission_year)"
            )
            conn.commit()
    
    except mysql.connector.Error as e:
        # Database might not be ready yet, which is OK
        # System will try again on next request
        pass
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def get_db():
    # Get a new database connection
    ensure_database_schema()
    return mysql.connector.connect(**get_db_config())


def close_db(conn=None, cursor=None, rollback=False):
    # Properly close database cursor and connection
    if cursor is not None:
        cursor.close()

    if conn is not None:
        if rollback:
            conn.rollback()
        conn.close()


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


def serialize_row(row):
    """Convert database row to JSON-serializable format"""
    return {key: serialize_value(value) for key, value in row.items()}


def add_batch_to_student(student):
    """Add batch information and current semester to a student record"""
    conn = cursor = None
    try:
        if 'admission_year' not in student:
            return student
            
        student = student.copy()
        admission_year = student.get('admission_year')
        course_id = student.get('course_id')
        
        # Query course to check if BSc (4 years) or other (3 years)
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM courses WHERE id = %s", (course_id,))
        course = cursor.fetchone()
        
        # Check for both "BSc" and "Bachelor of Science"
        is_bsc = course and ('BSc' in course.get('name', '') or 'Bachelor of Science' in course.get('name', ''))
        duration = 4 if is_bsc else 3
        end_year = admission_year + duration
        student['batch'] = f"{admission_year}-{end_year}"
        
        # Add current semester (auto-calculated based on admission year and course type)
        student['current_semester'] = calculate_current_semester(admission_year, is_bsc)
        
        return student
    except:
        return student
    finally:
        close_db(conn, cursor)


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
def prune_expired_tokens():
    # Remove expired session tokens from memory
    now = datetime.utcnow()
    expired_tokens = [
        token for token, session in ACTIVE_TOKENS.items()
        if session["expires_at"] <= now
    ]
    for token in expired_tokens:
        ACTIVE_TOKENS.pop(token, None)


def issue_token(user):
    # Generate and store new session token for user
    prune_expired_tokens()
    token = secrets.token_urlsafe(32)
    ACTIVE_TOKENS[token] = {
        "user_id": user.get("id"),
        "email": user["email"],
        "expires_at": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    }
    return token


def get_bearer_token():
    # Extract Bearer token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


def require_auth(view):
    # Decorator to require authentication for protected endpoints
    # Verifies token validity and extends session timeout
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        prune_expired_tokens()
        token = get_bearer_token()
        session = ACTIVE_TOKENS.get(token)

        if not token or not session:
            return json_error("Authentication required.", 401)

        # Extend session timeout on each request
        session["expires_at"] = datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)
        g.auth_token = token
        g.user_id = session.get("user_id")
        g.user_email = session["email"]
        return view(*args, **kwargs)

    return wrapped_view


def parse_json_body(expected_type=dict):
    # Parse and validate JSON request body
    data = request.get_json(silent=True)
    if not isinstance(data, expected_type):
        return None
    return data


def calculate_batch(admission_year, course_id, course_duration_map=None):
    # Calculate batch (e.g., 2023-2027 for BSc, 2023-2026 for other courses)
    # BSc is 4 years, others are 3 years
    # course_duration_map is used for testing, otherwise queries DB
    if course_duration_map is None:
        course_duration_map = {}
    
    # Check if this is a BSc course (4 years duration)
    is_bsc = False
    
    if course_id in course_duration_map:
        duration = course_duration_map[course_id]
    else:
        # Query database to check course name
        conn = cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name FROM courses WHERE id = %s", (course_id,))
            course = cursor.fetchone()
            if course and ('BSc' in course.get('name', '') or 'Bachelor of Science' in course.get('name', '')):
                is_bsc = True
        except:
            pass
        finally:
            close_db(conn, cursor)
    
    duration = 4 if is_bsc else 3
    end_year = admission_year + duration
    return f"{admission_year}-{end_year}"


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

    if not all([name, roll, course_id, semester, email, phone]):
        return None, "All student fields (name, roll, course, semester, email, phone) are required."

    if not is_valid_email(email):
        return None, "Please enter a valid student email address."

    # Validate phone number format (10-15 digits allowed, with optional country code)
    if not re.match(r"^[\d\s+\-()]{10,15}$", phone):
        return None, "Please enter a valid phone number (10-15 digits)."

    try:
        course_id = int(course_id)
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
    # Actual validation happens in endpoint when checking against course_semesters table
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
        try:
            student_id = int(raw_student_id)
        except (TypeError, ValueError):
            return None, f"Attendance item {index} has an invalid student ID."

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

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return json_error("An account with this email already exists.", 409)

        # Hash password and insert user
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed_password),
        )
        conn.commit()
        return jsonify({"message": "Registration successful. Please sign in."}), 201
    except mysql.connector.Error:
        return json_error("Unable to register right now. Please try again later.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


@app.route("/login", methods=["POST"])
def login():
    # User login - authenticate and issue session token - POST /login
    data = parse_json_body(dict)
    if data is None:
        return json_error("A valid JSON body is required.")

    email, password, error_message = validate_login_payload(data)
    if error_message:
        return json_error(error_message)

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        # Fetch user by email
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return json_error("Invalid email or password.", 401)

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
            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s",
                (upgraded_password, email),
            )
            conn.commit()

        # Issue new session token
        token = issue_token(user)
        return jsonify({
            "message": "Login successful.",
            "token": token,
            "email": email,
        })
    except mysql.connector.Error:
        return json_error("Unable to log in right now. Please try again later.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


@app.route("/logout", methods=["POST"])
@require_auth
def logout():
    # User logout - invalidate session token - POST /logout
    # Remove token from active sessions
    ACTIVE_TOKENS.pop(g.auth_token, None)
    return jsonify({"message": "Logged out successfully."})


@app.route("/me", methods=["GET"])
@require_auth
def me():
    # Current user info - retrieve authenticated user details - GET /me
    return jsonify({"email": g.user_email})


def get_course_end_date(admission_year, course_duration):
    """Calculate course end date (July of final year)
    
    Academic Calendar:
    - Batch starts: August (mid-year)
    - Batch ends: July (mid-year)
    - 2 semesters per year = 1 academic year
    
    Course end = admission_year + duration, July 31st
    
    Example:
    - Admitted Aug 2023, 4-year BSc: 2023 + 4 = ends July 2027
    - Admitted Aug 2023, 3-year other: 2023 + 3 = ends July 2026
    """
    end_year = admission_year + course_duration
    return date(end_year, 7, 31)


def has_course_ended(admission_year, course_duration):
    """Check if a student's course has ended based on today's date"""
    end_date = get_course_end_date(admission_year, course_duration)
    today = date.today()
    return today > end_date


@app.route("/students", methods=["GET"])
@require_auth
def get_students():
    # Get all students - retrieve complete student roster - GET /students
    # Optional query parameter: admission_year (to filter by batch)
    admission_year = request.args.get("admission_year", type=int)
    
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        if admission_year:
            # Fetch students with their courses for the specified batch (admission year)
            # Returns ALL students from that admission year regardless of course status
            cursor.execute("""
                SELECT s.*, c.name as course_name
                FROM students s
                JOIN courses c ON s.course_id = c.id
                WHERE s.admission_year = %s
                ORDER BY s.name ASC, s.roll ASC
            """, (admission_year,))
        else:
            # Retrieve all students, sorted by name then by roll number
            cursor.execute("""
                SELECT s.*, c.name as course_name
                FROM students s
                JOIN courses c ON s.course_id = c.id
                ORDER BY s.name ASC, s.roll ASC
            """)
        
        rows = cursor.fetchall()
        data = []
        
        for row in rows:
            student_dict = serialize_row(row)
            
            # Add batch info and calculate course status
            student_dict = add_batch_to_student(student_dict)
            
            # Add course duration and active status for attendance purposes
            course_name = row.get('course_name', '')
            is_bsc = 'BSc' in course_name or 'Bachelor of Science' in course_name
            duration = 4 if is_bsc else 3
            
            # Calculate course end date and check if still active
            course_end_date = get_course_end_date(admission_year, duration)
            course_is_active = not has_course_ended(admission_year, duration)
            
            student_dict['course_end_date'] = course_end_date.isoformat()
            student_dict['course_active'] = course_is_active
            student_dict['course_duration'] = duration
            
            data.append(student_dict)
        
        return jsonify(data)
    except mysql.connector.Error:
        return json_error("Unable to load students right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


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

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verify course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (student["course_id"],))
        if not cursor.fetchone():
            return json_error("Selected course does not exist.", 404)
        
        # Verify semester exists for this course
        cursor.execute(
            "SELECT id FROM course_semesters WHERE course_id = %s AND semester = %s",
            (student["course_id"], student["semester"]),
        )
        if not cursor.fetchone():
            return json_error("Selected semester is not available for this course.", 404)
        
        # Verify all papers exist for this course/semester
        if student["papers"]:
            placeholders = ", ".join(["%s"] * len(student["papers"]))
            cursor.execute(
                f"SELECT id FROM papers WHERE course_id = %s AND semester = %s AND id IN ({placeholders})",
                (student["course_id"], student["semester"], *student["papers"]),
            )
            valid_papers = {row["id"] for row in cursor.fetchall()}
            if len(valid_papers) != len(student["papers"]):
                return json_error("One or more selected papers do not exist for this course/semester.", 404)
        
        cursor.execute(
            "SELECT id FROM students WHERE roll = %s OR email = %s",
            (student["roll"], student["email"]),
        )
        if cursor.fetchone():
            return json_error("Roll number or email already exists.", 409)

        try:
            # Try to insert with admission_year column
            cursor.execute(
                "INSERT INTO students (name, roll, course_id, semester, admission_year, papers, email, phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    student["name"],
                    student["roll"],
                    student["course_id"],
                    student["semester"],
                    student["admission_year"],
                    json.dumps(student["papers"]),
                    student["email"],
                    student["phone"],
                ),
            )
        except mysql.connector.Error as e:
            # If admission_year column doesn't exist, insert without it (backward compatibility)
            if "Unknown column" in str(e):
                cursor.execute(
                    "INSERT INTO students (name, roll, course_id, semester, papers, email, phone) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        student["name"],
                        student["roll"],
                        student["course_id"],
                        student["semester"],
                        json.dumps(student["papers"]),
                        student["email"],
                        student["phone"],
                    ),
                )
            else:
                raise
        
        conn.commit()

        student_id = cursor.lastrowid
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        created_student = add_batch_to_student(serialize_row(cursor.fetchone()))
        return jsonify({
            "message": "Student added successfully.",
            "student": created_student,
        }), 201
    except mysql.connector.Error:
        return json_error("Unable to add the student right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


@app.route("/students/<int:student_id>", methods=["PUT"])
@require_auth
def update_student(student_id):
    # Update student - modify existing student record - PUT /students/{student_id}
    data = parse_json_body(dict)
    if data is None:
        return json_error("A valid JSON body is required.")

    student, error_message = validate_student_payload(data)
    if error_message:
        return json_error(error_message)

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        # Check if student exists
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        if not cursor.fetchone():
            return json_error("Student not found.", 404)

        # Verify course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (student["course_id"],))
        if not cursor.fetchone():
            return json_error("Selected course does not exist.", 404)
        
        # Verify semester exists for this course
        cursor.execute(
            "SELECT id FROM course_semesters WHERE course_id = %s AND semester = %s",
            (student["course_id"], student["semester"]),
        )
        if not cursor.fetchone():
            return json_error("Selected semester is not available for this course.", 404)
        
        # Verify all papers exist for this course/semester
        if student["papers"]:
            placeholders = ", ".join(["%s"] * len(student["papers"]))
            cursor.execute(
                f"SELECT id FROM papers WHERE course_id = %s AND semester = %s AND id IN ({placeholders})",
                (student["course_id"], student["semester"], *student["papers"]),
            )
            valid_papers = {row["id"] for row in cursor.fetchall()}
            if len(valid_papers) != len(student["papers"]):
                return json_error("One or more selected papers do not exist for this course/semester.", 404)

        # Ensure new roll/email don't conflict with other students
        cursor.execute(
            "SELECT id FROM students WHERE (roll = %s OR email = %s) AND id <> %s",
            (student["roll"], student["email"], student_id),
        )
        if cursor.fetchone():
            return json_error("Roll number or email already belongs to another student.", 409)

        try:
            # Update student record with new values
            cursor.execute(
                "UPDATE students SET name = %s, roll = %s, course_id = %s, semester = %s, admission_year = %s, papers = %s, email = %s, phone = %s WHERE id = %s",
                (
                    student["name"],
                    student["roll"],
                    student["course_id"],
                    student["semester"],
                    student["admission_year"],
                    json.dumps(student["papers"]),
                    student["email"],
                    student["phone"],
                    student_id,
                ),
            )
        except mysql.connector.Error as e:
            # If admission_year column doesn't exist, update without it (backward compatibility)
            if "Unknown column" in str(e):
                cursor.execute(
                    "UPDATE students SET name = %s, roll = %s, course_id = %s, semester = %s, papers = %s, email = %s, phone = %s WHERE id = %s",
                    (
                        student["name"],
                        student["roll"],
                        student["course_id"],
                        student["semester"],
                        json.dumps(student["papers"]),
                        student["email"],
                        student["phone"],
                        student_id,
                    ),
                )
            else:
                raise
        
        conn.commit()

        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        updated_student = add_batch_to_student(serialize_row(cursor.fetchone()))
        return jsonify({
            "message": "Student updated successfully.",
            "student": updated_student,
        })
    except mysql.connector.Error:
        return json_error("Unable to update the student right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


@app.route("/students/<int:student_id>", methods=["DELETE"])
@require_auth
def delete_student(student_id):
    # Delete student - remove student record and related attendance - DELETE /students/{student_id}
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        # Verify student exists before attempting deletion
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        if not cursor.fetchone():
            return json_error("Student not found.", 404)

        # Delete all attendance records for this student (cascade delete)
        cursor.execute("DELETE FROM attendance WHERE student_id = %s", (student_id,))
        # Delete the student record itself
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()
        return jsonify({"message": "Student deleted successfully."})
    except mysql.connector.Error:
        return json_error("Unable to delete the student right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


# ========== COURSES ENDPOINTS ==========
@app.route("/courses", methods=["GET"])
@require_auth
def get_courses():
    # Get all available courses - GET /courses
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, code FROM courses ORDER BY name ASC")
        data = [serialize_row(row) for row in cursor.fetchall()]
        return jsonify(data)
    except mysql.connector.Error:
        return json_error("Unable to load courses right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


# ========== COURSE SEMESTERS ENDPOINTS ==========
@app.route("/courses/<int:course_id>/semesters", methods=["GET"])
@require_auth
def get_semesters(course_id):
    # Get semesters for a specific course - GET /courses/{course_id}/semesters
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verify course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (course_id,))
        if not cursor.fetchone():
            return json_error("Course not found.", 404)
        
        cursor.execute(
            "SELECT semester FROM course_semesters WHERE course_id = %s ORDER BY semester ASC",
            (course_id,),
        )
        data = [row["semester"] for row in cursor.fetchall()]
        return jsonify(data)
    except mysql.connector.Error:
        return json_error("Unable to load semesters right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


# ========== PAPERS ENDPOINTS ==========
@app.route("/courses/<int:course_id>/semesters/<int:semester>/papers", methods=["GET"])
@require_auth
def get_papers(course_id, semester):
    # Get papers for a specific course and semester - GET /courses/{course_id}/semesters/{semester}/papers
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verify course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (course_id,))
        if not cursor.fetchone():
            return json_error("Course not found.", 404)
        
        # Verify semester exists for this course
        cursor.execute(
            "SELECT id FROM course_semesters WHERE course_id = %s AND semester = %s",
            (course_id, semester),
        )
        if not cursor.fetchone():
            return json_error("Semester not found for this course.", 404)
        
        cursor.execute(
            "SELECT id, name, code FROM papers WHERE course_id = %s AND semester = %s ORDER BY name ASC",
            (course_id, semester),
        )
        data = [serialize_row(row) for row in cursor.fetchall()]
        return jsonify(data)
    except mysql.connector.Error:
        return json_error("Unable to load papers right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


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
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get all unique admission years that have students
        cursor.execute("""
            SELECT DISTINCT admission_year
            FROM students
            ORDER BY admission_year DESC
        """)
        records = cursor.fetchall()
        
        batches = []
        seen = set()
        
        for record in records:
            admission_year = record['admission_year']
            
            # Calculate batch using 4-year duration (BSc standard)
            end_year = admission_year + 4
            batch_key = (admission_year, end_year)
            
            # Avoid duplicates
            if batch_key not in seen:
                seen.add(batch_key)
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
    finally:
        close_db(conn, cursor)


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

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Extract and validate all student IDs
        student_ids = sorted({record["student_id"] for record in normalized_records})
        placeholders = ", ".join(["%s"] * len(student_ids))
        cursor.execute(
            f"SELECT id FROM students WHERE id IN ({placeholders})",
            tuple(student_ids),
        )
        valid_student_ids = {row["id"] for row in cursor.fetchall()}

        # Check for any invalid student IDs
        missing_student_ids = sorted(set(student_ids) - valid_student_ids)
        if missing_student_ids:
            return json_error(
                f"Unknown student IDs: {', '.join(str(student_id) for student_id in missing_student_ids)}.",
                404,
            )

        # Process each attendance record: create if new, update if exists
        created_count = 0
        updated_count = 0

        for record in normalized_records:
            # Check if attendance record already exists for this student/date/subject
            cursor.execute(
                "SELECT id FROM attendance WHERE student_id = %s AND date = %s AND subject = %s",
                (record["student_id"], record["date"], record["subject"]),
            )
            existing = cursor.fetchone()

            if existing:
                # Record exists - update the status
                cursor.execute(
                    "UPDATE attendance SET status = %s WHERE id = %s",
                    (record["status"], existing["id"]),
                )
                updated_count += 1
            else:
                # Record doesn't exist - create new entry
                cursor.execute(
                    "INSERT INTO attendance (student_id, date, subject, status) VALUES (%s, %s, %s, %s)",
                    (
                        record["student_id"],
                        record["date"],
                        record["subject"],
                        record["status"],
                    ),
                )
                created_count += 1

        conn.commit()
        return jsonify({
            "message": "Attendance saved successfully.",
            "created": created_count,
            "updated": updated_count,
        })
    except mysql.connector.Error:
        return json_error("Unable to save attendance right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


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
    
    Fetches attendance records with optional filtering by date range and subject.
    Deduplicates records by unique (student_id, date, subject) key to handle
    any database inconsistencies. Sorts results by date, subject, and student_id
    in reverse chronological order (newest first).
    """
    start_date = normalize_text(request.args.get("start_date"))
    end_date = normalize_text(request.args.get("end_date"))
    subject_filter = normalize_text(request.args.get("subject"))

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        # Fetch all attendance records from database
        cursor.execute("SELECT * FROM attendance")
        raw_rows = cursor.fetchall()

        # Sort by ID to ensure consistent ordering
        raw_rows.sort(key=lambda row: row.get("id") or 0)
        
        # Deduplicate records by (student_id, date, subject) key
        # Keeps the last (highest ID) record for each combination
        deduplicated_records = {}
        for row in raw_rows:
            serialized = serialize_row(row)
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
                record.get("student_id", 0),
            ),
            reverse=True,
        )
        return jsonify(records)
    except mysql.connector.Error:
        return json_error("Unable to load attendance records right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


# ========== STATIC FILE SERVING ==========
@app.route('/')
def index():
    """
    Serve index.html - entry point for web application
    GET /
    Returns: HTML index page which handles client-side routing
    
    This serves the main entry point of the application. The index.html file
    contains client-side JavaScript that determines whether to show the login
    page or dashboard based on the user's authentication status.
    """
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """
    Serve static files and HTML pages - generic file serving endpoint
    GET /<path:path>
    Returns: Requested file if it exists, 404 Not Found otherwise
    
    Handles serving all static assets (CSS, JS, HTML pages) from the current
    directory. First attempts to serve the exact path, then tries adding .html
    extension (e.g., /dashboard serves dashboard.html if dashboard doesn't exist).
    This enables clean URLs without file extensions.
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
