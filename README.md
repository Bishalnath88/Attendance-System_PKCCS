// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";// Change this after you get Railway URL
const API_BASE_URL = "https://your-railway-app.up.railway.app";# Student Attendance System - Deployment Guide

## 🚀 Railway Deployment Setup

This project is configured for deployment on **Railway.app** with a MySQL database.

### Prerequisites
- Railway.app account with MySQL database
- Python 3.11+
- Git

### 📋 Configuration

#### 1. Environment Variables (.env file)
Already configured with Railway credentials:
```
ATTENDANCE_DB_HOST=interchange.proxy.rlwy.net
ATTENDANCE_DB_PORT=38999
ATTENDANCE_DB_USER=root
ATTENDANCE_DB_NAME=railway
ATTENDANCE_DB_PASSWORD=your_password
```

#### 2. Database Initialization
Before first deployment, run:
```bash
python init_db.py
```

This creates all required tables:
- `users` - Admin/user accounts
- `students` - Student information
- `attendance` - Attendance records

### 📦 Files Included

| File | Purpose |
|------|---------|
| `app.py` | Flask backend with API endpoints |
| `Procfile` | Railway deployment configuration |
| `runtime.txt` | Python version specification |
| `requirements.txt` | Python dependencies |
| `init_db.py` | Database schema initialization |
| `schema.sql` | SQL schema for manual setup |
| `.env` | Environment variables |
| `.gitignore` | Git ignore rules |

### 🔧 Deployment Steps

#### Step 1: Initialize Database (Local)
```bash
python init_db.py
```

#### Step 2: Test Locally
```bash
pip install -r requirements.txt
python app.py
```
App runs on `http://localhost:5000`

#### Step 3: Push to Railway
```bash
git add .
git commit -m "Deploy to Railway"
git push railway main
```

Or connect your GitHub repo directly in Railway dashboard.

### 📱 Frontend Configuration

✅ Already updated! `auth.js` configured with:
```javascript
const API_BASE_URL = "https://attendance-systempkccs-production.up.railway.app";
```

### 🔐 Security Notes

- ✅ Passwords are hashed using Werkzeug
- ✅ Token-based authentication with HTTP Bearer
- ✅ CORS enabled for frontend requests
- ✅ Environment variables protect sensitive data
- ⚠️ Never commit `.env` to version control

### 🛠️ API Endpoints

**Authentication:**
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /logout` - User logout

**Students:**
- `GET /students` - List all students
- `POST /students` - Add new student
- `PUT /students/<id>` - Update student
- `DELETE /students/<id>` - Delete student

**Attendance:**
- `GET /attendance` - Get attendance records (with filters)
- `POST /attendance` - Save/update attendance records

**User:**
- `GET /me` - Get current user info

### 📦 Dependencies
- Flask 2.3.3
- flask-cors 4.0.0
- mysql-connector-python 8.0.33
- Werkzeug 2.3.7

### 🐛 Troubleshooting

**Database Connection Error:**
```
Check .env file credentials
Verify Railway MySQL service is running
Ensure IP whitelist includes Railway deployment
```

**Port Issues:**
```
Railway auto-assigns PORT env variable
App uses: PORT or FLASK_PORT (5000 default)
```

**CORS Errors:**
```
auth.js API_BASE_URL must match deployed app URL
Frontend and backend must be on same/allowed origins
```

### 📝 Notes

- Session tokens expire after `SESSION_TTL_HOURS` (default: 12)
- LocalStorage used for frontend session management
- All tokens stored in memory (deployed instance maintains same token)
- Database uses UTF8MB4 for international character support

---

**Deployment URL:** https://attendance-systempkccs-production.up.railway.app
**Database Host:** interchange.proxy.rlwy.net:38999
**Database Name:** railway
