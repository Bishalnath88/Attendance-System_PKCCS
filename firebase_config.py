"""
Firebase Firestore Configuration
Initializes Firebase Admin SDK and provides database references
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from pathlib import Path
import json

# Path to service account key
SERVICE_ACCOUNT_KEY_PATH = Path(__file__).resolve().parent / "serviceAccountKey.json"

# Environment variable that may contain the raw JSON service account
# Use this in production to avoid committing the JSON file to the repo.
SERVICE_ACCOUNT_JSON_ENV = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Before using this, you must:
    1. Create a Firebase project at console.firebase.google.com
    2. Download the service account JSON key from Project Settings
    3. Place it in the project root as 'serviceAccountKey.json'
    
    Returns: Firestore database instance
    """
    
    # Prefer JSON provided via environment variable (for hosted deployments)
    if SERVICE_ACCOUNT_JSON_ENV:
        try:
            sa_dict = json.loads(SERVICE_ACCOUNT_JSON_ENV)
        except Exception as exc:
            raise ValueError("Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON environment variable") from exc

        if not firebase_admin._apps:
            cred = credentials.Certificate(sa_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()

    # Fallback to loading credentials file from disk for local development
    if not SERVICE_ACCOUNT_KEY_PATH.exists():
        raise FileNotFoundError(
            f"Service account key not found at: {SERVICE_ACCOUNT_KEY_PATH}\n"
            "For production deployments set the GOOGLE_SERVICE_ACCOUNT_JSON environment variable with the service account JSON.\n"
            "For local development you can place 'serviceAccountKey.json' in the project root."
        )

    # Initialize Firebase (only once)
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_KEY_PATH))
        firebase_admin.initialize_app(cred)
    
    # Get Firestore instance
    db = firestore.client()
    return db


def get_db():
    """Get Firestore database instance"""
    return initialize_firebase()


# Initialize collections references
def get_users_ref():
    return get_db().collection("users")

def get_courses_ref():
    return get_db().collection("courses")

def get_course_semesters_ref():
    return get_db().collection("course_semesters")

def get_papers_ref():
    return get_db().collection("papers")

def get_students_ref():
    return get_db().collection("students")

def get_attendance_ref():
    return get_db().collection("attendance")
