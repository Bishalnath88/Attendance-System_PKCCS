from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
import os
import re
import secrets

from flask import Flask, g, jsonify, request
from flask_cors import CORS
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash


def load_env_file():
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


load_env_file()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "12"))
ACTIVE_TOKENS = {}
PASSWORD_COLUMN_MIN_LENGTH = 255
SCHEMA_BOOTSTRAPPED = False


def get_db_config():
    return {
        "host": os.environ.get("ATTENDANCE_DB_HOST", "localhost"),
        "user": os.environ.get("ATTENDANCE_DB_USER", "root"),
        "password": os.environ.get("ATTENDANCE_DB_PASSWORD", "bishal&8822"),
        "database": os.environ.get("ATTENDANCE_DB_NAME", "attendance_system"),
        "port": int(os.environ.get("ATTENDANCE_DB_PORT", "3306")),
    }


def ensure_database_schema():
    global SCHEMA_BOOTSTRAPPED

    if SCHEMA_BOOTSTRAPPED:
        return

    conn = cursor = None
    try:
        conn = mysql.connector.connect(**get_db_config())
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            SCHEMA_BOOTSTRAPPED = True
            return

        cursor.execute("SHOW COLUMNS FROM users LIKE 'password'")
        column = cursor.fetchone()
        if not column:
            SCHEMA_BOOTSTRAPPED = True
            return

        column_type = str(column.get("Type", "")).lower()
        match = re.search(r"varchar\((\d+)\)", column_type)

        if match and int(match.group(1)) < PASSWORD_COLUMN_MIN_LENGTH:
            cursor.execute(
                f"ALTER TABLE users MODIFY COLUMN password VARCHAR({PASSWORD_COLUMN_MIN_LENGTH})"
            )
            conn.commit()

        SCHEMA_BOOTSTRAPPED = True
    except mysql.connector.Error:
        # Let the main request surface any connection or query errors normally.
        pass
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def get_db():
    ensure_database_schema()
    return mysql.connector.connect(**get_db_config())


def close_db(conn=None, cursor=None, rollback=False):
    if cursor is not None:
        cursor.close()

    if conn is not None:
        if rollback:
            conn.rollback()
        conn.close()


def json_error(message, status_code=400):
    return jsonify({"message": message}), status_code


def serialize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def serialize_row(row):
    return {key: serialize_value(value) for key, value in row.items()}


def normalize_email(raw_email):
    return str(raw_email or "").strip().lower()


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email))


def normalize_text(value):
    return str(value or "").strip()


def is_hashed_password(password):
    return str(password).startswith(("pbkdf2:", "scrypt:", "argon2:"))


def prune_expired_tokens():
    now = datetime.utcnow()
    expired_tokens = [
        token for token, session in ACTIVE_TOKENS.items()
        if session["expires_at"] <= now
    ]
    for token in expired_tokens:
        ACTIVE_TOKENS.pop(token, None)


def issue_token(user):
    prune_expired_tokens()
    token = secrets.token_urlsafe(32)
    ACTIVE_TOKENS[token] = {
        "user_id": user.get("id"),
        "email": user["email"],
        "expires_at": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    }
    return token


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


def require_auth(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        prune_expired_tokens()
        token = get_bearer_token()
        session = ACTIVE_TOKENS.get(token)

        if not token or not session:
            return json_error("Authentication required.", 401)

        session["expires_at"] = datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)
        g.auth_token = token
        g.user_id = session.get("user_id")
        g.user_email = session["email"]
        return view(*args, **kwargs)

    return wrapped_view


def parse_json_body(expected_type=dict):
    data = request.get_json(silent=True)
    if not isinstance(data, expected_type):
        return None
    return data


def validate_login_payload(data):
    email = normalize_email(data.get("email"))
    password = normalize_text(data.get("password"))

    if not email or not password:
        return None, None, "Email and password are required."

    if not is_valid_email(email):
        return None, None, "Please enter a valid email address."

    return email, password, None


def validate_student_payload(data):
    name = normalize_text(data.get("name"))
    roll = normalize_text(data.get("roll"))
    student_class = normalize_text(data.get("class"))
    email = normalize_email(data.get("email"))

    if not all([name, roll, student_class, email]):
        return None, "All student fields are required."

    if not is_valid_email(email):
        return None, "Please enter a valid student email address."

    return {
        "name": name,
        "roll": roll,
        "class": student_class,
        "email": email,
    }, None


