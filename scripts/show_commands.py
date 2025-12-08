#!/usr/bin/env python3
"""
ORION OS NAVIGATOR - Commands Display Script
Shows all available commands in the Command Console
"""

def print_commands():
    """Display all available commands organized by category"""
    
    print("=" * 70)
    print("ORION OS NAVIGATOR v3.0 - ALL AVAILABLE COMMANDS")
    print("=" * 70)
    print()
    
    # SYSTEM COMMANDS
    print("🔧 SYSTEM COMMANDS")
    print("-" * 70)
    print("  Screenshots:")
    print("    • screenshot, take screenshot, capture screen")
    print("    • rename screenshot to [name]")
    print("    • move screenshot to [path]")
    print()
    print("  Volume Control:")
    print("    • volume [0-100]          # Set volume (e.g., volume 75)")
    print("    • volume up/down          # Adjust volume")
    print("    • mute, unmute            # Mute/unmute system")
    print()
    print("  System Info:")
    print("    • system info, specs      # Show system information")
    print()
    
    # CAMERA
    print("📷 CAMERA COMMANDS")
    print("-" * 70)
    print("    • camera, take photo, take picture")
    print("    • camera preview, open camera")
    print()
    
    # PROCESS MANAGEMENT
    print("🖥️  PROCESS MANAGEMENT")
    print("-" * 70)
    print("    • processes, list processes [filter]")
    print("    • top, top processes [cpu/memory]")
    print("    • process info [pid or name]")
    print("    • kill [pid or name], end task")
    print("    • run [command], start process")
    print()
    
    # FILE OPERATIONS
    print("📁 FILE OPERATIONS")
    print("-" * 70)
    print("    • open [file/folder/app]")
    print("    • list files [path]")
    print("    • create folder [path], new folder")
    print("    • rename [path] to [new name]")
    print("    • move [source] to [destination]")
    print("    • copy [source] to [destination]")
    print("    • delete [path]")
    print()
    
    # FILE TOOLS
    print("🔍 FILE TOOLS (Advanced)")
    print("-" * 70)
    print("    • info [path]             # File/folder details")
    print("    • find [pattern]          # Search files")
    print("    • zip [source] to [dest]  # Compress")
    print("    • unzip [archive] to [dest] # Extract")
    print("    • size of [folder]        # Folder size")
    print("    • large files [path] [size MB]")
    print("    • duplicates [path]       # Find duplicates")
    print()
    
    # BROWSER
    print("🌐 BROWSER COMMANDS")
    print("-" * 70)
    print("    • open browser [url], browser [url]")
    print("    • search [query], google [query]")
    print("    • youtube [search]")
    print()
    
    # AI COMMANDS
    print("🤖 AI COMMANDS (Requires GEMINI_API_KEY)")
    print("-" * 70)
    print("    • ask ai [question], ai [question], chat [question]")
    print("    • analyze image [path]")
    print("    • describe image [path]")
    print("    • extract text [image], ocr [image]")
    print("    • compare images [path1] and [path2]")
    print("    • vision [image] [question]")
    print("    • generate image [description], draw [description]")
    print("    • create logo [description]")
    print()
    
    # PRODUCTIVITY
    print("📝 PRODUCTIVITY COMMANDS")
    print("-" * 70)
    print("    • add task [description], new task")
    print("    • show tasks, list tasks")
    print("    • remind me [text], add reminder")
    print("    • show reminders")
    print("    • calculate [expression], calc [expression]")
    print("    • time, date")
    print()
    
    # APPLICATIONS
    print("🎯 APPLICATIONS")
    print("-" * 70)
    print("    • open [app name]        # Open any application")
    print("    • launch [app name]")
    print("    Examples: open notepad, open calculator, open vscode")
    print()
    
    # HELP
    print("❓ HELP & UTILITIES")
    print("-" * 70)
    print("    • help, commands         # Show this help")
    print("    • exit, quit, close      # Exit application")
    print()
    
    print("=" * 70)
    print("HOW TO USE:")
    print("=" * 70)
    print("1. Open Command Console in the dashboard")
    print("2. Type any command above (case-insensitive)")
    print("3. Press Enter or click Send")
    print("4. Or use Voice Commands: Click 🎤 microphone button")
    print()
    print("💡 TIPS:")
    print("  • Commands work with natural language")
    print("  • Example: 'Take a screenshot' works same as 'screenshot'")
    print("  • Voice commands: Speak naturally, wait 10 seconds")
    print("  • AI commands need GEMINI_API_KEY in .env.local")
    print()
    print("📚 For detailed examples, see: COMMANDS_REFERENCE.md")
    print("=" * 70)


if __name__ == "__main__":
    print_commands()

