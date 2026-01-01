# 🔧 ORION OS Backend Server - Quick Fix Guide

## Problem
You're seeing this error:
```
❌ Error: Backend server is not running. Please start it with: python scripts/api_server.py
```

This means the Python Flask backend server (which handles system commands, voice, tasks, etc.) is not running.

## ✅ Quick Solution - 3 Easy Ways to Start the Backend

### Method 1: Using the Startup Script (EASIEST - Recommended)

**On Windows:**
```bash
# Double-click this file or run in terminal:
start-backend.bat
```

**On Mac/Linux:**
```bash
# Make it executable first (one time only):
chmod +x start-backend.sh

# Then run:
./start-backend.sh
```

### Method 2: Using npm/pnpm (If you prefer)

Open a **SECOND terminal** (keep your Next.js dev server running in the first one):

```bash
npm run dev:backend
```

or if you're using pnpm:

```bash
pnpm dev:backend
```

### Method 3: Direct Python Command

Open a **SECOND terminal** and run:

```bash
python scripts/api_server.py
```

## 📋 Complete Setup (First Time)

If this is your first time running the backend, follow these steps:

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or if you're using Python 3 specifically:

```bash
python3 -m pip install -r requirements.txt
```

### Step 2: Start the Backend Server

Use any of the 3 methods above.

### Step 3: Verify It's Running

You should see:
```
============================================================
ORION OS Navigator API Server
============================================================
Starting server on http://localhost:5000
Press Ctrl+C to stop
============================================================
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://YOUR-IP:5000
```

### Step 4: Test the Backend

Open your browser and visit:
- Health Check: http://localhost:5000/health

You should see:
```json
{
  "status": "ok",
  "service": "ORION OS Navigator API",
  "version": "1.0.0"
}
```

## 🚀 Running Both Frontend and Backend Together

You need **TWO terminal windows** running simultaneously:

### Terminal 1: Frontend (Next.js)
```bash
npm run dev
# or
pnpm dev
```

### Terminal 2: Backend (Flask/Python)
```bash
npm run dev:backend
# or
pnpm dev:backend
# or
python scripts/api_server.py
```

**Pro Tip:** Use your IDE's split terminal feature or use two separate terminal windows.

## 🔍 Troubleshooting

### Error: "Flask not installed"

Install dependencies:
```bash
pip install -r requirements.txt
```

### Error: "Port 5000 already in use"

Something else is using port 5000. Options:
1. Kill the process using port 5000
2. Change the port in `scripts/api_server.py` (line 620):
   ```python
   app.run(host='0.0.0.0', port=5001, debug=True)  # Changed to 5001
   ```
   Then update `.env.local`:
   ```
   BACKEND_API_URL=http://localhost:5001
   ```

### Error: "Python not found"

Make sure Python 3.11+ is installed:
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### Backend starts but frontend still shows error

1. Make sure backend is running on port 5000
2. Check if there's a firewall blocking localhost connections
3. Verify `.env.local` has correct backend URL:
   ```
   BACKEND_API_URL=http://localhost:5000
   ```

## 📦 What the Backend Does

The Python backend provides:
- ✅ System commands (open apps, control volume, etc.)
- ✅ Voice recognition and text-to-speech
- ✅ System metrics (CPU, memory, storage)
- ✅ Task and reminder management
- ✅ Notes management
- ✅ Command history
- ✅ Integration with system APIs

## 🔧 Backend API Endpoints

Once running, these endpoints are available:

- `GET /health` - Health check
- `POST /api/command` - Process commands
- `GET /api/system/info` - System information
- `GET /api/system/metrics` - System metrics (CPU, RAM, etc.)
- `GET /api/tasks` - Get tasks
- `POST /api/tasks` - Add task
- `GET /api/reminders` - Get reminders
- `POST /api/reminders` - Add reminder
- `GET /api/notes` - Get notes
- `POST /api/notes` - Add note
- `POST /api/voice/speak` - Text-to-speech
- `POST /api/voice/listen` - Voice recognition
- `GET /api/voice/status` - Voice engine status
- `GET /api/volume` - Get volume
- `POST /api/volume` - Set volume

## ⚙️ Configuration

The backend can be configured via environment variables in `.env.local`:

```bash
BACKEND_API_URL=http://localhost:5000  # Backend server URL
GEMINI_API_KEY=your_key_here           # For AI features (already configured)
```

## 🎯 Quick Reference Card

| Action | Command |
|--------|---------|
| Start Backend (Windows) | `start-backend.bat` |
| Start Backend (Mac/Linux) | `./start-backend.sh` |
| Start Backend (npm) | `npm run dev:backend` |
| Check Backend Health | Visit http://localhost:5000/health |
| Stop Backend | Press `Ctrl+C` in backend terminal |
| View Backend Logs | Check the terminal where backend is running |

## ✅ Success Checklist

After starting the backend, verify these:

- [ ] Terminal shows "Running on http://localhost:5000"
- [ ] http://localhost:5000/health returns {"status": "ok"}
- [ ] Frontend no longer shows "Backend server is not running" error
- [ ] System metrics dashboard shows live data
- [ ] Commands work (try: "show system info")
- [ ] Voice features work (if microphone is available)

## 🚨 Important Notes

1. **Keep it Running:** The backend server must stay running while using ORION OS
2. **Two Terminals:** You need both frontend (Next.js) AND backend (Python) running
3. **Port 5000:** Make sure nothing else is using this port
4. **Dependencies:** Run `pip install -r requirements.txt` if you haven't already

---

## 🎉 You're All Set!

Once you see both servers running:
- Frontend: http://localhost:3000 ✅
- Backend: http://localhost:5000 ✅

Your ORION OS is fully operational! 🚀