def parse_attendance_date(raw_date):
    try:
        return datetime.strptime(str(raw_date), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def validate_attendance_records(records):
    if not records:
        return None, "Attendance payload is empty."

    normalized_records = []
    allowed_statuses = {"present", "absent", "late"}

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            return None, f"Attendance item {index} is invalid."

        raw_student_id = record.get("student_id", record.get("studentId"))
        try:
            student_id = int(raw_student_id)
        except (TypeError, ValueError):
            return None, f"Attendance item {index} has an invalid student ID."

        attendance_date = parse_attendance_date(record.get("date"))
        if attendance_date is None:
            return None, f"Attendance item {index} must use YYYY-MM-DD date format."

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


@app.route("/register", methods=["POST"])
def register():
    data = parse_json_body(dict)
    if data is None:
        return json_error("A valid JSON body is required.")

    email, password, error_message = validate_login_payload(data)
    if error_message:
        return json_error(error_message)

    if len(password) < 6:
        return json_error("Password must be at least 6 characters long.")

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return json_error("An account with this email already exists.", 409)

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
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return json_error("Invalid email or password.", 401)

        stored_password = user.get("password", "")
        password_is_valid = (
            check_password_hash(stored_password, password)
            if is_hashed_password(stored_password)
            else stored_password == password
        )

        if not password_is_valid:
            return json_error("Invalid email or password.", 401)

        if stored_password and not is_hashed_password(stored_password):
            upgraded_password = generate_password_hash(password)
            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s",
                (upgraded_password, email),
            )
            conn.commit()

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
    ACTIVE_TOKENS.pop(g.auth_token, None)
    return jsonify({"message": "Logged out successfully."})


@app.route("/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"email": g.user_email})


@app.route("/students", methods=["GET"])
@require_auth
def get_students():
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students ORDER BY name ASC, roll ASC")
        data = [serialize_row(row) for row in cursor.fetchall()]
        return jsonify(data)
    except mysql.connector.Error:
        return json_error("Unable to load students right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


@app.route("/students", methods=["POST"])
@require_auth
def add_student():
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
        cursor.execute(
            "SELECT id FROM students WHERE roll = %s OR email = %s",
            (student["roll"], student["email"]),
        )
        if cursor.fetchone():
            return json_error("Roll number or email already exists.", 409)

        cursor.execute(
            "INSERT INTO students (name, roll, `class`, email) VALUES (%s, %s, %s, %s)",
            (student["name"], student["roll"], student["class"], student["email"]),
        )
        conn.commit()

        student_id = cursor.lastrowid
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        created_student = serialize_row(cursor.fetchone())
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
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        if not cursor.fetchone():
            return json_error("Student not found.", 404)

        cursor.execute(
            "SELECT id FROM students WHERE (roll = %s OR email = %s) AND id <> %s",
            (student["roll"], student["email"], student_id),
        )
        if cursor.fetchone():
            return json_error("Roll number or email already belongs to another student.", 409)

        cursor.execute(
            "UPDATE students SET name = %s, roll = %s, `class` = %s, email = %s WHERE id = %s",
            (
                student["name"],
                student["roll"],
                student["class"],
                student["email"],
                student_id,
            ),
        )
        conn.commit()

        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        updated_student = serialize_row(cursor.fetchone())
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
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        if not cursor.fetchone():
            return json_error("Student not found.", 404)

        cursor.execute("DELETE FROM attendance WHERE student_id = %s", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()
        return jsonify({"message": "Student deleted successfully."})
    except mysql.connector.Error:
        return json_error("Unable to delete the student right now.", 500)
    finally:
        close_db(conn, cursor, rollback=False)


@app.route("/attendance", methods=["POST"])
@require_auth
def save_attendance():
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

        student_ids = sorted({record["student_id"] for record in normalized_records})
        placeholders = ", ".join(["%s"] * len(student_ids))
        cursor.execute(
            f"SELECT id FROM students WHERE id IN ({placeholders})",
            tuple(student_ids),
        )
        valid_student_ids = {row["id"] for row in cursor.fetchall()}

        missing_student_ids = sorted(set(student_ids) - valid_student_ids)
        if missing_student_ids:
            return json_error(
                f"Unknown student IDs: {', '.join(str(student_id) for student_id in missing_student_ids)}.",
                404,
            )

        created_count = 0
        updated_count = 0

        for record in normalized_records:
            cursor.execute(
                "SELECT id FROM attendance WHERE student_id = %s AND date = %s AND subject = %s",
                (record["student_id"], record["date"], record["subject"]),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    "UPDATE attendance SET status = %s WHERE id = %s",
                    (record["status"], existing["id"]),
                )
                updated_count += 1
            else:
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
    start_date = normalize_text(request.args.get("start_date"))
    end_date = normalize_text(request.args.get("end_date"))
    subject_filter = normalize_text(request.args.get("subject"))

    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM attendance")
        raw_rows = cursor.fetchall()

        raw_rows.sort(key=lambda row: row.get("id") or 0)
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

        if start_date:
            records = [record for record in records if record["date"] >= start_date]
        if end_date:
            records = [record for record in records if record["date"] <= end_date]
        if subject_filter:
            records = [record for record in records if record["subject"] == subject_filter]

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


# Serve static files and HTML pages
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path != "" and os.path.exists(os.path.join('.', path)):
        return app.send_static_file(path)
    return json_error("Not found", 404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("FLASK_PORT", "5000")))
    app.run(
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=port,
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
