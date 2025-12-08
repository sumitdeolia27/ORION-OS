# 🚀 ORION OS NAVIGATOR - Quick Start Guide

## Step 1: Start the Backend Server

The backend server handles all system commands, voice recognition, and AI features.

### Option A: Using the Batch Script (Windows)
```bash
scripts\start_backend.bat
```

### Option B: Manual Start
```bash
python scripts/api_server.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

✅ **Keep this terminal open!** The backend must be running for commands to work.

---

## Step 2: Start the Frontend

Open a **new terminal window** and run:

```bash
pnpm dev
```

Or if you don't have pnpm:
```bash
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 16.0.7
  - Local:        http://localhost:3000
  - Ready in 2.3s
```

✅ Open **http://localhost:3000** in your browser.

---

## Step 3: Using All Functionality

### 🎯 Method 1: Command Console (Recommended)

1. **Open the Command Console:**
   - Click the "Command Console" panel in the dashboard
   - Or press `Ctrl+K` (if keyboard shortcut is enabled)

2. **Type commands naturally:**
   ```
   system info
   processes
   volume 75
   take screenshot
   ```

3. **Use Voice Commands:**
   - Click the microphone button in the command console
   - Speak your command clearly
   - Wait for recognition and execution

---

### 🎯 Method 2: AI Chat

1. **Open the AI Chat panel**
2. **Ask questions or give commands:**
   ```
   What's my system information?
   Take a screenshot
   List my running processes
   ```

---

## 📋 Complete Command Examples

### 🔧 SYSTEM COMMANDS

```bash
# Screenshots
screenshot
take screenshot
rename screenshot to my_screenshot
move screenshot to C:\Users\Desktop

# Volume Control
volume 50          # Set to 50%
volume up          # Increase by 10%
volume down        # Decrease by 10%
mute               # Mute system

# System Info
system info
specs
```

### 📷 CAMERA COMMANDS

```bash
camera             # Take a photo
take photo
camera preview     # Open camera preview window
open camera
```

### ⚙️ PROCESS MANAGEMENT

```bash
processes                    # List all processes
list processes chrome        # Filter by name
top processes cpu            # Top by CPU usage
top processes memory         # Top by memory
process info 1234           # Info about PID 1234
process info chrome          # Info about chrome process
kill chrome                  # Kill chrome process
kill 1234                    # Kill process by PID
end task chrome              # End task
run notepad                  # Start notepad
```

### 📁 FILE OPERATIONS

```bash
# Opening
open C:\Users                # Open folder
open file.txt                # Open file
open notepad                 # Open application

# File Management
list files C:\Users          # List files in directory
create folder test_folder    # Create new folder
rename old.txt new.txt      # Rename file
move file.txt C:\Desktop     # Move file
copy file.txt C:\Backup      # Copy file
delete file.txt              # Delete file
```

### 🛠️ FILE TOOLS

```bash
info C:\Users                # Get file/folder details
find *.txt                   # Search for .txt files
find python                  # Search for files containing "python"
zip folder.zip C:\MyFolder   # Create zip archive
unzip archive.zip C:\Extract # Extract zip
size of C:\Users             # Get folder size
large files C:\Users 100     # Find files larger than 100MB
duplicates C:\Users          # Find duplicate files
```

### 🌐 BROWSER COMMANDS

```bash
open browser https://google.com
search python tutorial
google how to code
youtube python tutorial
```

### 🤖 AI COMMANDS (Requires GEMINI_API_KEY)

```bash
ask ai what is python
analyze image screenshot.png
describe image photo.jpg
extract text image.png
compare images img1.jpg and img2.jpg
vision image.png what is in this image
generate image a sunset over mountains
create logo tech company logo
```

### 📝 PRODUCTIVITY

```bash
add task finish project
show tasks
remind me call mom at 3pm
show reminders
calculate 25 * 4 + 10
time                        # Get current time
date                        # Get current date
```

---

## 🎤 Voice Commands

1. **Click the microphone icon** in the Command Console
2. **Speak clearly:**
   - "Take screenshot"
   - "Volume up"
   - "Open browser"
   - "Search python tutorial"
   - "System info"

3. **Wait for recognition** - The system will:
   - Show what it heard
   - Execute the command
   - Display the result

---

## 🧪 Testing All Functionality

### Quick Test Script

Run the automated test script:

```bash
python scripts/test_functionality.py
```

This will test all major command categories automatically.

### Manual Testing

1. **Start both servers** (backend + frontend)
2. **Open Command Console** in browser
3. **Try each category:**
   - System: `system info`, `volume 50`
   - Processes: `processes`, `top processes cpu`
   - Files: `list files C:\Users`
   - Browser: `search test`
   - AI: `ask ai hello` (requires GEMINI_API_KEY)
   - Productivity: `calculate 10 + 5`

---

## 🔍 Troubleshooting

### Backend Not Responding

**Problem:** Commands return "Connection Error"

**Solution:**
1. Check if backend is running: `http://localhost:5000`
2. Restart backend: `python scripts/api_server.py`
3. Check firewall settings

