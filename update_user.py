"""
Update Firestore Users - Remove all and add specific user
"""

from firebase_config import get_db
from werkzeug.security import generate_password_hash
from datetime import datetime

def update_users():
    """Delete all users and add the specific user"""
    
    db = get_db()
    
    print("[*] Updating Users Collection...")
    print()
    
    # ============================================
    # 1. DELETE ALL EXISTING USERS
    # ============================================
    print("[*] Deleting existing users...")
    
    users_ref = db.collection("users")
    docs = users_ref.stream()
    
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
        print("    [DELETED] {}".format(doc.id))
    
    if count == 0:
        print("    [INFO] No existing users found")
    else:
        print("    [OK] {} user(s) deleted".format(count))
    
    print()
    
    # ============================================
    # 2. ADD NEW USER
    # ============================================
    print("[*] Adding new user...")
    
    email = "pkccsattendance88@gmail.com"
    password = "PKCCSSAMS@88"
    
    # Hash the password using werkzeug
    hashed_password = generate_password_hash(password)
    
    user_data = {
        "email": email,
        "password": hashed_password,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    doc_ref = db.collection("users").add(user_data)
    user_id = doc_ref[1].id
    
    print("    [OK] User added successfully!")
    print("    Email: {}".format(email))
    print("    User ID: {}".format(user_id))
    
    print()
    print("=" * 50)
    print("SUCCESS! USER UPDATE COMPLETE!")
    print("=" * 50)
    print()
    print("[*] Login with:")
    print("    Email: {}".format(email))
    print("    Password: {}".format(password))
    print()

if __name__ == "__main__":
    try:
        update_users()
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
