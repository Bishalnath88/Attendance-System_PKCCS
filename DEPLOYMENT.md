# 🚀 Railway.app Deployment Guide - Step by Step

## Complete Checklist for Deployment

### ✅ Pre-Deployment Setup (Local Machine)

1. **Test Database Connection**
   ```bash
   python init_db.py
   ```
   ✔️ Should show: `✅ Created 'users' table`

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test App Locally**
   ```bash
   python app.py
   ```
   - Open: http://localhost:5000
   - Should redirect to: http://localhost:5000/login.html
   - Check console for database connections

4. **Test Registration**
   - Go to login page
   - Register with email and password
   - Should work without errors

---

### 📱 Frontend Update for Production

Edit `auth.js` and update API_BASE_URL:

**Before (Development):**
```javascript
const API_BASE_URL = "http://127.0.0.1:5000";
```

**After (Production - replace with your Railway URL):**
```javascript
const API_BASE_URL = "https://your-app-name.up.railway.app";
```

Get your Railway app URL from Railway dashboard → Settings → Domains

---

### 🔧 Railway.app Deployment

#### Option 1: Deploy via Git (Recommended)

1. **Initialize Git Repository**
   ```bash
   cd d:\CODE PLAYGROUND\6th_Sem_Project\Main
   git init
   git add .
   git commit -m "Initial commit - Student Attendance System"
   ```

2. **Create GitHub Repository**
   - Go to github.com and create a new repo
   - Don't initialize with README
   - Copy the commands for "push an existing repository from the command line"

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/your-repo-name.git
   git branch -M main
   git push -u origin main
   ```

4. **Connect to Railway**
   - Go to railway.app → New Project
   - Select "Deploy from GitHub"
   - Select your repository
   - Railway auto-detects Python and creates deployment

#### Option 2: Deploy via Railway CLI

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Deploy**
   ```bash
   railway up
   ```

---

### 🗄️ Railway MySQL Setup

1. **Add MySQL Service to Railway Project**
   - New Service → MySQL
   - Generate database credentials

2. **Update .env with Railway MySQL Credentials**
   - Host, Port, Username, Password, Database
   - (Already done in this project)

3. **Initialize Database on Railway**
   ```bash
   # After deployment, run this once on Railway environment
   python init_db.py
   ```

OR use Railway Shell:
```bash
railway shell
python init_db.py
exit
```

---

### 🔑 Environment Variables in Railway

After creating MySQL service, Railway auto-detects and injects:
- `MYSQLHOST`
- `MYSQLPORT`
- `MYSQLUSER`
- `MYSQLDATABASE`
- `MYSQLPASSWORD`

But our app uses custom ones in `.env`. Make sure `.env` file is in root directory.

---

### 📊 Monitoring Deployment

1. **Check Build Logs**
   - Railway Dashboard → Deployments → View logs

2. **Check Runtime Logs**
   - Railway Dashboard → Logs

3. **Common Issues:**
   ```
   ERROR: ModuleNotFoundError: No module named 'flask'
   → dependencies not installed (check requirements.txt)
   
   ERROR: MySQL connection failed
   → database credentials wrong in .env
   
   PORT binding error
   → Procfile might be incorrect
   ```

---

### 🧪 Post-Deployment Testing

1. **Test Frontend**
   - Visit: `https://your-app.up.railway.app/login.html`
   - Should load login page

2. **Test Registration**
   - Register new account
   - Login should work
   - Dashboard should load

3. **Test API Endpoints**
   ```bash
   # Get students (requires token from login)
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://your-app.up.railway.app/students
   ```

---

### 📈 Optional: Custom Domain

In Railway Settings:
1. Go to Domains
2. Add custom domain: `yourdomain.com`
3. Update DNS records with Railway nameservers
4. Update `auth.js` API_BASE_URL with your domain

---

### 🔐 Production Checklist

- [ ] Database initialized with `init_db.py`
- [ ] `.env` file NOT committed to Git
- [ ] `auth.js` has correct API_BASE_URL
- [ ] FLASK_DEBUG = 0 in .env
- [ ] Requirements.txt has all dependencies
- [ ] Procfile configured correctly
- [ ] Runtime.txt specifies Python version
- [ ] Test registration works
- [ ] Test login works
- [ ] Test add/view students works

---

### 📞 Support & Troubleshooting

**Port Issues:**
- Railway assigns dynamic PORT
- Our app handles it: `PORT` env variable
- No manual port configuration needed

**Database Connectivity:**
- Railway provides secure tunnel
- Host: `interchange.proxy.rlwy.net`
- Must use correct port: 38999

**CORS Issues:**
- If frontend on different domain, CORS already enabled
- Check browser console for specific errors

---

### 🎉 Success Indicators

✅ App loads without errors
✅ Login page displays
✅ Can register new user
✅ Can login with credentials
✅ Dashboard loads with student list
✅ Can add/edit/delete students
✅ Can mark attendance

---

**Questions?** Check Railway.app documentation: https://docs.railway.app
