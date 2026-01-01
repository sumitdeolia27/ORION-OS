# 🚀 START HERE - ORION OS NAVIGATOR

## Quick Start (3 Steps)

### 1️⃣ Start Backend Server

**Windows:**
```bash
scripts\start_backend.bat
```

**Or manually:**
```bash
python scripts/api_server.py
```

✅ **Keep this terminal open!** You should see:
```
 * Running on http://127.0.0.1:5000
```

---

### 2️⃣ Start Frontend (New Terminal)

```bash
pnpm dev
```

✅ You should see:
```
  Local:        http://localhost:3000
```

---

### 3️⃣ Open Browser

Go to: **http://localhost:3000**

---

## 🎯 How to Use All Features

### **Command Console** (Main Interface)

1. Click **"Command Console"** in the dashboard
2. Type any command, for example:
   - `system info` - Get system information
   - `processes` - List running processes
   - `volume 50` - Set volume to 50%
   - `take screenshot` - Capture screen
   - `search python tutorial` - Google search
   - `ask ai what is python` - AI chat

3. **Voice Commands:** Click the 🎤 microphone button and speak

---

### **All Available Commands**

#### System
```
screenshot              # Take screenshot
volume 50               # Set volume (0-100)
volume up/down          # Adjust volume
mute                    # Mute system
system info             # System information
```

#### Camera
```
camera                  # Take photo
camera preview          # Open camera window
```

#### Processes
```
processes               # List all processes
top processes cpu       # Top by CPU
kill chrome             # Kill process
run notepad             # Start program
```

#### Files
```
open C:\Users           # Open folder/file
list files C:\Users     # List files
create folder test      # Create folder
rename old.txt new.txt  # Rename
move file.txt C:\       # Move file
copy file.txt C:\       # Copy file
delete file.txt         # Delete
```

#### File Tools
```
info C:\Users           # File details
find *.txt              # Search files
zip folder.zip C:\      # Create zip
unzip file.zip C:\     # Extract zip
size of C:\Users        # Folder size
large files C:\ 100     # Find large files (>100MB)
duplicates C:\          # Find duplicates
```

#### Browser
```
open browser https://google.com
search python tutorial
youtube python tutorial
```

#### AI (Needs GEMINI_API_KEY)
```
ask ai [question]
analyze image [path]
describe image [path]
extract text [image]
compare images [img1] and [img2]
vision [image] [question]
generate image [description]
create logo [description]
```

#### Productivity
```
add task [description]
show tasks
remind me [text]
show reminders
calculate 25 * 4
time
date
```

---

## 🎤 Voice Commands

1. Click **🎤 microphone** in Command Console
2. Speak clearly: "Take screenshot", "Volume up", etc.
3. Wait for execution

---

## 🧪 Test Everything

Run automated tests:
```bash
python scripts/test_functionality.py
```

---

## ❌ Troubleshooting

### Backend Not Working?
- Make sure `python scripts/api_server.py` is running
- Check it shows: `Running on http://127.0.0.1:5000`

### Commands Not Working?
- Backend must be running
- Check browser console for errors
- Check backend terminal for errors

### AI Not Working?
- Add `GEMINI_API_KEY=your_key` to `.env.local`
- Restart Next.js server
- Get key from: https://makersuite.google.com/app/apikey

### Voice Not Working?
- Grant microphone permission in browser
- Check microphone is connected
- Need internet for Google Speech API

---

## 📚 More Info

- **Full Guide:** See `QUICK_START_GUIDE.md`
- **Functionality Check:** See `FUNCTIONALITY_CHECK.md`
- **All Commands:** Type `help` in Command Console

---

**Ready to go! 🚀**

