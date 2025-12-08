#!/usr/bin/env python3
"""
Flask API Server for ORION OS Navigator Backend
Exposes the command processing functionality via REST API
"""

import os
import sys
import re
from pathlib import Path

# Add the scripts directory to the path so we can import orion_os_navigator
sys.path.insert(0, str(Path(__file__).parent))

# Import Flask and CORS
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("Installing Flask and flask-cors...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors"])
    from flask import Flask, request, jsonify
    from flask_cors import CORS

# Import backend components
from orion_os_navigator import (
    Config, SystemController, VoiceEngine, GeminiAI, CommandProcessor, DataManager
)
import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

# Global instances (initialized on first request)
_processor = None
_system = None
_voice = None
_ai = None

def get_processor():
    """Lazy initialization of command processor"""
    global _processor, _system, _voice, _ai
    
    if _processor is None:
        # Initialize configuration
        Config.init_directories()
        
        # Initialize core systems
        _system = SystemController()
        _voice = VoiceEngine()
        _ai = GeminiAI()
        
        # Initialize command processor (app parameter is None for API mode)
        _processor = CommandProcessor(_system, _voice, _ai, None)
        
        print("✓ Backend initialized successfully")
    
    return _processor

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "ORION OS Navigator API",
        "version": Config.VERSION
    })