### Voice Commands Not Working

**Problem:** Microphone not recognized

**Solution:**
1. Grant microphone permissions in browser
2. Check microphone is connected
3. Try speaking more clearly
4. Check internet connection (uses Google Speech API)

### AI Commands Not Working

**Problem:** "API key not configured" error

**Solution:**
1. Check `.env.local` has `GEMINI_API_KEY=your_key`
2. Restart Next.js dev server after adding key
3. Get API key from: https://makersuite.google.com/app/apikey

### Rate Limit Errors

**Problem:** "Rate limit exceeded" for AI commands

**Solution:**
1. Wait 60 seconds (cooldown period)
2. The system will show a countdown timer
3. Free tier limit: ~15 requests/minute
4. Wait at least 4 seconds between AI requests

---

## 📊 Dashboard Features

### Available Panels:

1. **Command Console** - Execute all commands
2. **AI Chat** - Chat with Gemini AI
3. **System Metrics** - CPU, RAM, Storage usage
4. **Tasks Panel** - Manage tasks
5. **Reminders Panel** - Set reminders
6. **File Explorer** - Browse files
7. **Notes Widget** - Take notes
8. **Status Bar** - Volume control, time, system status

### Quick Actions:

- **Screenshot** - Take screenshot
- **Voice Command** - Start voice recognition
- **Volume Slider** - Adjust system volume
- **System Info** - View system specs

---

## 🎯 Pro Tips

1. **Natural Language:** Commands work with natural language
   - ✅ "Take a screenshot"
   - ✅ "Increase volume"
   - ✅ "Show me running processes"

2. **Voice Commands:** Speak naturally
   - ✅ "Open browser and search for Python tutorial"
   - ✅ "Take a screenshot and save it as test"

3. **AI Integration:** Use AI for complex tasks
   - ✅ "What processes are using the most memory?"
   - ✅ "Analyze this screenshot and tell me what you see"

4. **Command History:** Previous commands are saved
   - Access through the Command Console
   - Can rerun previous commands

---

## 🚨 Important Notes

1. **Backend Must Run:** The Python backend server must be running for commands to work
2. **Admin Rights:** Some commands (like `kill process`) may require admin rights
3. **Platform Specific:** Some commands work differently on Windows/Mac/Linux
4. **API Keys:** AI features require GEMINI_API_KEY in `.env.local`
5. **Rate Limits:** Free tier Gemini API has ~15 requests/minute limit

---

## 📞 Need Help?

- Check `FUNCTIONALITY_CHECK.md` for detailed implementation status
- Run `python scripts/test_functionality.py` to test all features
- Check browser console for errors
- Check backend terminal for error messages

---

**Happy Commanding! 🚀**

