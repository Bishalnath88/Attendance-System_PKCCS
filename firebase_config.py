"""
Firebase Firestore Configuration
Initializes Firebase Admin SDK and provides database references
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from pathlib import Path

# Path to service account key
SERVICE_ACCOUNT_KEY_PATH = Path(__file__).resolve().parent / "serviceAccountKey.json"

def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Before using this, you must:
    1. Create a Firebase project at console.firebase.google.com
    2. Download the service account JSON key from Project Settings
    3. Place it in the project root as 'serviceAccountKey.json'
    
    Returns: Firestore database instance
    """
    
    # Check if credentials file exists
    if not SERVICE_ACCOUNT_KEY_PATH.exists():
        raise FileNotFoundError(
            f"Service account key not found at: {SERVICE_ACCOUNT_KEY_PATH}\n"
            "Please download it from Firebase Console > Project Settings > Service Accounts\n"
            "and place it in the project root as 'serviceAccountKey.json'"
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