@app.route('/api/command', methods=['POST'])
def process_command():
    """Process a command and return response"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        speak_response = data.get('speak', False)  # Option to speak the response
        
        if not command:
            return jsonify({
                "success": False,
                "error": "No command provided"
            }), 400
        
        processor = get_processor()
        
        # Handle commands that require app instance
        cmd_lower = command.lower().strip()
        
        # Tasks and reminders - use DataManager directly
        if cmd_lower.startswith("add task") or cmd_lower.startswith("new task"):
            task_text = command.lower().replace("add task", "").replace("new task", "").strip()
            if task_text:
                tasks = DataManager.load_json(Config.TASKS_FILE, [])
                tasks.append({"text": task_text, "done": False, "created": datetime.datetime.now().isoformat()})
                DataManager.save_json(Config.TASKS_FILE, tasks)
                response = f"Task added: {task_text}"
            else:
                response = "What task would you like to add?"
        elif cmd_lower.startswith("show tasks") or cmd_lower.startswith("list tasks"):
            tasks = DataManager.load_json(Config.TASKS_FILE, [])
            if not tasks:
                response = "No tasks."
            else:
                response = "\n".join([f"{'✅' if t.get('done') else '⬜'} {t.get('text', '')}" for t in tasks[:10]])
        elif cmd_lower.startswith("remind me") or cmd_lower.startswith("set reminder") or cmd_lower.startswith("add reminder"):
            reminder_text = cmd_lower.replace("remind me to", "").replace("remind me", "").replace("set reminder", "").replace("add reminder", "").strip()
            if reminder_text:
                reminders = DataManager.load_json(Config.REMINDERS_FILE, [])
                reminders.append({"text": reminder_text, "created": datetime.datetime.now().isoformat()})
                DataManager.save_json(Config.REMINDERS_FILE, reminders)
                response = f"Reminder set: {reminder_text}"
            else:
                response = "What should I remind you about?"
        elif cmd_lower.startswith("show reminders") or cmd_lower.startswith("list reminders"):
            reminders = DataManager.load_json(Config.REMINDERS_FILE, [])
            if not reminders:
                response = "No reminders."
            else:
                response = "\n".join([f"🔔 {r.get('text', '')}" for r in reminders[:10]])
        elif cmd_lower in ["exit", "quit", "close", "goodbye"]:
            response = "Backend API server is still running. Use Ctrl+C in the server terminal to stop."
        else:
            # Use processor for other commands
            response = processor.process(command)
        
        # Speak the response if requested
        if speak_response and _voice:
            try:
                # Clean response text (remove emojis and special chars for better TTS)
                clean_response = response
                # Remove emoji-like patterns
                import re
                clean_response = re.sub(r'[^\w\s.,!?;:()\-]', '', clean_response)
                if clean_response.strip():
                    _voice.speak(clean_response)
            except Exception as e:
                print(f"Voice speak error: {e}")
        
        return jsonify({
            "success": True,
            "command": command,
            "response": response
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Command processing error: {error_trace}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Get system information (formatted string)"""
    try:
        processor = get_processor()
        info = processor._cmd_system_info("system info")
        return jsonify({
            "success": True,
            "info": info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/system/metrics', methods=['GET'])
def system_metrics():
    """Get raw system metrics data"""
    try:
        processor = get_processor()
        info = processor.system.get_system_info()
        
        # Format uptime
        uptime_seconds = info.get("uptime", 0)
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        uptime_str = ""
        if days > 0:
            uptime_str = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        else:
            uptime_str = f"{minutes}m"
        
        # Get temperature (try to extract from temps)
        temperature = None
        temps = info.get("temps", {})
        if temps:
            # Get first available temperature
            for key, values in temps.items():
                if values:
                    temperature = values[0].current
                    break
        
        # Default temperature if not available
        if temperature is None:
            temperature = 40  # Default fallback
        
        return jsonify({
            "success": True,
            "metrics": {
                "cpu": round(info.get("cpu", 0), 1),
                "memory": round(info.get("memory", 0), 1),
                "memory_used": info.get("memory_used", 0),
                "memory_total": info.get("memory_total", 0),
                "storage": round(info.get("disk", 0), 1),
                "storage_used": info.get("disk_used", 0),
                "storage_total": info.get("disk_total", 0),
                "temperature": round(temperature, 1),
                "battery": info.get("battery", {}).get("percent", None) if info.get("battery") else None,
                "battery_plugged": info.get("battery", {}).get("plugged", False) if info.get("battery") else False,
                "uptime": uptime_str,
                "uptime_seconds": uptime_seconds,
                "platform": info.get("platform", "Unknown"),
                "hostname": info.get("hostname", "Unknown")
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    try:
        tasks = DataManager.load_json(Config.TASKS_FILE, [])
        return jsonify({
            "success": True,
            "tasks": tasks
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task"""
    try:
        data = request.get_json()
        task = data.get('task', {})
        
        tasks = DataManager.load_json(Config.TASKS_FILE, [])
        tasks.append(task)
        DataManager.save_json(Config.TASKS_FILE, tasks)
        
        return jsonify({
            "success": True,
            "task": task
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    """Get all reminders"""
    try:
        reminders = DataManager.load_json(Config.REMINDERS_FILE, [])
        return jsonify({
            "success": True,
            "reminders": reminders
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/reminders', methods=['POST'])
def add_reminder():
    """Add or update a reminder"""
    try:
        data = request.get_json()
        reminder = data.get('reminder', {})
        
        reminders = DataManager.load_json(Config.REMINDERS_FILE, [])
        
        # If reminder has an ID, update existing; otherwise add new
        if reminder.get('id'):
            reminder_id = reminder.get('id')
            found = False
            for i, r in enumerate(reminders):
                if str(r.get('id')) == str(reminder_id):
                    reminders[i] = reminder
                    found = True
                    break
            if not found:
                reminders.append(reminder)
        else:
            reminders.append(reminder)
        
        DataManager.save_json(Config.REMINDERS_FILE, reminders)
        
        return jsonify({
            "success": True,
            "reminder": reminder
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/reminders', methods=['DELETE'])
def delete_reminder():
    """Delete a reminder"""
    try:
        data = request.get_json()
        reminder_id = data.get('id')
        
        if not reminder_id:
            return jsonify({
                "success": False,
                "error": "Reminder ID is required"
            }), 400
        
        reminders = DataManager.load_json(Config.REMINDERS_FILE, [])
        reminders = [r for r in reminders if str(r.get('id')) != str(reminder_id)]
        DataManager.save_json(Config.REMINDERS_FILE, reminders)
        
        return jsonify({
            "success": True,
            "message": "Reminder deleted"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes"""
    try:
        notes = DataManager.load_json(Config.NOTES_FILE, [])
        return jsonify({
            "success": True,
            "notes": notes
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/notes', methods=['POST'])
def add_note():
    """Add a new note"""
    try:
        data = request.get_json()
        note = data.get('note', {})
        
        notes = DataManager.load_json(Config.NOTES_FILE, [])
        notes.append(note)
        DataManager.save_json(Config.NOTES_FILE, notes)
        
        return jsonify({
            "success": True,
            "note": note
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get command history"""
    try:
        processor = get_processor()
        history = processor.history
        return jsonify({
            "success": True,
            "history": history
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/voice/speak', methods=['POST'])
def speak_text():
    """Speak text using TTS"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                "success": False,
                "error": "No text provided"
            }), 400
        
        processor = get_processor()
        if _voice:
            # Clean text for better TTS
            import re
            clean_text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
            if clean_text.strip():
                _voice.speak(clean_text)
                return jsonify({
                    "success": True,
                    "message": "Speaking text"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Text is empty after cleaning"
                }), 400
        else:
            return jsonify({
                "success": False,
                "error": "Voice engine not initialized"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/voice/stop', methods=['POST'])
def stop_speaking():
    """Stop current speech"""
    try:
        if _voice:
            _voice.stop_speaking()
            return jsonify({
                "success": True,
                "message": "Speech stopped"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Voice engine not initialized"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/voice/listen', methods=['POST'])
def listen_voice():
    """Listen for voice input and return recognized text"""
    try:
        data = request.get_json() or {}
        timeout = data.get('timeout', 7)
        
        processor = get_processor()  # Ensure voice is initialized
        
        if not _voice:
            return jsonify({
                "success": False,
                "error": "Voice engine not initialized"
            }), 500
        
        if not _voice.has_microphone:
            return jsonify({
                "success": False,
                "error": "Microphone not available. Please check your microphone permissions and PyAudio installation."
            }), 500
        
        # Speak "Listening" first (non-blocking)
        try:
            _voice.speak("Listening")
            # Give TTS a moment to start
            import time
            time.sleep(1.0)  # Increased delay to let TTS finish
        except Exception as e:
            print(f"Warning: Could not speak 'Listening': {e}")
        
        # Listen for voice input directly (this will block, but Flask can handle it)
        try:
            print(f"Starting voice recognition with timeout {timeout} seconds...")
            print("Waiting for user to speak...")
            recognized_text = _voice.listen(timeout=timeout)
            print(f"Voice recognition result: '{recognized_text}'")
            
            if recognized_text and recognized_text.strip():
                # Normalize the text (fix common speech recognition issues)
                normalized_text = recognized_text.strip()
                # Fix common misrecognitions
                normalized_text = normalized_text.replace("you tube", "youtube")
                normalized_text = normalized_text.replace("you to", "youtube")
                normalized_text = normalized_text.replace("you too", "youtube")
                normalized_text = normalized_text.replace("open you tube", "open youtube")
                # Fix "on youtube" patterns
                normalized_text = re.sub(r'\s+on\s+you\s*tube', ' on youtube', normalized_text, flags=re.IGNORECASE)
                normalized_text = re.sub(r'\s+in\s+you\s*tube', ' in youtube', normalized_text, flags=re.IGNORECASE)
                
                print(f"Normalized command: '{normalized_text}'")
                return jsonify({
                    "success": True,
                    "text": normalized_text,
                    "message": "Voice recognized successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "No speech detected. Please try again. Make sure your microphone is working and speak clearly."
                }), 400
                
        except Exception as listen_error:
            error_msg = str(listen_error)
            print(f"Listen error: {error_msg}")
            return jsonify({
                "success": False,
                "error": f"Voice recognition error: {error_msg}"
            }), 500
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Voice listen endpoint error: {error_trace}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/voice/status', methods=['GET'])
def voice_status():
    """Get voice engine status"""
    try:
        if not _voice:
            return jsonify({
                "success": True,
                "available": False,
                "microphone": False,
                "tts": False
            })
        
        return jsonify({
            "success": True,
            "available": True,
            "microphone": _voice.has_microphone,
            "tts": _voice.tts_engine is not None,
            "is_speaking": _voice.is_speaking
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/volume', methods=['GET'])
def get_volume():
    """Get current system volume"""
    try:
        processor = get_processor()
        current_volume = processor.system.get_volume()
        return jsonify({
            "success": True,
            "volume": current_volume
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Set system volume"""
    try:
        data = request.get_json()
        volume = data.get('volume')
        
        if volume is None or not isinstance(volume, (int, float)):
            return jsonify({
                "success": False,
                "error": "Volume level required (0-100)"
            }), 400
        
        volume = max(0, min(100, int(volume)))
        
        processor = get_processor()
        success, message = processor.system.set_volume(volume)
        
        if success:
            return jsonify({
                "success": True,
                "volume": volume,
                "message": message
            })
        else:
            return jsonify({
                "success": False,
                "error": message
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("ORION OS Navigator API Server")
    print("=" * 60)
    print(f"Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)

