# 📚 ORION OS NAVIGATOR - Complete Commands Reference

## 🚀 How to Use Commands

### Method 1: Command Console (Recommended)
1. Open the **Command Console** panel in the dashboard
2. Type your command in the input field
3. Press `Enter` or click the send button
4. The command will execute and show results

### Method 2: Voice Commands
1. Click the **🎤 microphone button** in Command Console
2. Speak your command clearly
3. Wait for recognition (10 seconds timeout)
4. Command will execute automatically

### Method 3: Quick Actions
- Use the quick action buttons in the dashboard
- Click buttons for common tasks (Screenshot, Voice, etc.)

---

## 📋 ALL AVAILABLE COMMANDS

### 🔧 SYSTEM COMMANDS

#### Screenshots
```
screenshot
take screenshot
capture screen
```
**Example:** `take screenshot`

```
rename screenshot to [name]
rename last screenshot [name]
```
**Example:** `rename screenshot to my_screenshot`

```
move screenshot to [path]
move last screenshot to [path]
```
**Example:** `move screenshot to C:\Users\Desktop`

#### Volume Control
```
volume [0-100]          # Set volume to specific level
set volume [0-100]      # Same as above
volume up               # Increase by 10%
increase volume         # Same as above
turn up volume          # Same as above
louder                  # Same as above
volume down             # Decrease by 10%
decrease volume         # Same as above
turn down volume        # Same as above
quieter                 # Same as above
softer                  # Same as above
mute                    # Mute system
unmute                  # Unmute (sets to 50%)
```
**Examples:**
- `volume 75` - Set volume to 75%
- `volume up` - Increase volume
- `mute` - Mute system

#### System Information
```
system info
system status
specs
```
**Example:** `system info` - Shows CPU, RAM, storage, platform info

---

### 📷 CAMERA COMMANDS

```
camera
take photo
capture camera
take picture
webcam
```
**Example:** `take photo` - Takes a photo and saves it

```
camera preview
show camera
open camera
```
**Example:** `camera preview` - Opens camera preview window

---

### 🖥️ PROCESS MANAGEMENT

#### List Processes
```
processes
list processes
show processes
list processes [filter]    # Filter by name
```
**Examples:**
- `processes` - List all processes
- `list processes chrome` - List Chrome processes

#### Top Processes
```
top
top processes
top processes cpu          # Sort by CPU usage
top processes memory       # Sort by memory usage
```
**Example:** `top processes cpu` - Shows top 10 processes by CPU

#### Process Information
```
process info [pid or name]
```
**Example:** `process info chrome` - Shows Chrome process details

#### Kill Process
```
kill [pid or name]
kill process [pid or name]
end task [pid or name]
```
**Examples:**
- `kill chrome` - Kill Chrome process
- `kill 1234` - Kill process by PID
- `end task notepad` - End Notepad

#### Start Process
```
run [command]
start process [command]
```
**Examples:**
- `run notepad` - Open Notepad
- `run calc` - Open Calculator

---

### 📁 FILE OPERATIONS

#### Open Files/Folders
```
open [file/folder/app]
open file [path]
open folder [path]
```
**Examples:**
- `open C:\Users` - Open Users folder
- `open file.txt` - Open file
- `open notepad` - Open Notepad app

#### List Files
```
list files [path]
```
**Example:** `list files C:\Users` - List files in Users folder

#### Create Folder
```
create folder [path]
new folder [path]
```
**Example:** `create folder C:\MyFolder`

#### Rename File
```
rename [path] to [new name]
rename file [path] to [new name]
```
**Example:** `rename old.txt to new.txt`

#### Move File
```
move [source] to [destination]
move file [source] to [destination]
```
**Example:** `move file.txt to C:\Users\Desktop`

#### Copy File
```
copy [source] to [destination]
copy file [source] to [destination]
```
**Example:** `copy file.txt to C:\Backup`

#### Delete File
```
delete [path]
delete file [path]
```
**Example:** `delete old_file.txt`

---

### 🔍 FILE TOOLS (Advanced)

#### File Information
```
info [path]
file info [path]
```
**Example:** `info C:\Users` - Shows file/folder details

#### Search Files
```
find [pattern]
search files [pattern]
find files [pattern]
```
**Examples:**
- `find *.txt` - Find all .txt files
- `find files python` - Find files with "python" in name

#### Compress Files
```
zip [source] to [destination]
compress [source] to [destination]
```
**Example:** `zip C:\MyFolder to C:\MyFolder.zip`

#### Extract Files
```
unzip [archive] to [destination]
extract [archive] to [destination]
```
**Example:** `unzip archive.zip to C:\Extracted`

#### Folder Size
```
size of [folder]
folder size [folder]
```
**Example:** `size of C:\Users` - Shows folder size

#### Find Large Files
```
large files [path] [size MB]
find large [path] [size MB]
```
**Example:** `large files C:\Users 100` - Find files > 100MB

#### Find Duplicates
```
duplicates [path]
find duplicates [path]
```
**Example:** `duplicates C:\Users` - Find duplicate files

---

### 🌐 BROWSER COMMANDS

#### Open Browser
```
open browser [url]
browser [url]
open chrome
open firefox
```
**Examples:**
- `open browser https://google.com`
- `open browser google.com`
- `browser youtube.com`

#### Search Web
```
search [query]
google [query]
search for [query]
```
**Examples:**
- `search python tutorial`
- `google how to code`
- `search for machine learning`

#### YouTube
```
youtube [search]
open youtube
play youtube [search]
search youtube [search]
```
**Examples:**
- `youtube python tutorial`
- `play youtube music`
- `search youtube coding`

---

### 🤖 AI COMMANDS (Requires GEMINI_API_KEY)

