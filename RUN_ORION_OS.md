# 🚀 How to Run ORION OS (Complete Guide)

## Quick Start - 2 Simple Steps

ORION OS requires **TWO servers** to run:
1. **Frontend** (Next.js) - The web interface
2. **Backend** (Python Flask) - System commands, voice, and features

---

## ✅ Step 1: Start the Frontend (Next.js)

Open your first terminal and run:

```bash
npm run dev
```

or if you're using pnpm:

```bash
pnpm dev
```

You should see:
```
  ▲ Next.js 16.0.7
  - Local:        http://localhost:3000
  - Ready in 2.3s
```

✅ **Frontend is running!** Keep this terminal open.

---

## ✅ Step 2: Start the Backend (Python)

### Option A: Using the Startup Script (EASIEST)

**On Windows:**
```bash
# Double-click or run:
start-backend.bat
```

**On Mac/Linux:**
```bash
# Make executable (first time only):
chmod +x start-backend.sh

# Then run:
./start-backend.sh
```

### Option B: Using npm/pnpm

Open a **SECOND terminal** and run:

```bash
npm run dev:backend
```

or:

```bash
pnpm dev:backend
```

### Option C: Direct Python Command

Open a **SECOND terminal** and run:

```bash
python scripts/api_server.py
```

You should see:
```
============================================================
ORION OS Navigator API Server
============================================================
Starting server on http://localhost:5000
Press Ctrl+C to stop
============================================================
 * Running on http://127.0.0.1:5000
```

✅ **Backend is running!** Keep this terminal open too.

---

## 🎉 You're Ready!

Now open your browser and go to:
**http://localhost:3000**

You should see ORION OS fully working with:
- ✅ System metrics (CPU, RAM, Storage) updating in real-time
- ✅ AI Chat working (Gemini API key already configured)
- ✅ Command execution
- ✅ Voice features (if microphone available)
- ✅ Tasks and reminders
- ✅ All features working!

---

## 🔧 Troubleshooting

### "Backend server is not running" error

- Make sure you completed **Step 2** above
- Check that the backend terminal shows "Running on http://localhost:5000"
- Visit http://localhost:5000/health to verify backend is working

### Backend won't start - "Flask not installed"

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Port 5000 already in use

Something else is using port 5000. Either:
1. Stop the other application
2. Or change the backend port (see BACKEND_FIX_GUIDE.md)

### Python not found

- Install Python 3.11+ from https://www.python.org/downloads/
- Make sure "Add Python to PATH" is checked during installation

---

## 📊 What You'll See

When both servers are running, you'll have:

### Frontend (http://localhost:3000)
- Modern futuristic UI
- Real-time system monitoring
- AI chat assistant
- Command center
- Voice controls
- Task management

### Backend (http://localhost:5000)
- REST API server
- System integration
- Voice recognition
- Command processing
- Data persistence

---

## 🛑 Stopping ORION OS

To stop the servers:

1. **Frontend Terminal:** Press `Ctrl+C`
2. **Backend Terminal:** Press `Ctrl+C`

Both servers will shut down gracefully.

---

## ⚙️ Configuration Status

✅ **AI Chat:** Configured and working (Gemini 2.5 Flash)
✅ **Backend:** Python Flask API Server ready
✅ **Frontend:** Next.js 16 with React 19
✅ **API Key:** Valid and tested
✅ **Rate Limits:** Disabled (no restrictions)

---

## 📝 Terminal Setup

**Recommended Setup:**

```
Terminal 1 (Frontend):          Terminal 2 (Backend):
┌─────────────────────┐        ┌─────────────────────┐
│                     │        │                     │
│ $ npm run dev       │        │ $ start-backend.bat │
│                     │        │     or              │
│ ▲ Next.js 16.0.7    │        │ $ npm run dev:backend│
│ - Local: :3000      │        │                     │
│                     │        │ Running on :5000    │
│ [Keep running]      │        │ [Keep running]      │
│                     │        │                     │
└─────────────────────┘        └─────────────────────┘
```

---

## 🎯 Quick Reference

| What | Command | Port |
|------|---------|------|
| Frontend | `npm run dev` | 3000 |
| Backend | `npm run dev:backend` | 5000 |
| Backend (Windows) | `start-backend.bat` | 5000 |
| Backend (Mac/Linux) | `./start-backend.sh` | 5000 |
| Health Check | Visit http://localhost:5000/health | 5000 |
| Main App | Visit http://localhost:3000 | 3000 |

---

## 💡 Pro Tips

1. **Use Split Terminal:** Most IDEs let you split the terminal so you can see both running at once
2. **Background Process:** On Mac/Linux, you can run backend with `./start-backend.sh &` to run in background
3. **Auto-start:** Create a script that starts both servers automatically
4. **Keep Logs:** The backend terminal shows all command processing logs

---

## ✅ Success Checklist

Before using ORION OS, verify:

- [ ] Frontend running on http://localhost:3000
- [ ] Backend running on http://localhost:5000
- [ ] http://localhost:5000/health returns `{"status": "ok"}`
- [ ] No "Backend server is not running" error on frontend
- [ ] System metrics showing live data
- [ ] AI chat responding to messages

**If all checked, you're good to go!** 🚀

---

## 📚 Additional Resources

- **Backend Setup:** See `BACKEND_FIX_GUIDE.md`
- **AI Chat Setup:** See `SUCCESS_SETUP_COMPLETE.md`
- **Commands Reference:** See `COMMANDS_REFERENCE.md`
- **Quick Start:** See `QUICK_START_GUIDE.md`
- **Functionality Check:** See `FUNCTIONALITY_CHECK.md`

---

**Enjoy ORION OS!** 🌟