#### AI Chat
```
ask ai [question]
ai [question]
chat [question]
```
**Examples:**
- `ask ai what is python`
- `ai explain machine learning`
- `chat how do I code in javascript`

#### Image Analysis
```
analyze image [path]
describe image [path]
```
**Example:** `analyze image C:\photo.jpg`

#### Extract Text from Image (OCR)
```
extract text [image path]
ocr [image path]
```
**Example:** `extract text C:\document.jpg`

#### Compare Images
```
compare images [path1] and [path2]
```
**Example:** `compare images photo1.jpg and photo2.jpg`

#### Vision (Image + Question)
```
vision [image path] [question]
```
**Example:** `vision photo.jpg what is in this image`

#### Generate Image
```
generate image [description]
create image [description]
make image [description]
draw [description]
```
**Examples:**
- `generate image a sunset over mountains`
- `draw a cat wearing sunglasses`
- `create image futuristic city`

#### Create Logo
```
create logo [description]
```
**Example:** `create logo tech company with blue and green`

---

### 📝 PRODUCTIVITY COMMANDS

#### Tasks
```
add task [description]
new task [description]
show tasks
list tasks
```
**Examples:**
- `add task finish project`
- `show tasks` - List all tasks

#### Reminders
```
remind me [text]
set reminder [text]
add reminder [text]
show reminders
```
**Examples:**
- `remind me call mom at 3pm`
- `show reminders` - List all reminders

#### Calculator
```
calculate [expression]
calc [expression]
how much is [expression]
```
**Examples:**
- `calculate 25 * 4 + 10`
- `calc 100 / 5`
- `how much is 50 + 30`

#### Time & Date
```
time
what time
date
what date
```
**Examples:**
- `time` - Shows current time
- `date` - Shows current date

---

### 🎯 APPLICATIONS

#### Open Applications
```
open [app name]
launch [app name]
open app [app name]
```
**Examples:**
- `open notepad`
- `open calculator`
- `open vscode`
- `open spotify`
- `open discord`

**Available apps:**
- `notepad`, `calculator`, `paint`, `terminal`
- `vscode`, `code` (Visual Studio Code)
- `spotify`, `discord`
- Any installed application name

---

### ❓ HELP & UTILITIES

#### Help
```
help
commands
```
**Example:** `help` - Shows all available commands

#### Exit
```
exit
quit
close
goodbye
```
**Example:** `exit` - Closes the application

---

## 💡 TIPS & BEST PRACTICES

### 1. Natural Language
Commands work with natural language - you don't need exact syntax:
- ✅ "Take a screenshot"
- ✅ "Show me running processes"
- ✅ "Increase the volume"
- ✅ "Open browser and search for Python"

### 2. Voice Commands
- Speak clearly and naturally
- Wait for the microphone to stop listening (10 seconds)
- Commands are processed automatically after recognition

### 3. File Paths
- Use full paths: `C:\Users\Desktop\file.txt`
- Or relative paths: `file.txt` (current directory)
- Quotes not needed for paths with spaces

### 4. Multiple Commands
- Commands execute one at a time
- Wait for one command to finish before sending another

### 5. Error Handling
- If a command fails, check the error message
- Some commands require admin rights (like `kill process`)
- File operations need valid paths

---

## 🚨 COMMON ISSUES

### Command Not Working?
1. **Check backend is running:** `python scripts/api_server.py`
2. **Check error message:** Read the response in Command Console
3. **Try different wording:** Use variations of the command
4. **Check permissions:** Some commands need admin rights

### AI Commands Not Working?
1. **Check API key:** Ensure `GEMINI_API_KEY` is in `.env.local`
2. **Restart server:** After adding API key, restart Next.js
3. **Rate limits:** Wait 5 seconds between AI requests
4. **Get API key:** https://makersuite.google.com/app/apikey

### Voice Not Working?
1. **Check microphone:** Ensure mic is connected and working
2. **Grant permissions:** Browser may ask for microphone access
3. **Speak clearly:** Wait for recognition (10 seconds timeout)
4. **Check backend:** Voice recognition needs backend running

---

## 📊 COMMAND CATEGORIES SUMMARY

| Category | Commands Count | Examples |
|----------|---------------|----------|
| System | 8 | screenshot, volume, system info |
| Camera | 2 | take photo, camera preview |
| Processes | 5 | processes, kill, top |
| Files | 7 | open, copy, delete, rename |
| File Tools | 7 | find, zip, size, duplicates |
| Browser | 3 | open browser, search, youtube |
| AI | 8 | ask ai, analyze image, generate |
| Productivity | 6 | tasks, reminders, calculate |
| Applications | 10+ | open notepad, calculator, etc. |
| **Total** | **50+** | All commands above |

---

## 🎯 QUICK REFERENCE CARD

```
SYSTEM:     screenshot, volume 50, system info, mute
CAMERA:     take photo, camera preview
PROCESSES:  processes, kill chrome, top processes cpu
FILES:      open C:\Users, copy file.txt, delete old.txt
SEARCH:     find *.txt, large files C:\ 100
BROWSER:    open browser google.com, search python
AI:         ask ai [question], analyze image photo.jpg
TASKS:      add task [text], show tasks
REMINDERS:  remind me [text], show reminders
CALC:       calculate 25 * 4
TIME:       time, date
HELP:       help, commands
```

---

## 📝 NOTES

- All commands are case-insensitive
- Commands support natural language variations
- Some commands require specific permissions
- AI commands need `GEMINI_API_KEY` configured
- Backend server must be running for all commands
- Voice commands have a 10-second timeout

---

**Last Updated:** December 2024  
**Version:** ORION OS NAVIGATOR v3.0

