#!/usr/bin/env python3
"""
ORION OS NAVIGATOR v3.0
Advanced AI Command Center with Gemini Integration
Cross-platform support for Windows, macOS, and Linux
"""

import os
import sys
import json
import time
import threading
import subprocess
import platform
import shutil
import re
import math
import datetime
import base64
import tempfile
import webbrowser
import ctypes
import zipfile
from pathlib import Path
from typing import Optional, Callable, Dict, List, Any, Tuple
import queue

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================

import logging

# Configure simple logger for cleaner debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

def install_package(package: str, pip_name: str = None):
    """Install a package if not available"""
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name or package])

# Core dependencies
DEPENDENCIES = [
    ("customtkinter", "customtkinter"),
    ("PIL", "Pillow"),
    ("psutil", "psutil"),
    ("requests", "requests"),
    ("pyttsx3", "pyttsx3"),
    ("speech_recognition", "SpeechRecognition"),
    ("fuzzywuzzy", "fuzzywuzzy"),
    ("Levenshtein", "python-Levenshtein"),
    ("cv2", "opencv-python"),
]

if platform.system() == "Windows":
    DEPENDENCIES.extend([
        ("pycaw", "pycaw"),
        ("comtypes", "comtypes"),
    ])

print("Checking dependencies...")
for module, pip_name in DEPENDENCIES:
    install_package(module, pip_name)

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageGrab
import psutil
import requests
import pyttsx3
import speech_recognition as sr
from fuzzywuzzy import fuzz, process

# Try to import OpenCV for camera
CAMERA_AVAILABLE = False
try:
    import cv2
    CAMERA_AVAILABLE = True
except ImportError:
    print("Note: Install opencv-python for camera support: pip install opencv-python")

# Platform-specific imports
PLATFORM = platform.system()
VOLUME_AVAILABLE = False
PYCAW_AVAILABLE = False

if PLATFORM == "Windows":
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        PYCAW_AVAILABLE = True
        VOLUME_AVAILABLE = True
    except ImportError:
        print("Note: Install pycaw for volume control: pip install pycaw comtypes")

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration"""
    APP_NAME = "ORION OS NAVIGATOR"
    VERSION = "3.0"
    
    # Paths
    DATA_DIR = Path.home() / ".orion_os"
    TASKS_FILE = DATA_DIR / "tasks.json"
    REMINDERS_FILE = DATA_DIR / "reminders.json"
    NOTES_FILE = DATA_DIR / "notes.json"
    HISTORY_FILE = DATA_DIR / "history.json"
    SETTINGS_FILE = DATA_DIR / "settings.json"
    SCREENSHOTS_DIR = DATA_DIR / "screenshots"
    GENERATED_DIR = DATA_DIR / "generated_images"
    
    # Theme Colors (Cyberpunk)
    COLORS = {
        "bg_dark": "#0a0e14",
        "bg_card": "#0d1117",
        "bg_card_hover": "#161b22",
        "bg_sidebar": "#0d1117",
        "accent_cyan": "#00d4ff",
        "accent_green": "#00ff88",
        "accent_purple": "#a855f7",
        "accent_orange": "#ff6b35",
        "accent_red": "#ff4757",
        "accent_yellow": "#ffd93d",
        "text_primary": "#e6edf3",
        "text_secondary": "#8b949e",
        "text_muted": "#484f58",
        "border": "#21262d",
        "success": "#00ff88",
        "warning": "#ffd93d",
        "error": "#ff4757",
    }
    
    # Gemini API
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBNicbJCbzibrJpWVbMg_flCBnGXW0D_dk")
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    @classmethod
    def init_directories(cls):
        """Initialize all required directories"""
        dirs = [cls.DATA_DIR, cls.SCREENSHOTS_DIR, cls.GENERATED_DIR]
        for d in dirs:
            try:
                d.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                print(f"Warning: Cannot create directory {d}")


# ============================================================================
# DATA MANAGER
# ============================================================================

class DataManager:
    """Handles persistent data storage"""
    
    @staticmethod
    def load_json(filepath: Path, default: Any = None) -> Any:
        """Load JSON file with error handling"""
        if default is None:
            default = []
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {filepath}: {e}")
        return default
    
    @staticmethod
    def save_json(filepath: Path, data: Any) -> bool:
        """Save data to JSON file"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except IOError as e:
            print(f"Error saving {filepath}: {e}")
            return False


# ============================================================================
# GEMINI AI INTEGRATION
# ============================================================================

class GeminiAI:
    """Google Gemini AI Integration for vision and generation"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.available = bool(self.api_key)
        self._last_request_time = 0
        self._rate_limit_delay = 2.0  # Minimum seconds between requests (increased for free tier)
        self._request_lock = threading.Lock()
        self._consecutive_rate_limits = 0  # Track consecutive rate limit errors
        self._max_retries = 3  # Maximum retries for rate limit errors

    def _make_request(self, model: str, payload: dict, retry_count: int = 0) -> dict:
        """Make API request to Gemini with rate limiting and error handling"""
        if not self.available or not self.api_key:
            return {"error": "Gemini API key not configured. Set GEMINI_API_KEY environment variable or configure it in settings."}

        with self._request_lock:
            # Rate limiting with exponential backoff if we've hit rate limits
            base_delay = self._rate_limit_delay
            if self._consecutive_rate_limits > 0:
                # Exponential backoff: 2s, 4s, 8s, 16s, etc.
                base_delay = self._rate_limit_delay * (2 ** min(self._consecutive_rate_limits, 4))
            
            elapsed = time.time() - self._last_request_time
            if elapsed < base_delay:
                sleep_time = base_delay - elapsed
                time.sleep(sleep_time)

            # Use correct Gemini API endpoint format with header-based authentication
            url = f"{Config.GEMINI_API_URL}/models/{model}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                self._last_request_time = time.time()

                if response.status_code == 404:
                    # Reset rate limit counter on successful alternative model
                    self._consecutive_rate_limits = 0
                    # Try alternative model names if 404
                    alternative_models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro"]
                    for alt_model in alternative_models:
                        if alt_model != model:
                            alt_url = f"{Config.GEMINI_API_URL}/models/{alt_model}:generateContent"
                            alt_response = requests.post(alt_url, json=payload, headers=headers, timeout=60)
                            if alt_response.status_code == 200:
                                return alt_response.json()
                    return {"error": f"Model not found (404). Tried: {model} and alternatives. Please check available models."}
                elif response.status_code == 429:
                    # Rate limit exceeded - implement exponential backoff retry
                    self._consecutive_rate_limits += 1
                    wait_time = min(2 ** retry_count, 60)  # Cap at 60 seconds
                    
                    if retry_count < self._max_retries:
                        # Retry with exponential backoff
                        print(f"Rate limit hit. Waiting {wait_time} seconds before retry {retry_count + 1}/{self._max_retries}...")
                        time.sleep(wait_time)
                        return self._make_request(model, payload, retry_count + 1)
                    else:
                        return {
                            "error": f"Rate limit exceeded. Please wait {wait_time} seconds before trying again. "
                                   f"Free tier has limits: ~15 requests per minute. Consider upgrading your API plan."
                        }
                elif response.status_code == 401:
                    self._consecutive_rate_limits = 0
                    return {"error": "Invalid API key. Please check your GEMINI_API_KEY. Get a new key from: https://makersuite.google.com/app/apikey"}
                elif response.status_code == 403:
                    self._consecutive_rate_limits = 0
                    return {"error": "API access forbidden. Check your API key permissions. Get your API key from: https://makersuite.google.com/app/apikey"}

                # Success - reset rate limit counter
                self._consecutive_rate_limits = 0
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                return {"error": "Request timed out. Please try again."}
            except requests.exceptions.ConnectionError:
                return {"error": "Connection error. Please check your internet connection."}
            except requests.exceptions.RequestException as e:
                return {"error": f"API Error: {str(e)}"}
    
    def chat(self, message: str) -> str:
        """Chat with Gemini"""
        payload = {
            "contents": [{"parts": [{"text": message}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            }
        }
        
        # Use gemini-1.5-flash (stable model with wide availability)
        result = self._make_request("gemini-1.5-flash", payload)
        
        if "error" in result:
            return f"AI Error: {result['error']}"
        
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Unable to get response from AI. Please check your API key and try again."
    
    def analyze_image(self, image_path: str, question: str = "Describe this image in detail.") -> str:
        """Analyze an image using Gemini Vision"""
        try:
            img_path = Path(image_path).expanduser()
            if not img_path.exists():
                return f"Error: Image file not found: {image_path}"

            # Check file size (max 20MB for Gemini)
            file_size = img_path.stat().st_size
            if file_size > 20 * 1024 * 1024:
                return "Error: Image file too large. Maximum size is 20MB."

            with open(img_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Detect mime type
            ext = img_path.suffix.lower()
            mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                         ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}
            mime_type = mime_types.get(ext, "image/jpeg")
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": question},
                        {"inline_data": {"mime_type": mime_type, "data": image_data}}
                    ]
                }]
            }
            
            result = self._make_request("gemini-1.5-flash", payload)

            if "error" in result:
                return f"Vision Error: {result['error']}"
            
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Error analyzing image: {e}"
    
    def compare_images(self, path1: str, path2: str) -> str:
        """Compare two images"""
        try:
            images_data = []
            for path in [path1, path2]:
                with open(path, "rb") as f:
                    images_data.append(base64.b64encode(f.read()).decode("utf-8"))
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Compare these two images. Describe the similarities and differences."},
                        {"inline_data": {"mime_type": "image/jpeg", "data": images_data[0]}},
                        {"inline_data": {"mime_type": "image/jpeg", "data": images_data[1]}}
                    ]
                }]
            }
            
            result = self._make_request("gemini-1.5-flash", payload)

            if "error" in result:
                return f"Comparison Error: {result['error']}"
            
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Error comparing images: {e}"
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from image (OCR)"""
        return self.analyze_image(image_path, "Extract and return all text visible in this image. Format it properly.")
    
    def generate_image_description(self, description: str) -> str:
        """Generate detailed prompt for image generation"""
        prompt = f"""Create a detailed image generation prompt for: "{description}"
        Include: style, colors, composition, lighting, mood, and technical details.
        Return only the enhanced prompt, nothing else."""
        return self.chat(prompt)


# ============================================================================
# VOICE ENGINE
# ============================================================================

class VoiceEngine:
    """Text-to-speech and speech recognition"""
    
    def __init__(self):
        self.tts_engine = None
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.has_microphone = False
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.init_tts()
        self.init_microphone()
        
        # Start speech thread
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
    
    def init_tts(self):
        """Initialize text-to-speech engine"""
        # Check if TTS should be disabled via environment variable
        import os
        if os.environ.get('ORION_DISABLE_TTS', '').lower() in ('1', 'true', 'yes'):
            print("TTS disabled via ORION_DISABLE_TTS environment variable")
            self.tts_engine = None
            return

        try:
            # Initialize COM on Windows before creating TTS engine
            if PLATFORM == "Windows":
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception as com_err:
                    print(f"COM initialization warning: {com_err}")

            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 175)
            self.tts_engine.setProperty('volume', 0.9)

            # Try to set a good voice
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'english' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"TTS initialization error: {e}")
            print("TTS will be disabled, but the server will continue running.")
            self.tts_engine = None
    
    def init_microphone(self):
        """Initialize microphone"""
        try:
            # Probe microphone availability without keeping a persistent context
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Do not store an active Microphone instance to avoid nested context issues
            self.microphone = None
            self.has_microphone = True
        except Exception as e:
            # Provide actionable guidance if PyAudio is missing or cannot access the device
            msg = f"Microphone initialization error: {e}"
            print(msg)

            guidance = (
                "Microphone unavailable. Common cause: missing PyAudio. "
                "On Windows: run `pip install pipwin && pipwin install pyaudio`. "
                "Or install a prebuilt wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio. "
                "On macOS/Linux: try `pip install pyaudio` or install system audio dev headers first."
            )
            print(guidance)

            # If GUI has status label, update it so user sees guidance in the app
            try:
                if hasattr(self, 'status_label'):
                    self.status_label.configure(text="Mic unavailable — see console for install help")
            except Exception:
                pass

            self.microphone = None
            self.has_microphone = False
    
    def _speech_worker(self):
        """Background worker for speech synthesis"""
        # Initialize COM in this thread (required on Windows for pyttsx3)
        if PLATFORM == "Windows":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception as com_err:
                print(f"COM initialization in speech thread warning: {com_err}")

        while True:
            try:
                text = self.speech_queue.get()
                if text and self.tts_engine:
                    self.is_speaking = True
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                    self.is_speaking = False
            except Exception as e:
                print(f"Speech error: {e}")
                self.is_speaking = False
    
    def speak(self, text: str, language: str = "en"):
        """Speak text (non-blocking)"""
        if not self.is_speaking:
            self.speech_queue.put(text)
    
    def stop_speaking(self):
        """Stop current speech"""
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        self.is_speaking = False
        # Clear queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except:
                break
    
    def listen(self, timeout: int = 5) -> Optional[str]:
        """Listen for voice input (push-to-talk style)"""
        if not getattr(self, 'has_microphone', False):
            print("ERROR: Microphone not available")
            return None

        try:
            print(f"Setting up microphone for {timeout} second timeout...")
            # Create a fresh Microphone context each listen call to avoid re-entering
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening... Speak now!")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)

            print("Audio captured, processing...")
            # Try Google first, then offline
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"Recognized (Google): {text}")
                return text
            except sr.UnknownValueError:
                print("ERROR: Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"ERROR: Google recognition failed: {e}")
                # Try offline recognition
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print(f"Recognized (Sphinx): {text}")
                    return text
                except Exception as sphinx_error:
                    print(f"ERROR: Sphinx recognition also failed: {sphinx_error}")
                    return None
        except sr.WaitTimeoutError:
            print(f"ERROR: Timeout after {timeout} seconds - no speech detected")
            return None
        except Exception as e:
            print(f"Listen error: {e}")
            import traceback
            traceback.print_exc()
            return None


# ============================================================================
# SYSTEM CONTROLLER
# ============================================================================

class SystemController:
    """Cross-platform system controls"""
    
    def __init__(self):
        self.platform = PLATFORM
        self.last_screenshot_path = None
    
    # ---------------------- VOLUME CONTROL ----------------------
    
    def _set_volume_powershell(self, level: float) -> bool:
        """Set volume using PowerShell Core Audio API - returns True if successful"""
        try:
            # Create a temporary PowerShell script file for more reliable execution
            script_content = f'''$ErrorActionPreference = "Stop"
try {{
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Audio {{
    [DllImport("ole32.dll")]
    public static extern int CoCreateInstance([MarshalAs(UnmanagedType.LPStruct)] Guid rclsid, IntPtr pUnkOuter, uint dwClsContext, [MarshalAs(UnmanagedType.LPStruct)] Guid riid, out IntPtr ppv);
    [DllImport("ole32.dll")]
    public static extern int CoInitialize(IntPtr pvReserved);
    [DllImport("ole32.dll")]
    public static extern void CoUninitialize();
    public static bool SetVolume(float level) {{
        try {{
            CoInitialize(IntPtr.Zero);
            Guid CLSID_MMDeviceEnumerator = new Guid("{{BCDE0395-E52F-467C-8E3D-C4579291692E}}");
            Guid IID_IMMDeviceEnumerator = new Guid("{{A95664D2-9614-4F35-A746-DE8DB63617E6}}");
            Guid IID_IAudioEndpointVolume = new Guid("{{5CDF2C82-841E-4546-9722-0CF74078229A}}");
            IntPtr pDeviceEnumerator = IntPtr.Zero;
            int hr = CoCreateInstance(CLSID_MMDeviceEnumerator, IntPtr.Zero, 1, IID_IMMDeviceEnumerator, out pDeviceEnumerator);
            if (hr == 0 && pDeviceEnumerator != IntPtr.Zero) {{
                dynamic deviceEnumerator = Marshal.GetObjectForIUnknown(pDeviceEnumerator);
                dynamic device = deviceEnumerator.GetDefaultAudioEndpoint(0, 0);
                IntPtr pDevice = Marshal.GetIUnknownForObject(device);
                if (pDevice != IntPtr.Zero) {{
                    dynamic audioEndpointVolume = Marshal.GetObjectForIUnknown(pDevice);
                    audioEndpointVolume.SetMasterVolumeLevelScalar(level, Guid.Empty);
                    Marshal.Release(pDevice);
                }}
                Marshal.Release(pDeviceEnumerator);
                CoUninitialize();
                return true;
            }}
            CoUninitialize();
        }} catch {{
            return false;
        }}
        return false;
    }}
}}
"@
    $result = [Audio]::SetVolume({level})
    if ($result) {{
        Write-Host "SUCCESS"
        exit 0
    }} else {{
        Write-Host "FAILED"
        exit 1
    }}
}} catch {{
    Write-Host "ERROR"
    exit 1
}}
'''
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script_content],
                capture_output=True, text=True, timeout=5  # Reduced timeout to prevent hanging
            )
            # Check both return code and output
            if result.returncode == 0 or "SUCCESS" in result.stdout:
                return True
            else:
                print(f"PowerShell volume error: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("PowerShell volume command timed out after 5 seconds")
            return False
        except Exception as e:
            print(f"PowerShell execution error: {e}")
            return False

    def _get_windows_volume_interface(self):
        """Get Windows volume interface (handles different pycaw versions)"""
        if not PYCAW_AVAILABLE:
            return None
        try:
            devices = AudioUtilities.GetSpeakers()
            if devices is None:
                return None
            # Use the EndpointVolume property directly (simplest API)
            try:
                return devices.EndpointVolume
            except AttributeError:
                # Fallback for different pycaw versions
                try:
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    return cast(interface, POINTER(IAudioEndpointVolume))
                except Exception:
                    pass
            return None
        except Exception as e:
            print(f"Volume interface error: {e}")
            return None

    def get_volume(self) -> int:
        """Get current volume level"""
        try:
            if self.platform == "Windows" and PYCAW_AVAILABLE:
                volume = self._get_windows_volume_interface()
                if volume:
                    return int(volume.GetMasterVolumeLevelScalar() * 100)
                # Fallback: use PowerShell
                result = subprocess.run(
                    ["powershell", "-Command", "(Get-AudioDevice -PlaybackVolume).Volume"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return int(float(result.stdout.strip()))
            elif self.platform == "Darwin":
                result = subprocess.run(
                    ["osascript", "-e", "output volume of (get volume settings)"],
                    capture_output=True, text=True
                )
                return int(result.stdout.strip())
            elif self.platform == "Linux":
                result = subprocess.run(
                    ["amixer", "get", "Master"], capture_output=True, text=True
                )
                match = re.search(r'\[(\d+)%\]', result.stdout)
                if match:
                    return int(match.group(1))
        except Exception as e:
            print(f"Volume get error: {e}")
        return 50

    def set_volume(self, level: int) -> Tuple[bool, str]:
        """Set volume level (0-100)"""
        level = max(0, min(100, level))
        try:
            if self.platform == "Windows":
                # Method 1: Try pycaw first (most reliable - sets exact volume)
                if PYCAW_AVAILABLE:
                    volume = self._get_windows_volume_interface()
                    if volume:
                        try:
                            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                            # Verify the volume was actually set
                            time.sleep(0.1)  # Small delay for volume to update
                            actual_volume = int(volume.GetMasterVolumeLevelScalar() * 100)
                            if abs(actual_volume - level) <= 2:  # Allow 2% tolerance
                                return True, f"Volume set to {level}%"
                            else:
                                return True, f"Volume set to {level}% (actual: {actual_volume}%)"
                        except Exception as e:
                            print(f"Volume set error (pycaw): {e}")
                
                # Method 2: PowerShell Core Audio API (sets exact volume)
                if self._set_volume_powershell(level / 100.0):
                    # Verify the volume was actually set
                    time.sleep(0.1)  # Small delay for volume to update
                    actual_volume = self.get_volume()
                    if abs(actual_volume - level) <= 2:  # Allow 2% tolerance
                        return True, f"Volume set to {level}%"
                    else:
                        return True, f"Volume set to {level}% (actual: {actual_volume}%)"
                
                # Method 3: Try using Windows API via ctypes directly (incremental fallback)
                # Note: This method is slow for large changes, so limit it
                try:
                    import ctypes
                    
                    # Get current volume first
                    current_vol = self.get_volume()
                    diff = level - current_vol
                    steps = abs(diff)
                    
                    # Only use incremental for small adjustments (max 30 steps to avoid freezing)
                    if steps > 0 and steps <= 30:
                        VK_VOLUME_UP = 0xAF
                        VK_VOLUME_DOWN = 0xAE
                        KEYEVENTF_KEYUP = 0x0002
                        
                        # Use faster key presses to minimize blocking
                        delay = 0.005  # Reduced delay
                        
                        for _ in range(steps):
                            vk = VK_VOLUME_UP if diff > 0 else VK_VOLUME_DOWN
                            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
                            ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
                            time.sleep(delay)
                        
                        return True, f"Volume adjusted to approximately {level}%"
                    elif steps > 30:
                        # For large changes, suggest using exact volume setting
                        return False, f"Volume change too large ({steps} steps). Use 'volume {level}' for exact setting or install pycaw."
                except Exception as e:
                    print(f"Windows API volume control error: {e}")
                
                # Method 5: Try nircmd as last resort
                try:
                    subprocess.run(
                        ["nircmd", "setsysvolume", str(int(level * 655.35))],
                        capture_output=True, timeout=5, check=False
                    )
                    return True, f"Volume set to {level}%"
                except:
                    pass
                
                return False, "Volume control not available. Install pycaw: pip install pycaw comtypes"
            
            elif self.platform == "Darwin":
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=False)
                return True, f"Volume set to {level}%"
            
            elif self.platform == "Linux":
                subprocess.run(["amixer", "set", "Master", f"{level}%"], capture_output=True, check=False)
                return True, f"Volume set to {level}%"
            
        except Exception as e:
            return False, f"Volume error: {e}"
        
        return False, "Volume control not available"
    
    def volume_up(self, amount: int = 10) -> Tuple[bool, str]:
        """Increase volume"""
        return self.adjust_volume(amount)
    
    def volume_down(self, amount: int = 10) -> Tuple[bool, str]:
        """Decrease volume"""
        return self.adjust_volume(-amount)

    def adjust_volume(self, delta: int) -> Tuple[bool, str]:
        """Adjust volume by delta (positive or negative) using the canonical algorithm.

        This centralizes the logic so up/down use identical behavior and provides
        debug logging of current, target and actual volumes for transparency.
        """
        try:
            current = self.get_volume()
            target = max(0, min(100, int(current + delta)))
            logger.debug(f"Adjusting volume: current={current}, delta={delta}, target={target}")
            success, message = self.set_volume(target)
            # After attempt, read back actual volume for verification
            actual = self.get_volume()
            logger.debug(f"Adjust result: success={success}, message={message}, actual={actual}")
            # Normalize message to include actual value when possible
            if success:
                return True, f"Volume set to {actual}%"
            return False, message
        except Exception as e:
            return False, f"Adjust volume error: {e}"
    
    def mute(self) -> Tuple[bool, str]:
        """Mute audio"""
        return self.set_volume(0)
    
    # ---------------------- SCREENSHOT ----------------------
    
    def take_screenshot(self, name: str = None) -> Tuple[bool, str]:
        """Take a screenshot"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png" if name else f"screenshot_{timestamp}.png"
            filepath = Config.SCREENSHOTS_DIR / filename
            
            Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            
            if self.platform == "Windows":
                screenshot = ImageGrab.grab()
                screenshot.save(filepath)
            elif self.platform == "Darwin":
                subprocess.run(["screencapture", str(filepath)])
            elif self.platform == "Linux":
                # Try multiple screenshot tools
                tools = [
                    ["gnome-screenshot", "-f", str(filepath)],
                    ["scrot", str(filepath)],
                    ["import", "-window", "root", str(filepath)],
                ]
                success = False
                for tool in tools:
                    try:
                        subprocess.run(tool, check=True, capture_output=True)
                        success = True
                        break
                    except:
                        continue
                if not success:
                    return False, "No screenshot tool available. Install: gnome-screenshot, scrot, or imagemagick"
            
            self.last_screenshot_path = filepath
            return True, f"Screenshot saved: {filepath}"
        except Exception as e:
            return False, f"Screenshot error: {e}"
    
    def rename_last_screenshot(self, new_name: str) -> Tuple[bool, str]:
        """Rename the last screenshot"""
        if not self.last_screenshot_path:
            return False, "No recent screenshot to rename. Take a screenshot first."

        if not self.last_screenshot_path.exists():
            return False, f"Screenshot file no longer exists: {self.last_screenshot_path}"

        if not new_name or not new_name.strip():
            return False, "Please provide a new name for the screenshot."

        try:
            # Clean the new name
            new_name = new_name.strip().strip('"').strip("'")
            # Remove invalid characters for filenames
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                new_name = new_name.replace(char, '_')

            # Ensure .png extension
            if not new_name.lower().endswith('.png'):
                new_name = f"{new_name}.png"

            new_path = self.last_screenshot_path.parent / new_name

            # Check if target already exists
            if new_path.exists():
                return False, f"A file named '{new_name}' already exists."

            self.last_screenshot_path.rename(new_path)
            self.last_screenshot_path = new_path
            return True, f"Screenshot renamed to: {new_path.name}"
        except PermissionError:
            return False, "Permission denied. Cannot rename the screenshot."
        except Exception as e:
            return False, f"Rename error: {e}"
    
    def move_last_screenshot(self, destination: str) -> Tuple[bool, str]:
        """Move the last screenshot to a destination"""
        if not self.last_screenshot_path:
            return False, "No recent screenshot to move. Take a screenshot first."

        if not self.last_screenshot_path.exists():
            return False, f"Screenshot file no longer exists: {self.last_screenshot_path}"

        if not destination or not destination.strip():
            return False, "Please provide a destination path."

        try:
            # Clean and expand destination path
            destination = destination.strip().strip('"').strip("'")
            dest_path = Path(destination).expanduser()

            # Handle common folder names
            common_folders = {
                "desktop": Path.home() / "Desktop",
                "documents": Path.home() / "Documents",
                "downloads": Path.home() / "Downloads",
                "pictures": Path.home() / "Pictures",
                "images": Path.home() / "Pictures",
                "photos": Path.home() / "Pictures",
            }
            dest_lower = destination.lower()
            if dest_lower in common_folders:
                dest_path = common_folders[dest_lower]

            # Resolve the path
            try:
                if dest_path.exists():
                    dest_path = dest_path.resolve()
                else:
                    # Create parent directories if needed
                    dest_path.mkdir(parents=True, exist_ok=True)
                    dest_path = dest_path.resolve()
            except (OSError, ValueError) as e:
                return False, f"Invalid destination path: {destination}"

            # If destination is a directory, append the filename
            if dest_path.is_dir():
                dest_path = dest_path / self.last_screenshot_path.name
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if target already exists
            if dest_path.exists():
                # Add timestamp to avoid overwrite
                stem = dest_path.stem
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                dest_path = dest_path.parent / f"{stem}_{timestamp}{dest_path.suffix}"

            shutil.move(str(self.last_screenshot_path), str(dest_path))
            self.last_screenshot_path = dest_path
            return True, f"Screenshot moved to: {dest_path}"
        except PermissionError:
            return False, f"Permission denied. Cannot move to: {destination}"
        except Exception as e:
            return False, f"Move error: {e}"
    
    # ---------------------- FILE OPERATIONS ----------------------
    
    def open_file(self, path: str) -> Tuple[bool, str]:
        """Open a file or folder"""
        try:
            if not path or not path.strip():
                return False, "No file path specified."

            # Clean and expand path
            path = path.strip().strip('"').strip("'")
            file_path = Path(path).expanduser()

            if not file_path.exists():
                # Try common locations
                common_paths = [
                    Path.home() / path,
                    Path.home() / "Desktop" / path,
                    Path.home() / "Documents" / path,
                    Path.home() / "Downloads" / path,
                    Path.home() / "Pictures" / path,
                    Path.home() / "Videos" / path,
                    Path.home() / "Music" / path,
                ]
                found = False
                for p in common_paths:
                    if p.exists():
                        file_path = p
                        found = True
                        break
                if not found:
                    return False, f"File/folder not found: {path}"

            # Validate path is safe (no directory traversal attacks)
            try:
                file_path = file_path.resolve()
            except (OSError, ValueError):
                return False, f"Invalid path: {path}"

            if self.platform == "Windows":
                os.startfile(str(file_path))
            elif self.platform == "Darwin":
                subprocess.run(["open", str(file_path)], check=True)
            else:
                subprocess.run(["xdg-open", str(file_path)], check=True)

            return True, f"Opened: {file_path}"
        except PermissionError:
            return False, f"Permission denied: {path}"
        except FileNotFoundError:
            return False, f"File not found: {path}"
        except Exception as e:
            return False, f"Open error: {e}"
    
    def open_folder(self, path: str = None) -> Tuple[bool, str]:
        """Open a folder in file explorer"""
        if path is None:
            path = str(Path.home())
        return self.open_file(path)
    
    def rename_file(self, old_path: str, new_name: str) -> Tuple[bool, str]:
        """Rename a file"""
        try:
            old = Path(old_path).expanduser()
            if not old.exists():
                return False, f"File not found: {old_path}"
            
            new = old.parent / new_name
            if not new.suffix:
                new = new.with_suffix(old.suffix)
            
            old.rename(new)
            return True, f"Renamed to: {new.name}"
        except Exception as e:
            return False, f"Rename error: {e}"
    
    def move_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """Move a file to destination"""
        try:
            src = Path(source).expanduser()
            if not src.exists():
                return False, f"Source not found: {source}"
            
            dst = Path(destination).expanduser()
            if dst.is_dir():
                dst = dst / src.name
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src), str(dst))
            return True, f"Moved to: {dst}"
        except Exception as e:
            return False, f"Move error: {e}"
    
    def copy_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """Copy a file"""
        try:
            src = Path(source).expanduser()
            if not src.exists():
                return False, f"Source not found: {source}"
            
            dst = Path(destination).expanduser()
            if dst.is_dir():
                dst = dst / src.name
            
            if src.is_dir():
                shutil.copytree(str(src), str(dst))
            else:
                shutil.copy2(str(src), str(dst))
            
            return True, f"Copied to: {dst}"
        except Exception as e:
            return False, f"Copy error: {e}"
    
    def delete_file(self, path: str) -> Tuple[bool, str]:
        """Delete a file or folder"""
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return False, f"Not found: {path}"
            
            if p.is_dir():
                shutil.rmtree(str(p))
            else:
                p.unlink()
            
            return True, f"Deleted: {path}"
        except Exception as e:
            return False, f"Delete error: {e}"
    
    def create_folder(self, path: str) -> Tuple[bool, str]:
        """Create a new folder"""
        try:
            p = Path(path).expanduser()
            p.mkdir(parents=True, exist_ok=True)
            return True, f"Created folder: {p}"
        except Exception as e:
            return False, f"Create folder error: {e}"
    
    def list_files(self, path: str = None) -> List[Dict]:
        """List files in a directory"""
        try:
            p = Path(path).expanduser() if path else Path.home()
            if not p.exists():
                return []
            
            files = []
            for item in p.iterdir():
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": datetime.datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
            
            return sorted(files, key=lambda x: (not x["is_dir"], x["name"].lower()))
        except Exception as e:
            print(f"List files error: {e}")
            return []
    
    # ---------------------- APPLICATIONS ----------------------
    
    def open_browser(self, url: str = None) -> Tuple[bool, str]:
        """Open web browser"""
        try:
            if url:
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                webbrowser.open(url)
                return True, f"Opened: {url}"
            else:
                webbrowser.open("https://www.google.com")
                return True, "Browser opened"
        except Exception as e:
            return False, f"Browser error: {e}"
    
    def search_web(self, query: str) -> Tuple[bool, str]:
        """Search the web"""
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return True, f"Searching: {query}"
        except Exception as e:
            return False, f"Search error: {e}"
    
    def open_youtube(self, query: str = None) -> Tuple[bool, str]:
        """Open YouTube with optional search"""
        try:
            # If a query is provided, attempt to open the first matching video directly
            from urllib.parse import quote_plus

            if query:
                safe_q = quote_plus(query)
                search_url = f"https://www.youtube.com/results?search_query={safe_q}"

                # Try to fetch the search results and find the first video id to autoplay
                try:
                    resp = requests.get(search_url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200 and resp.text:
                        # Find the first /watch?v= occurrence
                        match = re.search(r"/watch\?v=([A-Za-z0-9_-]{6,})", resp.text)
                        if match:
                            vid = match.group(1)
                            watch_url = f"https://www.youtube.com/watch?v={vid}"
                            webbrowser.open(watch_url)
                            return True, f"Playing on YouTube: {query}"
                except Exception as e:
                    # Ignore fetch errors and fall back to opening search page
                    print(f"YouTube fetch error: {e}")

                # Fallback: open search results page
                webbrowser.open(search_url)
                return True, f"YouTube: Search for {query}"
            else:
                webbrowser.open("https://www.youtube.com")
                return True, "YouTube: Home"
        except Exception as e:
            return False, f"YouTube error: {e}"
    
    def open_application(self, app_name: str) -> Tuple[bool, str]:
        """Open an application by name"""
        app_map = {
            # Windows apps
            "notepad": ("notepad.exe", None, None),
            "calculator": ("calc.exe", None, None),
            "paint": ("mspaint.exe", None, None),
            "word": ("WINWORD.EXE", None, None),
            "excel": ("EXCEL.EXE", None, None),
            "powerpoint": ("POWERPNT.EXE", None, None),
            "explorer": ("explorer.exe", None, None),
            "cmd": ("cmd.exe", None, None),
            "terminal": ("cmd.exe", "Terminal", "gnome-terminal"),
            "chrome": ("chrome.exe", "Google Chrome", "google-chrome"),
            "firefox": ("firefox.exe", "Firefox", "firefox"),
            "edge": ("msedge.exe", None, None),
            "vscode": ("code.exe", "Visual Studio Code", "code"),
            "spotify": ("spotify.exe", "Spotify", "spotify"),
            "discord": ("discord.exe", "Discord", "discord"),
            "slack": ("slack.exe", "Slack", "slack"),
            "zoom": ("zoom.exe", "zoom.us", "zoom"),
            "teams": ("teams.exe", "Microsoft Teams", "teams"),
        }
        
        app_lower = app_name.lower()
        
        # Find best match
        matches = process.extractBests(app_lower, app_map.keys(), score_cutoff=60)
        if matches:
            best_match = matches[0][0]
            win_app, mac_app, linux_app = app_map[best_match]
            
            try:
                if self.platform == "Windows":
                    subprocess.Popen(win_app, shell=True)
                elif self.platform == "Darwin" and mac_app:
                    subprocess.run(["open", "-a", mac_app])
                elif self.platform == "Linux" and linux_app:
                    subprocess.Popen(linux_app, shell=True)
                
                return True, f"Opened {best_match}"
            except Exception as e:
                return False, f"Could not open {app_name}: {e}"
        
        # Try direct execution
        try:
            if self.platform == "Windows":
                subprocess.Popen(f"start {app_name}", shell=True)
            elif self.platform == "Darwin":
                subprocess.run(["open", "-a", app_name])
            else:
                subprocess.Popen(app_name, shell=True)
            return True, f"Opened {app_name}"
        except:
            return False, f"Application not found: {app_name}"
    
    # ---------------------- CAMERA ----------------------

    def capture_camera(self, name: str = None) -> Tuple[bool, str]:
        """Capture image from camera"""
        if not CAMERA_AVAILABLE:
            return False, "Camera not available. Install opencv-python: pip install opencv-python"

        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return False, "Could not open camera. Make sure a camera is connected."

            # Let camera warm up
            time.sleep(0.5)

            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                return False, "Failed to capture image from camera."

            # Generate filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png" if name else f"camera_{timestamp}.png"
            filepath = Config.SCREENSHOTS_DIR / filename

            Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

            # Convert BGR to RGB and save
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.save(filepath)

            self.last_screenshot_path = filepath
            return True, f"Camera capture saved: {filepath}"
        except Exception as e:
            return False, f"Camera error: {e}"

    def show_camera_preview(self) -> Tuple[bool, str]:
        """Show camera preview window"""
        if not CAMERA_AVAILABLE:
            return False, "Camera not available. Install opencv-python: pip install opencv-python"

        def preview_thread():
            try:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    return

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    cv2.imshow('Camera Preview - Press Q to close', frame)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                cap.release()
                cv2.destroyAllWindows()
            except Exception as e:
                print(f"Camera preview error: {e}")

        threading.Thread(target=preview_thread, daemon=True).start()
        return True, "Camera preview opened. Press 'Q' to close."

    # ---------------------- SYSTEM INFO ----------------------

    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Battery
            battery = None
            try:
                battery_info = psutil.sensors_battery()
                if battery_info:
                    battery = {
                        "percent": battery_info.percent,
                        "plugged": battery_info.power_plugged,
                        "time_left": battery_info.secsleft if battery_info.secsleft > 0 else None
                    }
            except:
                pass
            
            # Temperature (Linux/Mac)
            temps = None
            try:
                temps = psutil.sensors_temperatures()
            except:
                pass
            
            return {
                "cpu": cpu_percent,
                "memory": memory.percent,
                "memory_used": memory.used // (1024**3),
                "memory_total": memory.total // (1024**3),
                "disk": disk.percent,
                "disk_used": disk.used // (1024**3),
                "disk_total": disk.total // (1024**3),
                "battery": battery,
                "temps": temps,
                "platform": self.platform,
                "hostname": platform.node(),
                "uptime": time.time() - psutil.boot_time()
            }
        except Exception as e:
            print(f"System info error: {e}")
            return {}

    # ---------------------- PROCESS MANAGEMENT ----------------------

    def list_processes(self, filter_name: str = None, limit: int = 20) -> List[Dict]:
        """List running processes with optional filter"""
        try:
            processes = []
            # First pass: collect all processes
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    info = proc.info
                    if filter_name and filter_name.lower() not in info['name'].lower():
                        continue
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'cpu': 0,  # Will be updated
                        'memory': 0,  # Will be updated
                        'status': info.get('status', 'running')
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Second pass: get CPU and memory percentages (this requires accessing the process)
            for proc_dict in processes:
                try:
                    proc = psutil.Process(proc_dict['pid'])
                    proc_dict['cpu'] = proc.cpu_percent(interval=0.1) or 0
                    proc_dict['memory'] = proc.memory_percent() or 0
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process might have terminated, keep default values
                    continue

            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu'], reverse=True)
            return processes[:limit] if processes else []
        except ImportError:
            return []
        except Exception as e:
            print(f"List processes error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_process_info(self, pid_or_name: str) -> Tuple[bool, str]:
        """Get detailed info about a process"""
        try:
            proc = None
            # Try as PID first
            try:
                pid = int(pid_or_name)
                proc = psutil.Process(pid)
            except ValueError:
                # Search by name
                for p in psutil.process_iter(['pid', 'name']):
                    if pid_or_name.lower() in p.info['name'].lower():
                        proc = p
                        break

            if not proc:
                return False, f"Process not found: {pid_or_name}"

            info = proc.as_dict(attrs=['pid', 'name', 'status', 'cpu_percent', 'memory_percent',
                                       'create_time', 'num_threads', 'exe', 'cmdline'])

            create_time = datetime.datetime.fromtimestamp(info['create_time']).strftime('%Y-%m-%d %H:%M:%S')

            result = f"""Process: {info['name']} (PID: {info['pid']})
Status: {info['status']}
CPU: {info['cpu_percent']:.1f}%
Memory: {info['memory_percent']:.1f}%
Threads: {info['num_threads']}
Started: {create_time}
Path: {info['exe'] or 'N/A'}"""
            return True, result
        except psutil.NoSuchProcess:
            return False, f"Process not found: {pid_or_name}"
        except psutil.AccessDenied:
            return False, f"Access denied to process: {pid_or_name}"
        except Exception as e:
            return False, f"Error getting process info: {e}"

    def kill_process(self, pid_or_name: str, force: bool = False) -> Tuple[bool, str]:
        """Kill a process by PID or name"""
        try:
            killed = []
            # Try as PID first
            try:
                pid = int(pid_or_name)
                proc = psutil.Process(pid)
                name = proc.name()
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                killed.append(f"{name} (PID: {pid})")
            except ValueError:
                # Kill by name
                for proc in psutil.process_iter(['pid', 'name']):
                    if pid_or_name.lower() in proc.info['name'].lower():
                        try:
                            if force:
                                proc.kill()
                            else:
                                proc.terminate()
                            killed.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

            if killed:
                return True, f"Killed: {', '.join(killed)}"
            return False, f"Process not found: {pid_or_name}"
        except psutil.NoSuchProcess:
            return False, f"Process not found: {pid_or_name}"
        except psutil.AccessDenied:
            return False, f"Access denied. Try running as administrator."
        except Exception as e:
            return False, f"Kill error: {e}"

    def start_process(self, command: str, background: bool = True) -> Tuple[bool, str]:
        """Start a new process"""
        try:
            if background:
                if self.platform == "Windows":
                    proc = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    proc = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"Started process: {command} (PID: {proc.pid})"
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return True, result.stdout or "Process completed successfully."
                else:
                    return False, result.stderr or f"Process failed with code {result.returncode}"
        except subprocess.TimeoutExpired:
            return False, "Process timed out after 30 seconds."
        except Exception as e:
            return False, f"Start process error: {e}"

    def get_top_processes(self, by: str = "cpu", limit: int = 10) -> str:
        """Get top processes by CPU or memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by specified metric
            if by.lower() == "memory" or by.lower() == "ram":
                processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
                metric = "Memory"
            else:
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                metric = "CPU"

            result = [f"Top {limit} processes by {metric}:\n"]
            for i, p in enumerate(processes[:limit], 1):
                cpu = p['cpu_percent'] or 0
                mem = p['memory_percent'] or 0
                result.append(f"{i}. {p['name'][:20]:<20} CPU: {cpu:5.1f}%  RAM: {mem:5.1f}%")

            return "\n".join(result)
        except Exception as e:
            return f"Error getting top processes: {e}"

    # ---------------------- ENHANCED FILE MANAGEMENT ----------------------

    def get_file_info(self, path: str) -> Tuple[bool, str]:
        """Get detailed information about a file or folder"""
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return False, f"Not found: {path}"

            stat = p.stat()
            size = stat.st_size
            modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            created = datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')

            # Format size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024**2:
                size_str = f"{size/1024:.1f} KB"
            elif size < 1024**3:
                size_str = f"{size/1024**2:.1f} MB"
            else:
                size_str = f"{size/1024**3:.2f} GB"

            if p.is_dir():
                # Count items in directory
                items = list(p.iterdir())
                files = sum(1 for i in items if i.is_file())
                folders = sum(1 for i in items if i.is_dir())
                result = f"""Folder: {p.name}
Path: {p}
Items: {len(items)} ({files} files, {folders} folders)
Modified: {modified}
Created: {created}"""
            else:
                result = f"""File: {p.name}
Path: {p}
Size: {size_str}
Type: {p.suffix or 'No extension'}
Modified: {modified}
Created: {created}"""

            return True, result
        except PermissionError:
            return False, f"Permission denied: {path}"
        except Exception as e:
            return False, f"Error getting file info: {e}"

    def search_files(self, pattern: str, path: str = None, max_results: int = 50) -> List[Dict]:
        """Search for files matching a pattern"""
        try:
            search_path = Path(path).expanduser() if path else Path.home()
            if not search_path.exists():
                return []

            results = []
            pattern_lower = pattern.lower()

            def search_recursive(directory: Path, depth: int = 0):
                if depth > 5 or len(results) >= max_results:  # Limit depth and results
                    return
                try:
                    for item in directory.iterdir():
                        if len(results) >= max_results:
                            return
                        try:
                            if pattern_lower in item.name.lower():
                                results.append({
                                    'name': item.name,
                                    'path': str(item),
                                    'is_dir': item.is_dir(),
                                    'size': item.stat().st_size if item.is_file() else 0
                                })
                            if item.is_dir() and not item.name.startswith('.'):
                                search_recursive(item, depth + 1)
                        except (PermissionError, OSError):
                            continue
                except PermissionError:
                    pass

            search_recursive(search_path)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def zip_files(self, source: str, dest: str = None) -> Tuple[bool, str]:
        """Create a zip archive"""
        try:
            src = Path(source).expanduser().resolve()
            if not src.exists():
                return False, f"Source not found: {source}"

            if dest:
                dst = Path(dest).expanduser()
            else:
                dst = src.parent / f"{src.name}.zip"

            if not str(dst).endswith('.zip'):
                dst = Path(str(dst) + '.zip')

            import zipfile
            with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zf:
                if src.is_file():
                    zf.write(src, src.name)
                else:
                    for file in src.rglob('*'):
                        if file.is_file():
                            zf.write(file, file.relative_to(src.parent))

            size = dst.stat().st_size / 1024
            return True, f"Created: {dst} ({size:.1f} KB)"
        except Exception as e:
            return False, f"Zip error: {e}"

    def unzip_files(self, source: str, dest: str = None) -> Tuple[bool, str]:
        """Extract a zip archive"""
        try:
            src = Path(source).expanduser().resolve()
            if not src.exists():
                return False, f"Zip file not found: {source}"

            if dest:
                dst = Path(dest).expanduser()
            else:
                dst = src.parent / src.stem

            dst.mkdir(parents=True, exist_ok=True)

            import zipfile
            with zipfile.ZipFile(src, 'r') as zf:
                zf.extractall(dst)
                file_count = len(zf.namelist())

            return True, f"Extracted {file_count} files to: {dst}"
        except Exception as e:
            return False, f"Unzip error: {e}"

    def get_folder_size(self, path: str) -> Tuple[bool, str]:
        """Calculate the total size of a folder"""
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return False, f"Not found: {path}"

            if not p.is_dir():
                size = p.stat().st_size
            else:
                size = sum(f.stat().st_size for f in p.rglob('*') if f.is_file())

            # Format size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024**2:
                size_str = f"{size/1024:.1f} KB"
            elif size < 1024**3:
                size_str = f"{size/1024**2:.1f} MB"
            else:
                size_str = f"{size/1024**3:.2f} GB"

            return True, f"Size of {p.name}: {size_str}"
        except PermissionError:
            return False, f"Permission denied: {path}"
        except Exception as e:
            return False, f"Error: {e}"

    def find_large_files(self, path: str = None, min_size_mb: int = 100, limit: int = 20) -> str:
        """Find large files in a directory"""
        try:
            search_path = Path(path).expanduser() if path else Path.home()
            if not search_path.exists():
                return "Path not found."

            min_size = min_size_mb * 1024 * 1024
            large_files = []

            for f in search_path.rglob('*'):
                try:
                    if f.is_file() and f.stat().st_size >= min_size:
                        large_files.append((f, f.stat().st_size))
                except (PermissionError, OSError):
                    continue

            large_files.sort(key=lambda x: x[1], reverse=True)

            if not large_files:
                return f"No files larger than {min_size_mb}MB found."

            result = [f"Large files (>{min_size_mb}MB):\n"]
            for f, size in large_files[:limit]:
                size_str = f"{size/1024**2:.1f}MB" if size < 1024**3 else f"{size/1024**3:.2f}GB"
                result.append(f"  {size_str:>10}  {f.name[:40]}")

            return "\n".join(result)
        except Exception as e:
            return f"Error: {e}"

    def find_duplicate_files(self, path: str = None, limit: int = 20) -> str:
        """Find duplicate files by name in a directory"""
        try:
            search_path = Path(path).expanduser() if path else Path.home()
            if not search_path.exists():
                return "Path not found."

            files_by_name = {}
            for f in search_path.rglob('*'):
                try:
                    if f.is_file():
                        name = f.name.lower()
                        if name not in files_by_name:
                            files_by_name[name] = []
                        files_by_name[name].append(str(f))
                except (PermissionError, OSError):
                    continue

            duplicates = {k: v for k, v in files_by_name.items() if len(v) > 1}

            if not duplicates:
                return "No duplicate files found."

            result = ["Duplicate files found:\n"]
            count = 0
            for name, paths in sorted(duplicates.items()):
                if count >= limit:
                    result.append(f"\n...and more duplicates")
                    break
                result.append(f"\n{name}:")
                for p in paths[:3]:
                    result.append(f"  - {p}")
                count += 1

            return "\n".join(result)
        except Exception as e:
            return f"Error: {e}"

    # ---------------------- CALCULATIONS ----------------------
    
    def calculate(self, expression: str) -> Tuple[bool, str]:
        """Evaluate a mathematical expression"""
        try:
            # Clean expression
            expr = expression.lower()
            expr = expr.replace("x", "*").replace("×", "*").replace("÷", "/")
            expr = expr.replace("^", "**").replace("plus", "+").replace("minus", "-")
            expr = expr.replace("times", "*").replace("divided by", "/")
            expr = expr.replace("squared", "**2").replace("cubed", "**3")
            expr = expr.replace("square root of", "math.sqrt(")
            expr = expr.replace("sqrt", "math.sqrt(")
            expr = expr.replace("sin", "math.sin(").replace("cos", "math.cos(").replace("tan", "math.tan(")
            expr = expr.replace("log", "math.log10(").replace("ln", "math.log(")
            expr = expr.replace("pi", str(math.pi)).replace("e", str(math.e))
            
            # Add closing parentheses if needed
            open_count = expr.count("(")
            close_count = expr.count(")")
            expr += ")" * (open_count - close_count)
            
            # Remove non-math characters
            expr = re.sub(r'[^0-9+\-*/().mathsqrtlogsincotan\s]', '', expr)
            
            # Safe evaluation
            allowed_names = {"math": math}
            result = eval(expr, {"__builtins__": {}}, allowed_names)
            
            # Format result
            if isinstance(result, float):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 6)
            
            return True, f"{expression} = {result}"
        except Exception as e:
            return False, f"Calculation error: {e}"


# ============================================================================
# COMMAND PROCESSOR
# ============================================================================

class CommandProcessor:
    """Natural language command processing with fuzzy matching"""
    
    def __init__(self, system: SystemController, voice: VoiceEngine, ai: GeminiAI, app):
        self.system = system
        self.voice = voice
        self.ai = ai
        self.app = app
        self.history = DataManager.load_json(Config.HISTORY_FILE, [])
        
        # Command patterns with fuzzy matching
        self.commands = {
            # Screenshot commands
            "take screenshot": self._cmd_screenshot,
            "screenshot": self._cmd_screenshot,
            "capture screen": self._cmd_screenshot,
            "rename screenshot": self._cmd_rename_screenshot,
            "rename last screenshot": self._cmd_rename_screenshot,
            "move screenshot": self._cmd_move_screenshot,
            "move last screenshot": self._cmd_move_screenshot,
            
            # Volume commands
            "volume up to": self._cmd_set_volume,  # "volume up to 80" -> set to 80
            "volume down to": self._cmd_set_volume,  # "volume down to 20" -> set to 20
            "volume up": self._cmd_volume_up,
            "increase volume": self._cmd_volume_up,
            "turn up volume": self._cmd_volume_up,
            "louder": self._cmd_volume_up,
            "volume down": self._cmd_volume_down,
            "decrease volume": self._cmd_volume_down,
            "turn down volume": self._cmd_volume_down,
            "quieter": self._cmd_volume_down,
            "softer": self._cmd_volume_down,
            "set volume": self._cmd_set_volume,
            "volume": self._cmd_set_volume,
            "mute": self._cmd_mute,
            "unmute": lambda cmd: self._cmd_set_volume("volume 50"),
            
            # Browser commands
            "open browser": self._cmd_browser,
            "browser": self._cmd_browser,
            "open chrome": lambda cmd: self.system.open_application("chrome"),
            "open firefox": lambda cmd: self.system.open_application("firefox"),
            "search": self._cmd_search,
            "google": self._cmd_search,
            "search for": self._cmd_search,
            
            # YouTube
            "open youtube": self._cmd_youtube,
            "open you tube": self._cmd_youtube,
            "youtube": self._cmd_youtube,
            "you tube": self._cmd_youtube,
            "play youtube": self._cmd_youtube,
            "search youtube": self._cmd_youtube,
            "play on youtube": self._cmd_youtube,
            
            # File operations
            "open file": self._cmd_open_file,
            "open folder": self._cmd_open_folder,
            "open": self._cmd_open,
            "rename file": self._cmd_rename_file,
            "rename": self._cmd_rename_file,
            "move file": self._cmd_move_file,
            "move": self._cmd_move_file,
            "copy file": self._cmd_copy_file,
            "copy": self._cmd_copy_file,
            "delete file": self._cmd_delete_file,
            "delete": self._cmd_delete_file,
            "create folder": self._cmd_create_folder,
            "new folder": self._cmd_create_folder,
            "list files": self._cmd_list_files,
            
            # Camera commands
            "camera": self._cmd_camera,
            "take photo": self._cmd_camera,
            "capture camera": self._cmd_camera,
            "take picture": self._cmd_camera,
            "webcam": self._cmd_camera,
            "camera preview": self._cmd_camera_preview,
            "show camera": self._cmd_camera_preview,
            "open camera": self._cmd_camera_preview,

            # Applications
            "open notepad": lambda cmd: self.system.open_application("notepad"),
            "open calculator": lambda cmd: self.system.open_application("calculator"),
            "open paint": lambda cmd: self.system.open_application("paint"),
            "open terminal": lambda cmd: self.system.open_application("terminal"),
            "open vscode": lambda cmd: self.system.open_application("vscode"),
            "open code": lambda cmd: self.system.open_application("vscode"),
            "open spotify": lambda cmd: self.system.open_application("spotify"),
            "open discord": lambda cmd: self.system.open_application("discord"),
            "open app": self._cmd_open_app,
            "launch": self._cmd_open_app,
            
            # Calculations
            "calculate": self._cmd_calculate,
            "calc": self._cmd_calculate,
            "what is": self._cmd_calculate_or_ai,
            "how much is": self._cmd_calculate,
            
            # System
            "system info": self._cmd_system_info,
            "system status": self._cmd_system_info,
            "specs": self._cmd_system_info,

            # Process Management
            "list processes": self._cmd_list_processes,
            "show processes": self._cmd_list_processes,
            "processes": self._cmd_list_processes,
            "top processes": self._cmd_top_processes,
            "top": self._cmd_top_processes,
            "process info": self._cmd_process_info,
            "kill process": self._cmd_kill_process,
            "kill": self._cmd_kill_process,
            "end task": self._cmd_kill_process,
            "start process": self._cmd_start_process,
            "run": self._cmd_start_process,

            # Enhanced File Management
            "file info": self._cmd_file_info,
            "info": self._cmd_file_info,
            "search files": self._cmd_search_files,
            "find files": self._cmd_search_files,
            "find": self._cmd_search_files,
            "zip": self._cmd_zip,
            "compress": self._cmd_zip,
            "unzip": self._cmd_unzip,
            "extract": self._cmd_unzip,
            "folder size": self._cmd_folder_size,
            "size of": self._cmd_folder_size,
            "large files": self._cmd_large_files,
            "find large": self._cmd_large_files,
            "duplicates": self._cmd_duplicates,
            "find duplicates": self._cmd_duplicates,

            # Tasks
            "add task": self._cmd_add_task,
            "new task": self._cmd_add_task,
            "show tasks": self._cmd_show_tasks,
            "list tasks": self._cmd_show_tasks,
            
            # Reminders
            "remind me": self._cmd_add_reminder,
            "set reminder": self._cmd_add_reminder,
            "add reminder": self._cmd_add_reminder,
            "show reminders": self._cmd_show_reminders,
            
            # AI Commands
            "ask ai": self._cmd_ai_chat,
            "ai": self._cmd_ai_chat,
            "chat": self._cmd_ai_chat,
            
            # AI Vision Commands
            "analyze image": self._cmd_analyze_image,
            "describe image": self._cmd_describe_image,
            "extract text": self._cmd_extract_text,
            "ocr": self._cmd_extract_text,
            "compare images": self._cmd_compare_images,
            "vision": self._cmd_vision,
            "generate image": self._cmd_generate_image,
            "create image": self._cmd_generate_image,
            "make image": self._cmd_generate_image,
            "make the image": self._cmd_generate_image,
            "make the image of": self._cmd_generate_image,
            "make an image": self._cmd_generate_image,
            "draw": self._cmd_generate_image,
            "draw me": self._cmd_generate_image,
            "draw a": self._cmd_generate_image,
            "create image": self._cmd_generate_image,
            "create logo": self._cmd_create_logo,
            
            # Time
            "time": self._cmd_time,
            "what time": self._cmd_time,
            "date": self._cmd_date,
            "what date": self._cmd_date,
            
            # Help
            "help": self._cmd_help,
            "commands": self._cmd_help,
            
            # Exit
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
            "close": self._cmd_exit,
            "goodbye": self._cmd_exit,
        }
    
    def process(self, command: str) -> str:
        """Process a command and return response"""
        if not command:
            return "No command received."
        
        command = command.strip()
        cmd_lower = command.lower()
        
        # Log command being processed
        logger.debug(f"Processing: '{command}'")
        
        # Check if it's a standalone number (likely a volume level)
        if cmd_lower.isdigit():
            volume_level = int(cmd_lower)
            if 0 <= volume_level <= 100:
                # Treat as volume command
                return self._cmd_set_volume(f"volume {volume_level}")
        
        # Add to history
        self.history.append({
            "command": command,
            "timestamp": datetime.datetime.now().isoformat()
        })
        if len(self.history) > 100:
            self.history = self.history[-100:]
        DataManager.save_json(Config.HISTORY_FILE, self.history)
        
        # Find best matching command
        best_match = None
        best_score = 0
        
        for pattern, handler in self.commands.items():
            # Check direct start
            if cmd_lower.startswith(pattern):
                score = len(pattern) * 10
                if score > best_score:
                    best_score = score
                    best_match = (pattern, handler)
            
            # Fuzzy match
            # Avoid matching patterns that include 'to' (e.g., 'volume up to') when
            # the user didn't provide a numeric level — prefer incremental commands.
            if 'to' in pattern and not re.search(r'\d+', cmd_lower):
                continue

            score = fuzz.partial_ratio(pattern, cmd_lower)
            if score > 70 and score > best_score:
                best_score = score
                best_match = (pattern, handler)
        
        if best_match and best_score > 60:
            pattern, handler = best_match
            logger.debug(f"Matched pattern: '{pattern}' (score: {best_score})")
            try:
                result = handler(command)
                logger.debug(f"Handler returned: {result}")
                if isinstance(result, tuple):
                    success, message = result
                    return message
                return result if result else "Done."
            except Exception as e:
                logger.error(f"Handler error: {e}")
                return f"Error: {e}"
        
        # Default to AI chat if no command matched
        logger.debug(f"No match found, using AI chat")
        return self._cmd_ai_chat(command)
    
    # Command implementations
    
    def _cmd_screenshot(self, cmd: str) -> Tuple[bool, str]:
        name = None
        parts = cmd.lower().split()
        for i, word in enumerate(parts):
            if word in ("as", "named", "called") and i + 1 < len(parts):
                name = "_".join(parts[i+1:])
                break
        return self.system.take_screenshot(name)
    
    def _cmd_rename_screenshot(self, cmd: str) -> Tuple[bool, str]:
        # Extract new name from command
        patterns = ["rename screenshot to", "rename last screenshot to", "rename screenshot", "rename to"]
        new_name = cmd
        for pattern in patterns:
            if pattern in cmd.lower():
                new_name = cmd.lower().split(pattern)[-1].strip()
                break
        return self.system.rename_last_screenshot(new_name)
    
    def _cmd_move_screenshot(self, cmd: str) -> Tuple[bool, str]:
        patterns = ["move screenshot to", "move last screenshot to", "move to"]
        dest = cmd
        for pattern in patterns:
            if pattern in cmd.lower():
                dest = cmd.lower().split(pattern)[-1].strip()
                break
        dest = dest.replace("~", str(Path.home()))
        return self.system.move_last_screenshot(dest)
    
    def _cmd_volume_up(self, cmd: str) -> Tuple[bool, str]:
        # Check if it's "volume up to X" pattern (should set exact volume)
        if "to" in cmd.lower():
            return self._cmd_set_volume(cmd)
        amount = 10
        nums = re.findall(r'\d+', cmd)
        if nums:
            amount = int(nums[0])
        return self.system.volume_up(amount)
    
    def _cmd_volume_down(self, cmd: str) -> Tuple[bool, str]:
        # Check if it's "volume down to X" pattern (should set exact volume)
        if "to" in cmd.lower():
            return self._cmd_set_volume(cmd)
        amount = 10
        nums = re.findall(r'\d+', cmd)
        if nums:
            amount = int(nums[0])
        return self.system.volume_down(amount)
    
    def _cmd_set_volume(self, cmd: str) -> Tuple[bool, str]:
        nums = re.findall(r'\d+', cmd)
        if nums:
            return self.system.set_volume(int(nums[0]))
        return False, "Please specify volume level (0-100)"
    
    def _cmd_mute(self, cmd: str) -> Tuple[bool, str]:
        return self.system.mute()
    
    def _cmd_browser(self, cmd: str) -> Tuple[bool, str]:
        url = None
        if "open browser" in cmd.lower():
            parts = cmd.lower().split("open browser")[-1].strip()
            if parts:
                url = parts
        return self.system.open_browser(url)
    
    def _cmd_search(self, cmd: str) -> Tuple[bool, str]:
        patterns = ["search for", "search", "google"]
        query = cmd
        for pattern in patterns:
            if pattern in cmd.lower():
                query = cmd.lower().split(pattern)[-1].strip()
                break
        if query:
            return self.system.search_web(query)
        return False, "What would you like to search for?"
    
    def _cmd_youtube(self, cmd: str) -> Tuple[bool, str]:
        # Try to extract intent and query from many natural forms, e.g.:
        # "play Halka Halka in YouTube", "play Halka Halka on YouTube", "youtube Halka Halka",
        # "search YouTube for Halka Halka", "play on youtube Halka Halka", "open youtube"
        # "cartoon on youtube", "cartoon in youtube"
        text = cmd.strip()
        lower = cmd.lower()

        # Pattern: open youtube (just open YouTube homepage)
        if re.match(r'^(open\s+)?(you\s*)?tube$', lower) or lower in ["open youtube", "open you tube", "youtube", "you tube"]:
            return self.system.open_youtube(None)

        # Pattern: <query> on/in youtube (e.g., "cartoon on youtube", "music in youtube")
        m = re.search(r'^(.+?)\s+(?:on|in)\s+(?:you\s*)?tube$', lower, re.IGNORECASE)
        if m:
            query = m.group(1).strip()
            # Don't match if query is just "play" or "open"
            if query and query not in ["play", "open", "search"]:
                return self.system.open_youtube(query)

        # Pattern: play <query> in/on youtube
        m = re.search(r'play\s+(.+?)\s+(?:in|on)\s+(?:you\s*)?tube', lower, re.IGNORECASE)
        if m:
            query = m.group(1).strip()
            return self.system.open_youtube(query)

        # Pattern: search youtube for <query>
        m = re.search(r'(?:search\s+(?:you\s*)?tube\s+for|search\s+for)\s+(.+)', lower, re.IGNORECASE)
        if m:
            query = m.group(1).strip()
            return self.system.open_youtube(query)

        # Pattern: play <query> youtube OR <query> youtube
        m = re.search(r'play\s+(.+?)\s+(?:you\s*)?tube', lower, re.IGNORECASE)
        if m:
            query = m.group(1).strip()
            return self.system.open_youtube(query)

        # Pattern: youtube play <query>
        m = re.search(r'(?:you\s*)?tube\s+play\s+(.+)', lower, re.IGNORECASE)
        if m:
            query = m.group(1).strip()
            return self.system.open_youtube(query)

        # Pattern: youtube <query> or open youtube <query>
        m = re.search(r'(?:open\s+)?(?:you\s*)?tube\s+(.+)', lower, re.IGNORECASE)
        if m:
            query = m.group(1).strip()
            return self.system.open_youtube(query)

        # If no specific query, just open YouTube home or search if trailing text
        # Try to capture anything after 'youtube' or 'open youtube'
        for pattern in ["search youtube for", "search youtube", "open youtube", "youtube"]:
            if pattern in lower:
                remaining = lower.split(pattern)[-1].strip()
                if remaining:
                    return self.system.open_youtube(remaining)
                break

        return self.system.open_youtube(None)

    def _cmd_camera(self, cmd: str) -> Tuple[bool, str]:
        """Capture image from camera"""
        name = None
        parts = cmd.lower().split()
        for i, word in enumerate(parts):
            if word in ("as", "named", "called") and i + 1 < len(parts):
                name = "_".join(parts[i+1:])
                break
        return self.system.capture_camera(name)

    def _cmd_camera_preview(self, cmd: str) -> Tuple[bool, str]:
        """Show camera preview"""
        return self.system.show_camera_preview()

    def _cmd_open_file(self, cmd: str) -> Tuple[bool, str]:
        path = cmd.lower().replace("open file", "").replace("open", "").strip()
        return self.system.open_file(path)
    
    def _cmd_open_folder(self, cmd: str) -> Tuple[bool, str]:
        path = cmd.lower().replace("open folder", "").replace("open", "").strip()
        if not path:
            path = str(Path.home())
        return self.system.open_folder(path)
    
    def _cmd_open(self, cmd: str) -> Tuple[bool, str]:
        target = cmd.lower().replace("open", "").strip()
        
        # Check if it's a path
        test_path = Path(target).expanduser()
        if test_path.exists():
            return self.system.open_file(str(test_path))
        
        # Check common locations
        for loc in [Path.home() / target, Path.home() / "Desktop" / target, 
                   Path.home() / "Documents" / target, Path.home() / "Downloads" / target]:
            if loc.exists():
                return self.system.open_file(str(loc))
        
        # Try as application
        return self.system.open_application(target)
    
    def _cmd_rename_file(self, cmd: str) -> Tuple[bool, str]:
        # Pattern: rename [file] to [new name]
        match = re.search(r'rename\s+(.+?)\s+to\s+(.+)', cmd, re.IGNORECASE)
        if match:
            old_path = match.group(1).strip()
            new_name = match.group(2).strip()
            return self.system.rename_file(old_path, new_name)
        return False, "Usage: rename [filepath] to [new name]"
    
    def _cmd_move_file(self, cmd: str) -> Tuple[bool, str]:
        match = re.search(r'move\s+(.+?)\s+to\s+(.+)', cmd, re.IGNORECASE)
        if match:
            source = match.group(1).strip()
            dest = match.group(2).strip()
            return self.system.move_file(source, dest)
        return False, "Usage: move [source] to [destination]"
    
    def _cmd_copy_file(self, cmd: str) -> Tuple[bool, str]:
        match = re.search(r'copy\s+(.+?)\s+to\s+(.+)', cmd, re.IGNORECASE)
        if match:
            source = match.group(1).strip()
            dest = match.group(2).strip()
            return self.system.copy_file(source, dest)
        return False, "Usage: copy [source] to [destination]"
    
    def _cmd_delete_file(self, cmd: str) -> Tuple[bool, str]:
        path = cmd.lower().replace("delete file", "").replace("delete", "").strip()
        if path:
            return self.system.delete_file(path)
        return False, "Usage: delete [filepath]"
    
    def _cmd_create_folder(self, cmd: str) -> Tuple[bool, str]:
        path = cmd.lower().replace("create folder", "").replace("new folder", "").strip()
        if path:
            return self.system.create_folder(path)
        return False, "Usage: create folder [path]"
    
    def _cmd_list_files(self, cmd: str) -> str:
        path = cmd.lower().replace("list files", "").replace("in", "").strip()
        files = self.system.list_files(path if path else None)
        if not files:
            return "No files found."
        
        result = []
        for f in files[:20]:
            icon = "📁" if f["is_dir"] else "📄"
            result.append(f"{icon} {f['name']}")
        
        return "\n".join(result)
    
    def _cmd_open_app(self, cmd: str) -> Tuple[bool, str]:
        app = cmd.lower().replace("open app", "").replace("open", "").replace("launch", "").strip()
        return self.system.open_application(app)
    
    def _cmd_calculate(self, cmd: str) -> Tuple[bool, str]:
        expr = cmd.lower()
        for word in ["calculate", "calc", "what is", "how much is", "compute"]:
            expr = expr.replace(word, "")
        return self.system.calculate(expr.strip())
    
    def _cmd_calculate_or_ai(self, cmd: str) -> str:
        # Try calculation first
        success, result = self._cmd_calculate(cmd)
        if success and "error" not in result.lower():
            return result
        # Fall back to AI
        return self._cmd_ai_chat(cmd)
    
    def _cmd_system_info(self, cmd: str) -> str:
        info = self.system.get_system_info()
        lines = [
            f"💻 System: {info.get('platform', 'Unknown')} ({info.get('hostname', '')})",
            f"🔲 CPU: {info.get('cpu', 0):.1f}%",
            f"🧠 Memory: {info.get('memory', 0):.1f}% ({info.get('memory_used', 0)}GB / {info.get('memory_total', 0)}GB)",
            f"💾 Disk: {info.get('disk', 0):.1f}% ({info.get('disk_used', 0)}GB / {info.get('disk_total', 0)}GB)",
        ]
        
        if info.get("battery"):
            bat = info["battery"]
            plug = "🔌" if bat["plugged"] else "🔋"
            lines.append(f"{plug} Battery: {bat['percent']}%")
        
        uptime = info.get("uptime", 0)
        hours, rem = divmod(int(uptime), 3600)
        mins = rem // 60
        lines.append(f"⏱️ Uptime: {hours}h {mins}m")
        
        return "\n".join(lines)

    # ---- Process Management Commands ----

    def _cmd_list_processes(self, cmd: str) -> str:
        """List running processes"""
        filter_name = None
        for pattern in ["list processes", "show processes", "processes"]:
            if pattern in cmd.lower():
                filter_name = cmd.lower().replace(pattern, "").strip()
                break

        processes = self.system.list_processes(filter_name if filter_name else None)
        if not processes:
            return "No processes found."

        result = ["Running Processes:\n"]
        for p in processes[:15]:
            result.append(f"  {p['pid']:>6}  {p['name'][:25]:<25} CPU: {p['cpu']:5.1f}%  RAM: {p['memory']:5.1f}%")
        return "\n".join(result)

    def _cmd_top_processes(self, cmd: str) -> str:
        """Show top processes by CPU or memory"""
        by = "cpu"
        if "memory" in cmd.lower() or "ram" in cmd.lower():
            by = "memory"
        return self.system.get_top_processes(by=by)

    def _cmd_process_info(self, cmd: str) -> Tuple[bool, str]:
        """Get info about a specific process"""
        pid_or_name = cmd.lower().replace("process info", "").replace("info", "").strip()
        if not pid_or_name:
            return False, "Usage: process info [pid or name]"
        return self.system.get_process_info(pid_or_name)

    def _cmd_kill_process(self, cmd: str) -> Tuple[bool, str]:
        """Kill a process"""
        force = "force" in cmd.lower()
        pid_or_name = cmd.lower()
        for pattern in ["kill process", "kill", "end task", "force"]:
            pid_or_name = pid_or_name.replace(pattern, "")
        pid_or_name = pid_or_name.strip()

        if not pid_or_name:
            return False, "Usage: kill [pid or process name]"
        return self.system.kill_process(pid_or_name, force=force)

    def _cmd_start_process(self, cmd: str) -> Tuple[bool, str]:
        """Start a new process"""
        command = cmd.lower()
        for pattern in ["start process", "run"]:
            command = command.replace(pattern, "")
        command = command.strip()

        if not command:
            return False, "Usage: run [command]"
        return self.system.start_process(command)

    # ---- Enhanced File Management Commands ----

    def _cmd_file_info(self, cmd: str) -> Tuple[bool, str]:
        """Get file/folder information"""
        path = cmd.lower()
        for pattern in ["file info", "info"]:
            path = path.replace(pattern, "")
        path = path.strip()

        if not path:
            return False, "Usage: info [file or folder path]"
        return self.system.get_file_info(path)

    def _cmd_search_files(self, cmd: str) -> str:
        """Search for files"""
        pattern = cmd.lower()
        for p in ["search files", "find files", "find"]:
            pattern = pattern.replace(p, "")
        pattern = pattern.strip()

        if not pattern:
            return "Usage: find [filename pattern]"

        results = self.system.search_files(pattern)
        if not results:
            return f"No files found matching '{pattern}'"

        output = [f"Found {len(results)} files:\n"]
        for f in results[:20]:
            icon = "📁" if f['is_dir'] else "📄"
            output.append(f"  {icon} {f['name']}")
        if len(results) > 20:
            output.append(f"\n  ...and {len(results) - 20} more")
        return "\n".join(output)

    def _cmd_zip(self, cmd: str) -> Tuple[bool, str]:
        """Create zip archive"""
        match = re.search(r'(?:zip|compress)\s+(.+?)(?:\s+to\s+(.+))?$', cmd, re.IGNORECASE)
        if match:
            source = match.group(1).strip()
            dest = match.group(2).strip() if match.group(2) else None
            return self.system.zip_files(source, dest)
        return False, "Usage: zip [source] to [destination.zip]"

    def _cmd_unzip(self, cmd: str) -> Tuple[bool, str]:
        """Extract zip archive"""
        match = re.search(r'(?:unzip|extract)\s+(.+?)(?:\s+to\s+(.+))?$', cmd, re.IGNORECASE)
        if match:
            source = match.group(1).strip()
            dest = match.group(2).strip() if match.group(2) else None
            return self.system.unzip_files(source, dest)
        return False, "Usage: unzip [archive.zip] to [destination]"

    def _cmd_folder_size(self, cmd: str) -> Tuple[bool, str]:
        """Get folder size"""
        path = cmd.lower()
        for pattern in ["folder size", "size of"]:
            path = path.replace(pattern, "")
        path = path.strip()

        if not path:
            return False, "Usage: size of [folder path]"
        return self.system.get_folder_size(path)

    def _cmd_large_files(self, cmd: str) -> str:
        """Find large files"""
        path = None
        min_size = 100

        # Extract size if specified
        size_match = re.search(r'(\d+)\s*(?:mb|MB)', cmd)
        if size_match:
            min_size = int(size_match.group(1))

        # Extract path
        cleaned = cmd.lower()
        for pattern in ["large files", "find large", "in"]:
            cleaned = cleaned.replace(pattern, "")
        cleaned = re.sub(r'\d+\s*(?:mb|MB)', '', cleaned).strip()
        if cleaned:
            path = cleaned

        return self.system.find_large_files(path, min_size)

    def _cmd_duplicates(self, cmd: str) -> str:
        """Find duplicate files"""
        path = cmd.lower()
        for pattern in ["find duplicates", "duplicates", "in"]:
            path = path.replace(pattern, "")
        path = path.strip() or None
        return self.system.find_duplicate_files(path)

    def _cmd_add_task(self, cmd: str) -> str:
        task = cmd.lower().replace("add task", "").replace("new task", "").strip()
        if task:
            self.app.add_task(task)
            return f"Task added: {task}"
        return "What task would you like to add?"
    
    def _cmd_show_tasks(self, cmd: str) -> str:
        tasks = self.app.get_tasks()
        if not tasks:
            return "No tasks."
        return "\n".join([f"{'✅' if t.get('done') else '⬜'} {t['text']}" for t in tasks[:10]])
    
    def _cmd_add_reminder(self, cmd: str) -> str:
        text = cmd.lower().replace("remind me to", "").replace("remind me", "").replace("set reminder", "").replace("add reminder", "").strip()
        if text:
            self.app.add_reminder(text)
            return f"Reminder set: {text}"
        return "What should I remind you about?"
    
    def _cmd_show_reminders(self, cmd: str) -> str:
        reminders = self.app.get_reminders()
        if not reminders:
            return "No reminders."
        return "\n".join([f"🔔 {r['text']}" for r in reminders[:10]])
    
    def _cmd_ai_chat(self, cmd: str) -> str:
        query = cmd.lower()
        for word in ["ask ai", "ai", "chat"]:
            query = query.replace(word, "", 1)
        query = query.strip() or cmd
        return self.ai.chat(query)
    
    def _cmd_analyze_image(self, cmd: str) -> str:
        path = cmd.lower().replace("analyze image", "").strip()
        if not path:
            # Use last screenshot
            if self.system.last_screenshot_path and self.system.last_screenshot_path.exists():
                path = str(self.system.last_screenshot_path)
            else:
                return "Please specify an image path or take a screenshot first."
        return self.ai.analyze_image(path)
    
    def _cmd_describe_image(self, cmd: str) -> str:
        path = cmd.lower().replace("describe image", "").strip()
        if not path and self.system.last_screenshot_path:
            path = str(self.system.last_screenshot_path)
        return self.ai.analyze_image(path, "Describe this image in detail, including all visible elements, colors, and composition.")
    
    def _cmd_extract_text(self, cmd: str) -> str:
        path = cmd.lower().replace("extract text from", "").replace("extract text", "").replace("ocr", "").strip()
        if not path and self.system.last_screenshot_path:
            path = str(self.system.last_screenshot_path)
        return self.ai.extract_text(path)
    
    def _cmd_compare_images(self, cmd: str) -> str:
        match = re.search(r'compare.*?([^\s]+)\s+(?:and|with|to)\s+([^\s]+)', cmd, re.IGNORECASE)
        if match:
            return self.ai.compare_images(match.group(1), match.group(2))
        return "Usage: compare images [path1] and [path2]"
    
    def _cmd_vision(self, cmd: str) -> str:
        match = re.search(r'vision\s+([^\s]+)\s+(.+)', cmd, re.IGNORECASE)
        if match:
            return self.ai.analyze_image(match.group(1), match.group(2))
        return "Usage: vision [image_path] [question]"
    
    def _cmd_generate_image(self, cmd: str) -> str:
        # Normalize and attempt to extract a usable description from many natural forms
        lower = cmd.lower()
        remove_patterns = [
            "generate image",
            "create image",
            "make the image of",
            "make the image",
            "make image",
            "make an image",
            "draw me",
            "draw a",
            "draw",
            "create an image",
        ]

        for p in remove_patterns:
            if p in lower:
                lower = lower.replace(p, " ")
        desc = lower.strip()

        # If still empty, try to capture 'of X' constructs
        if not desc:
            m = re.search(r'of\s+(.+)', cmd, re.IGNORECASE)
            if m:
                desc = m.group(1).strip()

        # As a last resort, use last up-to-3 words (often the object)
        if not desc:
            words = cmd.strip().split()
            desc = ' '.join(words[-3:]) if len(words) > 0 else ''

        if not desc:
            return "Please describe the image you want to generate."

        # Skip AI call if API key is not available (avoid slow rate-limit waits)
        # Only try AI if both available flag is true AND key is actually configured
        if getattr(self.ai, 'available', False) and getattr(self.ai, 'api_key', None):
            try:
                enhanced = self.ai.generate_image_description(desc)
                # If the AI returned an error string, fall through to local fallback
                if isinstance(enhanced, str) and enhanced.lower().startswith("error"):
                    raise Exception(enhanced)
                return f"Enhanced prompt for image generation:\n\n{enhanced}\n\nNote: To generate images, use a service like DALL-E, Midjourney, or Stable Diffusion with this prompt."
            except Exception as e:
                # Log and fall back to a simple local image generator
                print(f"AI image generation unavailable or failed: {e}")
        else:
            print(f"Skipping AI (no valid API key); using local image generation for: {desc}")

        # Local fallback: generate a simple illustrative image using PIL
        try:
            Config.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # sanitize desc for filename
            safe = re.sub(r'[^a-z0-9_-]', '_', desc.lower())[:40]
            filename = f"{safe}_{timestamp}.png" if safe else f"image_{timestamp}.png"
            filepath = Config.GENERATED_DIR / filename

            # Create a 512x512 image with a simple illustration
            img = Image.new('RGB', (512, 512), color=(240, 240, 255))
            draw = ImageDraw.Draw(img)

            # Simple background shape based on hash of description
            hue = abs(hash(desc)) % 360
            # Convert hue to RGB-ish color (approx)
            bg_color = (200 + (hue % 55), 180 + ((hue//2) % 55), 160 + ((hue//3) % 95))
            draw.rectangle([0, 0, 512, 512], fill=bg_color)

            desc_lower = desc.lower()

            # Draw different shapes based on keywords
            if 'cat' in desc_lower:
                # Stylized cat
                draw.ellipse((140, 220, 372, 420), fill=(200, 180, 160), outline=(50, 30, 30))
                draw.ellipse((160, 120, 352, 312), fill=(220, 200, 180), outline=(50, 30, 30))
                draw.polygon([(180, 140), (210, 80), (240, 140)], fill=(220,200,180), outline=(50,30,30))
                draw.polygon([(312, 140), (342, 80), (372, 140)], fill=(220,200,180), outline=(50,30,30))
                draw.ellipse((220, 190, 250, 220), fill=(30, 80, 30))
                draw.ellipse((282, 190, 312, 220), fill=(30, 80, 30))
                draw.ellipse((234, 202, 242, 212), fill=(0,0,0))
                draw.ellipse((296, 202, 304, 212), fill=(0,0,0))
                draw.polygon([(272, 230), (260, 250), (284, 250)], fill=(255,150,150), outline=(50,30,30))
                draw.line((200, 240, 140, 230), fill=(30,30,30), width=2)
                draw.line((200, 250, 140, 250), fill=(30,30,30), width=2)
                draw.line((200, 260, 140, 270), fill=(30,30,30), width=2)
                draw.line((324, 240, 384, 230), fill=(30,30,30), width=2)
                draw.line((324, 250, 384, 250), fill=(30,30,30), width=2)
                draw.line((324, 260, 384, 270), fill=(30,30,30), width=2)
                draw.line((380, 320, 460, 260), fill=(200,180,160), width=18)
            elif 'dog' in desc_lower:
                # Stylized dog
                draw.ellipse((140, 240, 372, 400), fill=(180, 140, 100), outline=(50, 30, 30))  # Body
                draw.ellipse((150, 100, 340, 270), fill=(200, 160, 120), outline=(50, 30, 30))  # Head
                draw.polygon([(170, 120), (185, 50), (205, 120)], fill=(200,160,120), outline=(50,30,30))  # Left ear
                draw.polygon([(310, 120), (325, 50), (345, 120)], fill=(200,160,120), outline=(50,30,30))  # Right ear
                draw.ellipse((210, 150, 240, 180), fill=(40, 40, 40))  # Left eye
                draw.ellipse((280, 150, 310, 180), fill=(40, 40, 40))  # Right eye
                draw.ellipse((250, 200, 270, 225), fill=(100, 60, 30))  # Nose
                draw.line((150, 380, 120, 450), fill=(180,140,100), width=12)  # Leg 1
                draw.line((220, 390, 200, 460), fill=(180,140,100), width=12)  # Leg 2
                draw.line((300, 390, 320, 460), fill=(180,140,100), width=12)  # Leg 3
                draw.line((370, 380, 400, 450), fill=(180,140,100), width=12)  # Leg 4
                draw.line((370, 240, 440, 180), fill=(180,140,100), width=14)  # Tail
            elif 'bird' in desc_lower or 'eagle' in desc_lower or 'parrot' in desc_lower:
                # Stylized bird
                draw.ellipse((180, 220, 280, 320), fill=(200, 100, 50), outline=(50, 30, 30))  # Body
                draw.ellipse((220, 140, 310, 230), fill=(220, 120, 70), outline=(50, 30, 30))  # Head
                draw.ellipse((240, 170, 260, 195), fill=(0, 0, 0))  # Eye
                draw.polygon([(310, 190), (360, 160), (330, 210)], fill=(255, 150, 0))  # Beak
                draw.line((150, 260, 50, 280), fill=(50,30,30), width=3)  # Left wing
                draw.line((310, 260, 410, 280), fill=(50,30,30), width=3)  # Right wing
                draw.polygon([(250, 320), (240, 380), (260, 380)], fill=(50,30,30))  # Tail
                draw.line((200, 330, 180, 400), fill=(200,100,50), width=6)  # Leg 1
                draw.line((280, 330, 300, 400), fill=(200,100,50), width=6)  # Leg 2
            elif 'flower' in desc_lower or 'rose' in desc_lower or 'sunflower' in desc_lower:
                # Stylized flower
                draw.ellipse((200, 280, 300, 380), fill=(100, 180, 50))  # Stem base
                draw.line((250, 280, 250, 100), fill=(34, 139, 34), width=6)  # Stem
                draw.ellipse((240, 110, 260, 140), fill=(34, 139, 34))  # Leaf 1
                draw.ellipse((280, 160, 300, 190), fill=(34, 139, 34))  # Leaf 2
                # Petals
                for i in range(8):
                    angle = i * (2 * math.pi / 8)
                    px = 256 + 80 * math.cos(angle)
                    py = 180 + 80 * math.sin(angle)
                    draw.ellipse((px-25, py-35, px+25, py+35), fill=(255, 100, 150), outline=(200, 50, 100))
                # Center
                draw.ellipse((230, 160, 282, 212), fill=(255, 200, 0), outline=(200, 150, 0))
            else:
                # Generic: draw a simple icon/text indicating the description
                draw.ellipse((156, 106, 356, 306), fill=(255,255,255))
                draw.text((180, 260), desc[:24], fill=(30,30,30))

            img.save(filepath)
            return f"Generated placeholder image: {filepath}"
        except Exception as e:
            return f"Failed to create placeholder image: {e}"
    
    def _cmd_create_logo(self, cmd: str) -> str:
        desc = cmd.lower().replace("create logo", "").strip()
        if desc:
            prompt = f"Create a detailed logo design prompt for: {desc}. Include style, colors, typography, and design elements."
            return self.ai.chat(prompt)
        return "Please describe the logo you want to create."
    
    def _cmd_time(self, cmd: str) -> str:
        now = datetime.datetime.now()
        return f"Current time: {now.strftime('%I:%M:%S %p')}"
    
    def _cmd_date(self, cmd: str) -> str:
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}"
    
    def _cmd_help(self, cmd: str) -> str:
        return """ORION OS NAVIGATOR v3.0 - COMMANDS

SYSTEM:
• screenshot, take screenshot
• rename screenshot to [name]
• move screenshot to [path]
• volume up/down, volume [0-100], mute
• system info, specs

CAMERA:
• camera, take photo, take picture
• camera preview, open camera

PROCESS MANAGEMENT:
• processes, list processes [filter]
• top, top processes [cpu/memory]
• process info [pid or name]
• kill [pid or name], end task
• run [command]

FILES:
• open [file/folder/app]
• rename [path] to [new name]
• move [source] to [destination]
• copy [source] to [destination]
• delete [path]
• create folder [path]
• list files [path]

FILE TOOLS:
• info [path] - file/folder details
• find [pattern] - search files
• zip [source] to [dest]
• unzip [archive] to [dest]
• size of [folder]
• large files [path] [size MB]
• duplicates [path]

BROWSER:
• open browser [url]
• search [query], google [query]
• youtube [search]

AI (Requires GEMINI_API_KEY):
• ask ai [question]
• analyze image [path]
• describe image [path]
• extract text [image]
• compare images [path1] and [path2]
• vision [image] [question]
• generate image [description]
• create logo [description]

PRODUCTIVITY:
• add task [description]
• show tasks
• remind me [text]
• show reminders
• calculate [expression]
• time, date

Type naturally - Orion understands variations!"""
    
    def _cmd_exit(self, cmd: str) -> str:
        self.voice.speak("Goodbye! Shutting down Orion OS.")
        self.app.root.after(1500, self.app.root.destroy)
        return "Shutting down..."


# ============================================================================
# MAIN APPLICATION UI
# ============================================================================

class OrionApp:
    """Main application with futuristic UI"""
    
    def __init__(self):
        # Initialize configuration
        Config.init_directories()
        
        # Initialize core systems
        self.voice = VoiceEngine()
        self.ai = GeminiAI()
        self.system = SystemController()
        
        # Data
        self.tasks = DataManager.load_json(Config.TASKS_FILE, [])
        self.reminders = DataManager.load_json(Config.REMINDERS_FILE, [])
        self.notes = DataManager.load_json(Config.NOTES_FILE, [])
        
        # UI
        self.setup_ui()
        
        # Command processor (needs app reference)
        self.processor = CommandProcessor(self.system, self.voice, self.ai, self)
        
        # State
        self.is_listening = False
        self.current_panel = "console"
        
        # Start system monitoring
        self.update_system_metrics()
        self.update_clock()
        
        # Greeting
        self.root.after(500, self.greet)
    
    def setup_ui(self):
        """Setup the main UI with improved organization"""
        # Window setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.root = ctk.CTk()
        self.root.title(f"{Config.APP_NAME} v{Config.VERSION}")
        self.root.geometry("1600x900")
        self.root.minsize(1400, 800)
        
        colors = Config.COLORS
        self.root.configure(fg_color=colors["bg_dark"])
        
        # Main container
        self.main_container = ctk.CTkFrame(self.root, fg_color=colors["bg_dark"])
        self.main_container.pack(fill="both", expand=True)
        
        # Create top status bar with improved layout
        self.create_status_bar()
        
        # Create main content area with 3-column layout
        # Left: Navigation, Right: Metrics, Center: Content
        content_layout = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_layout.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        
        # Left sidebar - Navigation (220px)
        self.create_sidebar(content_layout)
        
        # Center area - Main content (expandable)
        center = ctk.CTkFrame(content_layout, fg_color="transparent")
        center.pack(side="left", fill="both", expand=True, padx=(8, 8))
        
        # Create organized center layout
        self.create_main_content(center)
        
        # Right panel - Metrics and Actions (300px)
        self.create_right_panel(content_layout)
    
    def create_status_bar(self):
        """Create top status bar"""
        colors = Config.COLORS
        
        status_bar = ctk.CTkFrame(self.main_container, fg_color=colors["bg_card"], height=40, corner_radius=0)
        status_bar.pack(fill="x", padx=0, pady=0)
        status_bar.pack_propagate(False)
        
        # Left section - Logo and status
        left_frame = ctk.CTkFrame(status_bar, fg_color="transparent")
        left_frame.pack(side="left", padx=15)
        
        # Status indicators
        self.net_indicator = ctk.CTkLabel(left_frame, text="● Online", 
                                          text_color=colors["accent_green"], font=("JetBrains Mono", 11))
        self.net_indicator.pack(side="left", padx=(0, 15))
        
        self.cpu_label = ctk.CTkLabel(left_frame, text="CPU 0%", 
                                      text_color=colors["accent_cyan"], font=("JetBrains Mono", 11))
        self.cpu_label.pack(side="left", padx=5)
        
        self.ram_label = ctk.CTkLabel(left_frame, text="RAM 0%", 
                                      text_color=colors["accent_purple"], font=("JetBrains Mono", 11))
        self.ram_label.pack(side="left", padx=5)
        
        self.disk_label = ctk.CTkLabel(left_frame, text="SSD 0%", 
                                       text_color=colors["accent_orange"], font=("JetBrains Mono", 11))
        self.disk_label.pack(side="left", padx=5)
        
        # Right section - Time and mic status
        right_frame = ctk.CTkFrame(status_bar, fg_color="transparent")
        right_frame.pack(side="right", padx=15)
        
        self.mic_status = ctk.CTkLabel(right_frame, text="● Mic Off", 
                                       text_color=colors["text_muted"], font=("JetBrains Mono", 11))
        self.mic_status.pack(side="left", padx=15)
        
        self.time_label = ctk.CTkLabel(right_frame, text="00:00:00", 
                                       text_color=colors["accent_cyan"], font=("JetBrains Mono", 14, "bold"))
        self.time_label.pack(side="left", padx=5)
        
        self.orion_status = ctk.CTkLabel(right_frame, text="● Orion Online", 
                                         text_color=colors["accent_green"], font=("JetBrains Mono", 11))
        self.orion_status.pack(side="left", padx=(15, 0))
    
    def create_sidebar(self, parent):
        """Create left sidebar with navigation"""
        colors = Config.COLORS
        
        sidebar = ctk.CTkFrame(parent, fg_color=colors["bg_card"], width=220, corner_radius=12)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)
        
        # Logo section
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(logo_frame, text="◈ ORION OS NAVIGATOR", 
                    text_color=colors["accent_cyan"], font=("JetBrains Mono", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text=f"Advanced AI Command Center v{Config.VERSION}", 
                    text_color=colors["text_muted"], font=("JetBrains Mono", 9)).pack(anchor="w")
        
        # Separator
        ctk.CTkFrame(sidebar, fg_color=colors["border"], height=1).pack(fill="x", padx=15, pady=10)
        
        # Navigation label
        ctk.CTkLabel(sidebar, text="NAVIGATION", text_color=colors["text_muted"], 
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=15, pady=(5, 10))
        
        # Navigation buttons
        nav_items = [
            ("Command Console", "console", "K"),
            ("AI Assistant", "ai", "A"),
            ("Tasks", "tasks", "T"),
            ("Reminders", "reminders", "R"),
            ("File Explorer", "files", "F"),
            ("Command History", "history", "H"),
            ("System Metrics", "metrics", "M"),
        ]
        
        self.nav_buttons = {}
        for text, panel, shortcut in nav_items:
            btn_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=2)
            
            btn = ctk.CTkButton(
                btn_frame, text=f"  {text}", anchor="w",
                fg_color="transparent" if panel != "console" else colors["accent_cyan"],
                text_color=colors["text_primary"] if panel != "console" else colors["bg_dark"],
                hover_color=colors["bg_card_hover"],
                font=("JetBrains Mono", 12),
                height=36, corner_radius=8,
                command=lambda p=panel: self.switch_panel(p)
            )
            btn.pack(side="left", fill="x", expand=True)
            
            shortcut_label = ctk.CTkLabel(btn_frame, text=shortcut, 
                                         text_color=colors["text_muted"], font=("JetBrains Mono", 10))
            shortcut_label.pack(side="right", padx=5)
            
            self.nav_buttons[panel] = btn
        
        # Separator
        ctk.CTkFrame(sidebar, fg_color=colors["border"], height=1).pack(fill="x", padx=15, pady=15)
        
        # Quick commands section
        ctk.CTkLabel(sidebar, text="QUICK COMMANDS", text_color=colors["text_muted"], 
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=15, pady=(0, 10))
        
        quick_cmds = ctk.CTkFrame(sidebar, fg_color="transparent")
        quick_cmds.pack(fill="x", padx=15)
        
        quick_buttons = [
            ("🎤", self.toggle_voice, colors["accent_cyan"]),
            ("📸", lambda: self.execute_command("screenshot"), colors["accent_green"]),
            ("📷", lambda: self.execute_command("camera"), colors["accent_purple"]),
            ("🌐", lambda: self.execute_command("open browser"), colors["accent_orange"]),
            ("⏻", lambda: self.execute_command("exit"), colors["accent_red"]),
        ]

        for i, (icon, cmd, color) in enumerate(quick_buttons):
            btn = ctk.CTkButton(quick_cmds, text=icon, width=36, height=36,
                               fg_color=colors["bg_card_hover"], hover_color=color,
                               font=("Segoe UI Emoji", 14), corner_radius=8,
                               command=cmd)
            btn.grid(row=0, column=i, padx=2)
        
        # Weather widget
        self.create_weather_widget(sidebar)
        
        # Quick notes
        self.create_notes_widget(sidebar)
    
    def create_weather_widget(self, parent):
        """Create weather widget in sidebar with real data"""
        colors = Config.COLORS
        
        weather_frame = ctk.CTkFrame(parent, fg_color=colors["bg_card_hover"], corner_radius=10)
        weather_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(weather_frame, text="WEATHER", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=10, pady=(8, 0))
        
        temp_frame = ctk.CTkFrame(weather_frame, fg_color="transparent")
        temp_frame.pack(fill="x", padx=10, pady=5)
        
        # Fetch real weather in background
        self.weather_icon = ctk.CTkLabel(temp_frame, text="☀️", font=("Segoe UI Emoji", 24))
        self.weather_icon.pack(side="left")
        
        temp_info = ctk.CTkFrame(temp_frame, fg_color="transparent")
        temp_info.pack(side="left", padx=10)
        
        self.weather_temp = ctk.CTkLabel(temp_info, text="--°C", text_color=colors["accent_cyan"],
                    font=("JetBrains Mono", 18, "bold"))
        self.weather_temp.pack(anchor="w")
        
        self.weather_desc = ctk.CTkLabel(temp_info, text="Loading...", text_color=colors["text_secondary"],
                    font=("JetBrains Mono", 10))
        self.weather_desc.pack(anchor="w")
        
        self.weather_humidity = ctk.CTkLabel(weather_frame, text="💧 Humidity: --", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10))
        self.weather_humidity.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Fetch weather in background
        def fetch_weather():
            try:
                resp = requests.get("https://wttr.in/London?format=j1", timeout=5)
                if resp.ok:
                    data = resp.json()
                    current = data['current_condition'][0]
                    temp = int(current['temp_C'])
                    desc = current['weatherDesc'][0]['value']
                    humidity = current['humidity']
                    
                    # Update UI on main thread
                    self.root.after(0, lambda: self.update_weather_display(temp, desc, humidity))
            except:
                pass  # Use defaults if fetch fails
        
        threading.Thread(target=fetch_weather, daemon=True).start()
    
    def update_weather_display(self, temp: int, desc: str, humidity: int):
        """Update weather display with fetched data"""
        colors = Config.COLORS
        
        # Choose icon based on description
        icon = "☀️"
        if 'rain' in desc.lower():
            icon = "🌧️"
        elif 'cloud' in desc.lower():
            icon = "☁️"
        elif 'snow' in desc.lower():
            icon = "❄️"
        elif 'night' in desc.lower():
            icon = "🌙"
        
        self.weather_icon.configure(text=icon)
        self.weather_temp.configure(text=f"{temp}°C")
        self.weather_desc.configure(text=desc[:20])
        self.weather_humidity.configure(text=f"💧 Humidity: {humidity}%")
    
    def create_notes_widget(self, parent):
        """Create quick notes widget"""
        colors = Config.COLORS
        
        notes_frame = ctk.CTkFrame(parent, fg_color=colors["bg_card_hover"], corner_radius=10)
        notes_frame.pack(fill="x", padx=15, pady=(10, 15), side="bottom")
        
        header = ctk.CTkFrame(notes_frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 5))
        
        ctk.CTkLabel(header, text="QUICK NOTES", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10)).pack(side="left")
        
        add_btn = ctk.CTkButton(header, text="+", width=24, height=24,
                               fg_color="transparent", hover_color=colors["accent_cyan"],
                               font=("JetBrains Mono", 14), command=self.add_note)
        add_btn.pack(side="right")
        
        self.notes_list = ctk.CTkFrame(notes_frame, fg_color="transparent")
        self.notes_list.pack(fill="x", padx=10, pady=(0, 8))
        
        self.refresh_notes()
    
    def create_main_content(self, parent):
        """Create main content area with organized panels"""
        colors = Config.COLORS
        
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # Top section - Command input area
        input_section = ctk.CTkFrame(main_frame, fg_color=colors["bg_card"], corner_radius=12)
        input_section.pack(fill="x", padx=0, pady=(0, 12))
        
        # Command input label
        ctk.CTkLabel(input_section, text="◈ COMMAND INPUT", text_color=colors["accent_cyan"],
                    font=("JetBrains Mono", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 8))
        
        # Input area
        input_frame = ctk.CTkFrame(input_section, fg_color=colors["bg_dark"], corner_radius=8)
        input_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        # Command input with icon
        input_left = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_left.pack(side="left", padx=8, pady=6)
        
        ctk.CTkLabel(input_left, text=">", text_color=colors["accent_green"],
                    font=("JetBrains Mono", 14, "bold")).pack(side="left", padx=(0, 8))
        
        self.command_input = ctk.CTkEntry(
            input_frame, placeholder_text="Type command here... (press Enter or click send)",
            fg_color=colors["bg_dark"], text_color=colors["text_primary"],
            font=("JetBrains Mono", 12), border_color=colors["border"], border_width=1
        )
        self.command_input.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=6)
        self.command_input.bind("<Return>", self.on_command_input)
        
        # Send button
        send_btn = ctk.CTkButton(
            input_frame, text="⬆ SEND", fg_color=colors["accent_cyan"],
            text_color=colors["bg_dark"], font=("JetBrains Mono", 11, "bold"),
            width=100, height=32, command=self.on_command_input
        )
        send_btn.pack(side="right", padx=4, pady=4)
        
        # Separator
        ctk.CTkFrame(input_section, fg_color=colors["border"], height=1).pack(fill="x", padx=15, pady=8)
        
        # Bottom section - Panel display area
        panels_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        panels_frame.pack(fill="both", expand=True, padx=0)
        
        # Panel header with navigation tabs
        tab_frame = ctk.CTkFrame(panels_frame, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(0, 8))
        
        self.panels_container = ctk.CTkFrame(panels_frame, fg_color="transparent")
        self.panels_container.pack(fill="both", expand=True)
        
        # Create all panels
        self.panels = {}
        self.panel_tabs = {}
        
        # Define panels
        panel_list = [
            ("console", "◈ CONSOLE", colors["accent_cyan"]),
            ("ai", "◆ AI ASSISTANT", colors["accent_purple"]),
            ("tasks", "★ TASKS", colors["accent_green"]),
            ("reminders", "⚡ REMINDERS", colors["accent_orange"]),
            ("files", "📁 FILES", colors["accent_cyan"]),
            ("history", "⏱ HISTORY", colors["accent_yellow"]),
            ("metrics", "⊙ METRICS", colors["accent_purple"]),
        ]
        
        # Create tab buttons
        for panel_id, label, color in panel_list:
            tab_btn = ctk.CTkButton(
                tab_frame, text=label, fg_color="transparent", text_color=colors["text_muted"],
                font=("JetBrains Mono", 11), height=28, corner_radius=6,
                hover_color=colors["bg_card_hover"],
                command=lambda p=panel_id, c=color: self.switch_panel(p, tab_color=c)
            )
            tab_btn.pack(side="left", padx=3, pady=0)
            self.panel_tabs[panel_id] = (tab_btn, color)
        
        # Create panels
        self.create_console_panel()
        self.create_ai_panel()
        self.create_tasks_panel()
        self.create_reminders_panel()
        self.create_files_panel()
        self.create_history_panel()
        self.create_metrics_panel()
        
        # Show console by default
        self.switch_panel("console")
        
        # Command input bar at bottom
        self.create_command_bar(main_frame)
    
    def create_console_panel(self):
        """Create command console panel"""
        colors = Config.COLORS
        
        panel = ctk.CTkFrame(self.panels_container, fg_color=colors["bg_card"], corner_radius=12)
        self.panels["console"] = panel
        
        # Terminal header
        header = ctk.CTkFrame(panel, fg_color=colors["bg_card_hover"], height=35, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        dots_frame = ctk.CTkFrame(header, fg_color="transparent")
        dots_frame.pack(side="left", padx=10)
        
        for color in [colors["accent_red"], colors["accent_yellow"], colors["accent_green"]]:
            ctk.CTkLabel(dots_frame, text="●", text_color=color, font=("Arial", 10)).pack(side="left", padx=2)
        
        ctk.CTkLabel(header, text="orion@navigator:~$", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 11)).pack(side="left", padx=10)
        
        # Console output
        self.console_text = ctk.CTkTextbox(
            panel, fg_color=colors["bg_dark"], text_color=colors["accent_cyan"],
            font=("JetBrains Mono", 12), wrap="word", corner_radius=0
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.console_text.configure(state="disabled")
    
    def create_ai_panel(self):
        """Create AI chat panel"""
        colors = Config.COLORS
        
        panel = ctk.CTkFrame(self.panels_container, fg_color=colors["bg_card"], corner_radius=12)
        self.panels["ai"] = panel
        
        # Header
        header = ctk.CTkFrame(panel, fg_color=colors["bg_card_hover"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="◈ AI ASSISTANT", text_color=colors["accent_purple"],
                    font=("JetBrains Mono", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        status = "Connected" if self.ai.available else "API Key Required"
        status_color = colors["accent_green"] if self.ai.available else colors["accent_red"]
        ctk.CTkLabel(header, text=f"● {status}", text_color=status_color,
                    font=("JetBrains Mono", 10)).pack(side="right", padx=15)
        
        # Chat display (upper part)
        self.ai_chat = ctk.CTkTextbox(
            panel, fg_color=colors["bg_dark"], text_color=colors["text_primary"],
            font=("JetBrains Mono", 12), wrap="word"
        )
        self.ai_chat.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.ai_chat.configure(state="disabled")
        
        # AI input bar (lower part) - new
        input_frame = ctk.CTkFrame(panel, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        self.ai_input = ctk.CTkEntry(
            input_frame, placeholder_text="Ask AI...",
            fg_color=colors["bg_dark"], text_color=colors["text_primary"],
            font=("JetBrains Mono", 11), border_color=colors["border"], border_width=1
        )
        self.ai_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.ai_input.bind("<Return>", self.on_ai_input)
        
        send_btn = ctk.CTkButton(
            input_frame, text="Send", fg_color=colors["accent_purple"],
            text_color=colors["text_primary"], font=("JetBrains Mono", 10, "bold"),
            width=70, height=32, command=self.on_ai_input
        )
        send_btn.pack(side="right")

    def create_command_bar(self, parent):
        """Create bottom command bar with send, mic and clear controls"""
        colors = Config.COLORS

        bar = ctk.CTkFrame(parent, fg_color="transparent", height=48)
        bar.pack(fill="x", side="bottom", padx=12, pady=(8, 12))

        # Status / hint label
        self.status_label = ctk.CTkLabel(bar, text="", text_color=colors["text_secondary"],
                                         font=("JetBrains Mono", 10))
        self.status_label.pack(side="left", padx=8)

        # Right-side controls
        controls_frame = ctk.CTkFrame(bar, fg_color="transparent")
        controls_frame.pack(side="right")

        clear_btn = ctk.CTkButton(controls_frame, text="Clear", width=80,
                                  fg_color=colors["bg_card_hover"], command=self.clear_console)
        clear_btn.pack(side="right", padx=6)

        mic_btn = ctk.CTkButton(controls_frame, text="🎤", width=40,
                                fg_color=colors["bg_card_hover"], command=self.toggle_listen)
        mic_btn.pack(side="right", padx=6)

        send_btn = ctk.CTkButton(controls_frame, text="Send", width=80,
                                 fg_color=colors["accent_cyan"], command=self.on_command_input)
        send_btn.pack(side="right", padx=6)

    def clear_console(self):
        """Clear console and AI chat outputs with feedback"""
        try:
            if hasattr(self, "console_text"):
                self.console_text.configure(state="normal")
                self.console_text.delete("1.0", "end")
                self.console_text.insert("end", "[CONSOLE CLEARED]\n")
                self.console_text.configure(state="disabled")
        except Exception as e:
            print(f"Clear console error: {e}")

        try:
            if hasattr(self, "ai_chat"):
                self.ai_chat.configure(state="normal")
                self.ai_chat.delete("1.0", "end")
                self.ai_chat.insert("end", "[AI CHAT CLEARED]\n")
                self.ai_chat.configure(state="disabled")
        except Exception as e:
            print(f"Clear AI chat error: {e}")
        
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="Cleared")
            self.root.after(2000, lambda: self.status_label.configure(text="Ready"))

    def toggle_listen(self):
        """Start a background listen and place recognized text into the command input with feedback."""
        # Show listening status
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="🎤 Listening...")
        
        def _listen():
            try:
                if hasattr(self, "voice") and self.voice:
                    if not getattr(self.voice, 'has_microphone', False):
                        self.root.after(0, lambda: self.log_to_console("Microphone not available", "error"))
                        return
                    
                    text = self.voice.listen(timeout=6)
                    if text:
                        try:
                            self.command_input.delete(0, "end")
                            self.command_input.insert(0, text)
                            self.root.after(0, lambda t=text: self.log_to_console(f"Recognized: {t}", "success"))
                        except Exception as e:
                            self.root.after(0, lambda: self.log_to_console(f"Insert error: {e}", "error"))
                    else:
                        self.root.after(0, lambda: self.log_to_console("No speech detected", "info"))
                else:
                    self.root.after(0, lambda: self.log_to_console("Voice engine not initialized", "error"))
            except Exception as e:
                print(f"Listen thread error: {e}")
                self.root.after(0, lambda: self.log_to_console(f"Listen error: {e}", "error"))
            finally:
                # Clear listening status
                if hasattr(self, 'status_label'):
                    self.root.after(0, lambda: self.status_label.configure(text="Ready"))

        threading.Thread(target=_listen, daemon=True).start()
    
    def create_tasks_panel(self):
        """Create tasks panel"""
        colors = Config.COLORS
        
        panel = ctk.CTkFrame(self.panels_container, fg_color=colors["bg_card"], corner_radius=12)
        self.panels["tasks"] = panel
        
        # Header
        header = ctk.CTkFrame(panel, fg_color=colors["bg_card_hover"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="◈ TASKS", text_color=colors["accent_green"],
                    font=("JetBrains Mono", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        add_btn = ctk.CTkButton(header, text="+ Add Task", fg_color=colors["accent_green"],
                               text_color=colors["bg_dark"], font=("JetBrains Mono", 11),
                               width=100, height=30, command=self.prompt_add_task)
        add_btn.pack(side="right", padx=15, pady=10)
        
        # Tasks list
        self.tasks_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.tasks_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_tasks()
    
    def create_reminders_panel(self):
        """Create reminders panel"""
        colors = Config.COLORS
        
        panel = ctk.CTkFrame(self.panels_container, fg_color=colors["bg_card"], corner_radius=12)
        self.panels["reminders"] = panel
        
        # Header
        header = ctk.CTkFrame(panel, fg_color=colors["bg_card_hover"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="◈ REMINDERS", text_color=colors["accent_orange"],
                    font=("JetBrains Mono", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        add_btn = ctk.CTkButton(header, text="+ Add Reminder", fg_color=colors["accent_orange"],
                               text_color=colors["bg_dark"], font=("JetBrains Mono", 11),
                               width=120, height=30, command=self.prompt_add_reminder)
        add_btn.pack(side="right", padx=15, pady=10)
        
        # Reminders list
        self.reminders_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.reminders_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_reminders()
    
    def create_files_panel(self):
        """Create file explorer panel"""
        colors = Config.COLORS
        
        panel = ctk.CTkFrame(self.panels_container, fg_color=colors["bg_card"], corner_radius=12)
        self.panels["files"] = panel
        
        # Header
        header = ctk.CTkFrame(panel, fg_color=colors["bg_card_hover"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="◈ FILE EXPLORER", text_color=colors["accent_cyan"],
                    font=("JetBrains Mono", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        # Path bar
        self.current_path = Path.home()
        self.path_var = ctk.StringVar(value=str(self.current_path))
        
        path_entry = ctk.CTkEntry(header, textvariable=self.path_var, width=400,
                                 fg_color=colors["bg_dark"], font=("JetBrains Mono", 11))
        path_entry.pack(side="left", padx=10, pady=10)
        path_entry.bind("<Return>", lambda e: self.navigate_to_path(self.path_var.get()))
        
        # Files list
        self.files_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.files_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_files()
    
    def create_history_panel(self):
        """Create command history panel"""
        colors = Config.COLORS
        
        panel = ctk.CTkFrame(self.panels_container, fg_color=colors["bg_card"], corner_radius=12)
        self.panels["history"] = panel
        
        # Header
        header = ctk.CTkFrame(panel, fg_color=colors["bg_card_hover"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="◈ COMMAND HISTORY", text_color=colors["accent_yellow"],
                    font=("JetBrains Mono", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        clear_btn = ctk.CTkButton(header, text="Clear", fg_color=colors["accent_red"],
                                 text_color=colors["text_primary"], font=("JetBrains Mono", 11),
                                 width=70, height=30, command=self.clear_history)
        clear_btn.pack(side="right", padx=15, pady=10)
        
        # History list
        self.history_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_metrics_panel(self):
        """Create system metrics panel"""
        colors = Config.COLORS
        
        panel = ctk.CTkFrame(self.panels_container, fg_color=colors["bg_card"], corner_radius=12)
        self.panels["metrics"] = panel
        
        # Header
        header = ctk.CTkFrame(panel, fg_color=colors["bg_card_hover"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="◈ SYSTEM METRICS", text_color=colors["accent_purple"],
                    font=("JetBrains Mono", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        # Metrics content
        self.metrics_content = ctk.CTkFrame(panel, fg_color="transparent")
        self.metrics_content.pack(fill="both", expand=True, padx=20, pady=20)
    
    def create_right_panel(self, parent):
        """Create right panel with metrics and actions - improved organization"""
        colors = Config.COLORS
        
        right_panel = ctk.CTkFrame(parent, fg_color=colors["bg_card"], width=320, corner_radius=12)
        right_panel.pack(side="right", fill="both", padx=(8, 0))
        right_panel.pack_propagate(False)
        
        # Scrollable container for right panel content
        right_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        right_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        
        # 1. Orion Orb visualization (top)
        self.create_orb_widget(right_scroll)
        
        # 2. System metrics (organized)
        self.create_metrics_widget(right_scroll)
        
        # 3. Quick actions (organized)
        self.create_actions_widget(right_scroll)
        
        # 4. Recent tasks (organized)
        self.create_recent_tasks_widget(right_scroll)
    
    def create_orb_widget(self, parent):
        """Create animated Orion orb - optimized for right panel"""
        colors = Config.COLORS
        
        orb_frame = ctk.CTkFrame(parent, fg_color=colors["bg_card_hover"], corner_radius=10)
        orb_frame.pack(fill="x", padx=0, pady=(0, 12))
        
        # Label
        ctk.CTkLabel(orb_frame, text="◈ ORION ORB", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=12, pady=(8, 5))
        
        # Canvas for orb animation (smaller for right panel)
        self.orb_canvas = ctk.CTkCanvas(orb_frame, bg=colors["bg_dark"], 
                                        highlightthickness=0, width=296, height=120)
        self.orb_canvas.pack(fill="x", padx=8, pady=(0, 8))
        
        # Status text
        status_frame = ctk.CTkFrame(orb_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        ctk.CTkLabel(status_frame, text="● System Active", text_color=colors["accent_green"],
                    font=("JetBrains Mono", 10)).pack(anchor="w")
        
        # Draw orb
        self.orb_angle = 0
        self._animation_running = True
        self._animation_id = None
        self.animate_orb()

        # Bind cleanup on window close
        if not hasattr(self, '_close_bound'):
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            self._close_bound = True

    def _on_close(self):
        """Clean up on window close"""
        self._animation_running = False
        if self._animation_id:
            try:
                self.root.after_cancel(self._animation_id)
            except:
                pass
        self.voice.stop_speaking()
        self.root.destroy()

    def animate_orb(self):
        """Animate the orb with proper cleanup"""
        if not self._animation_running:
            return

        colors = Config.COLORS
        self.orb_canvas.delete("all")

        cx, cy = 125, 70

        # Outer rings
        for i, radius in enumerate([50, 40, 30]):
            offset = math.sin(self.orb_angle + i * 0.5) * 3
            self.orb_canvas.create_oval(
                cx - radius + offset, cy - radius * 0.3,
                cx + radius + offset, cy + radius * 0.3,
                outline=colors["accent_cyan"], width=1
            )

        # Core glow
        for i in range(3):
            r = 20 - i * 5
            self.orb_canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=colors["accent_green"], outline=""
            )

        # Particles
        for i in range(8):
            angle = self.orb_angle + i * (math.pi / 4)
            dist = 35 + math.sin(angle * 2) * 10
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist * 0.4
            self.orb_canvas.create_oval(px-2, py-2, px+2, py+2, fill=colors["accent_cyan"], outline="")

        self.orb_angle += 0.05
        if self._animation_running:
            self._animation_id = self.root.after(50, self.animate_orb)
    
    def create_metrics_widget(self, parent):
        """Create system metrics display"""
        colors = Config.COLORS
        
        metrics_frame = ctk.CTkFrame(parent, fg_color=colors["bg_card_hover"], corner_radius=10)
        metrics_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(metrics_frame, text="◈ SYSTEM METRICS", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Metrics
        self.metric_bars = {}
        metrics_data = [
            ("CPU Usage", "cpu", colors["accent_cyan"]),
            ("Memory", "memory", colors["accent_green"]),
            ("Storage", "storage", colors["accent_purple"]),
            ("Temperature", "temp", colors["accent_orange"]),
            ("Power", "power", colors["accent_yellow"]),
        ]
        
        for label, key, color in metrics_data:
            row = ctk.CTkFrame(metrics_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            
            ctk.CTkLabel(row, text=label, text_color=colors["text_secondary"],
                        font=("JetBrains Mono", 10), width=80, anchor="w").pack(side="left")
            
            bar = ctk.CTkProgressBar(row, fg_color=colors["bg_dark"], progress_color=color,
                                    height=8, width=120)
            bar.pack(side="left", padx=5)
            bar.set(0)
            
            val_label = ctk.CTkLabel(row, text="0%", text_color=color,
                                    font=("JetBrains Mono", 10), width=40)
            val_label.pack(side="right")
            
            self.metric_bars[key] = (bar, val_label)
        
        # Uptime
        self.uptime_label = ctk.CTkLabel(metrics_frame, text="⏱ Uptime: 0h 0m",
                                        text_color=colors["text_muted"], font=("JetBrains Mono", 10))
        self.uptime_label.pack(anchor="w", padx=15, pady=(5, 10))
    
    def create_actions_widget(self, parent):
        """Create quick actions"""
        colors = Config.COLORS
        
        actions_frame = ctk.CTkFrame(parent, fg_color=colors["bg_card_hover"], corner_radius=10)
        actions_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(actions_frame, text="◈ QUICK ACTIONS", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=15, pady=(10, 10))
        
        actions = [
            ("Screenshot", lambda: self.execute_command("screenshot")),
            ("Camera", lambda: self.execute_command("camera")),
            ("Browser", lambda: self.execute_command("open browser")),
            ("Files", lambda: self.execute_command("open folder")),
            ("Volume Up", lambda: self.execute_command("volume up")),
            ("Volume Down", lambda: self.execute_command("volume down")),
            ("System Info", lambda: self.execute_command("system info")),
        ]
        
        for text, cmd in actions:
            btn = ctk.CTkButton(actions_frame, text=text, fg_color=colors["bg_dark"],
                               hover_color=colors["accent_cyan"], text_color=colors["text_primary"],
                               font=("JetBrains Mono", 11), height=32, corner_radius=6,
                               command=cmd)
            btn.pack(fill="x", padx=15, pady=2)
        
        ctk.CTkFrame(actions_frame, fg_color="transparent", height=10).pack()
    
    def create_actions_widget(self, parent):
        """Create quick actions - improved grid layout"""
        colors = Config.COLORS
        
        actions_frame = ctk.CTkFrame(parent, fg_color=colors["bg_card_hover"], corner_radius=10)
        actions_frame.pack(fill="x", padx=0, pady=(0, 12))
        
        ctk.CTkLabel(actions_frame, text="◈ QUICK ACTIONS", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=12, pady=(8, 8))
        
        # 2x3 button grid
        actions = [
            ("📸 Screenshot", lambda: self.execute_command("screenshot")),
            ("📷 Camera", lambda: self.execute_command("camera")),
            ("🌐 Browser", lambda: self.execute_command("open browser")),
            ("📁 Files", lambda: self.execute_command("open folder")),
            ("🔊 Vol Up", lambda: self.execute_command("volume up")),
            ("🔇 Vol Down", lambda: self.execute_command("volume down")),
        ]
        
        # Create grid
        grid_container = ctk.CTkFrame(actions_frame, fg_color="transparent")
        grid_container.pack(fill="x", padx=10, pady=(0, 8))
        
        for i, (text, cmd) in enumerate(actions):
            col = i % 2
            row = i // 2
            
            btn = ctk.CTkButton(
                grid_container, text=text, fg_color=colors["bg_dark"],
                hover_color=colors["accent_cyan"], text_color=colors["text_secondary"],
                font=("JetBrains Mono", 10), height=32, corner_radius=6,
                command=cmd
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
        
        grid_container.grid_columnconfigure(0, weight=1)
        grid_container.grid_columnconfigure(1, weight=1)

    def create_recent_tasks_widget(self, parent):
        """Create recent tasks list in the right panel"""
        colors = Config.COLORS

        tasks_frame = ctk.CTkFrame(parent, fg_color=colors["bg_card_hover"], corner_radius=10)
        tasks_frame.pack(fill="x", padx=0, pady=(0, 12))

        ctk.CTkLabel(tasks_frame, text="◈ RECENT TASKS", text_color=colors["text_muted"],
                    font=("JetBrains Mono", 10)).pack(anchor="w", padx=12, pady=(8, 6))

        # Text area for tasks (read-only)
        tasks_box = ctk.CTkTextbox(tasks_frame, fg_color=colors["bg_dark"], text_color=colors["text_primary"],
                                   font=("JetBrains Mono", 11), height=110, wrap="word")
        tasks_box.pack(fill="both", expand=False, padx=10, pady=(0, 10))
        tasks_box.configure(state="normal")

        # Load tasks from file if available
        tasks = []
        try:
            if Config.TASKS_FILE.exists():
                with open(Config.TASKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tasks = data
                    elif isinstance(data, dict):
                        tasks = data.get('tasks', []) or data.get('items', []) or []
        except Exception:
            tasks = []

        if not tasks:
            tasks_box.insert("end", "No recent tasks. Create some in the Tasks panel.")
        else:
            for t in tasks[-6:]:
                if isinstance(t, dict):
                    title = t.get('title') or t.get('name') or str(t)
                else:
                    title = str(t)
                tasks_box.insert("end", f"- {title}\n")

        tasks_box.configure(state="disabled")
    
    # ==================== FUNCTIONALITY ====================
    
    def switch_panel(self, panel_name: str, tab_color=None):
        """Switch to a different panel with improved visual feedback"""
        colors = Config.COLORS
        
        # Hide all panels
        for name, panel in self.panels.items():
            panel.pack_forget()
        
        # Show selected panel
        if panel_name in self.panels:
            self.panels[panel_name].pack(fill="both", expand=True)
            self.current_panel = panel_name
        
        # Update nav buttons
        if hasattr(self, 'nav_buttons'):
            for name, btn in self.nav_buttons.items():
                if name == panel_name:
                    btn.configure(fg_color=colors["accent_cyan"], text_color=colors["bg_dark"])
                else:
                    btn.configure(fg_color="transparent", text_color=colors["text_primary"])
        
        # Update panel tabs
        if hasattr(self, 'panel_tabs'):
            for name, (tab_btn, color) in self.panel_tabs.items():
                if name == panel_name:
                    tab_btn.configure(fg_color=tab_color or color, text_color=colors["bg_dark"])
                else:
                    tab_btn.configure(fg_color="transparent", text_color=colors["text_muted"])
        
        # Refresh content if needed
        if panel_name == "history":
            self.refresh_history()
        elif panel_name == "files":
            self.refresh_files()
    
    def on_ai_input(self, event=None):
        """Handle AI input from the AI panel directly"""
        if not hasattr(self, 'ai_input'):
            return

        query = self.ai_input.get().strip()
        if not query:
            return

        # Clear entry
        self.ai_input.delete(0, 'end')

        # Log the user query
        colors = Config.COLORS
        self.ai_chat.configure(state="normal")
        self.ai_chat.insert("end", f"You: {query}\n")
        self.ai_chat.see("end")
        self.ai_chat.configure(state="disabled")

        # Get AI response in background thread
        def get_response():
            try:
                response = self.ai.chat(query)
                self.root.after(0, lambda r=response: self.display_ai_response(r))
            except Exception as e:
                self.root.after(0, lambda: self.display_ai_response(f"Error: {e}"))

        threading.Thread(target=get_response, daemon=True).start()

    def display_ai_response(self, response: str):
        """Display AI response in the chat"""
        colors = Config.COLORS
        self.ai_chat.configure(state="normal")
        self.ai_chat.insert("end", f"AI: {response}\n\n")
        self.ai_chat.see("end")
        self.ai_chat.configure(state="disabled")
    
    def log_to_console(self, message: str, msg_type: str = "info"):
        """Log message to console"""
        colors = Config.COLORS
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        self.console_text.configure(state="normal")
        
        prefix = "ORION"
        if msg_type == "user":
            prefix = "USER"
        elif msg_type == "error":
            prefix = "ERROR"
        elif msg_type == "success":
            prefix = "SUCCESS"
        
        self.console_text.insert("end", f"[{timestamp}] {prefix}: {message}\n")
        self.console_text.see("end")
        self.console_text.configure(state="disabled")
    
    def execute_command(self, command: str):
        """Execute a command in background thread to prevent UI freezing"""
        if not command:
            return
        
        # Auto-switch to Console panel so user sees output
        if hasattr(self, 'switch_panel'):
            self.switch_panel("console")
        
        # Log user command immediately on main thread
        self.log_to_console(command, "user")
        
        # Show processing indicator
        self.log_to_console("Processing...", "info")
        
        def process_in_background():
            """Process command in background thread"""
            try:
                # Process command (this may take time)
                response = self.processor.process(command)
                
                # Update UI on main thread
                self.root.after(0, lambda r=response: self.log_to_console(r, "info"))
                
                # Speak response (shortened) - also on main thread
                if len(response) < 200:
                    self.root.after(0, lambda r=response: self.voice.speak(r))
            except Exception as e:
                import traceback
                error_msg = f"Error executing command: {e}\n{traceback.format_exc()}"
                self.root.after(0, lambda: self.log_to_console(error_msg, "error"))
        
        # Run in background thread
        threading.Thread(target=process_in_background, daemon=True).start()
    
    def execute_from_entry(self):
        """Execute command from entry field"""
        command = self.cmd_entry.get().strip()
        if command:
            self.cmd_entry.delete(0, "end")
            self.execute_command(command)

    def on_command_input(self, event=None):
        """Unified handler for command input (Enter key or button) with feedback.

        Supports both `self.command_input` (new name) and `self.cmd_entry` (legacy name).
        """
        # Prefer the new `command_input` if it exists
        cmd = None
        if hasattr(self, 'command_input') and self.command_input:
            try:
                cmd = self.command_input.get().strip()
                # Clear entry
                self.command_input.delete(0, 'end')
            except Exception:
                cmd = None
        # Fallback to legacy `cmd_entry`
        if not cmd and hasattr(self, 'cmd_entry') and self.cmd_entry:
            try:
                cmd = self.cmd_entry.get().strip()
                self.cmd_entry.delete(0, 'end')
            except Exception:
                cmd = None

        if cmd:
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="Processing...")
            self.execute_command(cmd)
        else:
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="(empty command)")
                self.root.after(1500, lambda: self.status_label.configure(text="Ready"))
    
    def toggle_voice(self):
        """Toggle voice input (push-to-talk) - thread-safe"""
        colors = Config.COLORS

        # Thread-safe check using lock
        if not hasattr(self, '_voice_lock'):
            self._voice_lock = threading.Lock()

        with self._voice_lock:
            if self.is_listening:
                return
            self.is_listening = True

        self.mic_btn.configure(fg_color=colors["accent_red"])
        self.mic_status.configure(text="● Listening...", text_color=colors["accent_red"])
        self.log_to_console("Listening... Speak now.", "info")
        self.voice.speak("Listening")

        def listen_thread():
            try:
                result = self.voice.listen(timeout=7)
                self.root.after(0, lambda r=result: self.handle_voice_result(r))
            except Exception as e:
                self.root.after(0, lambda: self.handle_voice_result(None))
                print(f"Voice listen error: {e}")

        threading.Thread(target=listen_thread, daemon=True).start()
    
    def handle_voice_result(self, result: Optional[str]):
        """Handle voice recognition result"""
        colors = Config.COLORS
        
        self.is_listening = False
        self.mic_btn.configure(fg_color=colors["bg_card_hover"])
        self.mic_status.configure(text="● Mic Off", text_color=colors["text_muted"])
        
        if result:
            self.log_to_console(f"Heard: {result}", "success")
            self.execute_command(result)
        else:
            self.log_to_console("No speech detected. Try again.", "error")
    
    def greet(self):
        """Greet user on startup"""
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        self.log_to_console(f"{greeting}! Orion OS Navigator v{Config.VERSION} is online and ready to assist.", "info")
        self.log_to_console("Type 'help' for available commands or click the microphone to speak.", "info")
        self.voice.speak(f"{greeting}! Orion is ready.")
    
    def update_clock(self):
        """Update clock display"""
        now = datetime.datetime.now()
        self.time_label.configure(text=now.strftime("%H:%M:%S"))
        self.root.after(1000, self.update_clock)
    
    def update_system_metrics(self):
        """Update system metrics display"""
        try:
            info = self.system.get_system_info()
            
            # Update status bar
            self.cpu_label.configure(text=f"CPU {info.get('cpu', 0):.0f}%")
            self.ram_label.configure(text=f"RAM {info.get('memory', 0):.0f}%")
            self.disk_label.configure(text=f"SSD {info.get('disk', 0):.0f}%")
            
            # Update metric bars
            if "cpu" in self.metric_bars:
                bar, label = self.metric_bars["cpu"]
                bar.set(info.get("cpu", 0) / 100)
                label.configure(text=f"{info.get('cpu', 0):.0f}%")
            
            if "memory" in self.metric_bars:
                bar, label = self.metric_bars["memory"]
                bar.set(info.get("memory", 0) / 100)
                label.configure(text=f"{info.get('memory', 0):.0f}%")
            
            if "storage" in self.metric_bars:
                bar, label = self.metric_bars["storage"]
                bar.set(info.get("disk", 0) / 100)
                label.configure(text=f"{info.get('disk', 0):.0f}%")
            
            if "temp" in self.metric_bars:
                bar, label = self.metric_bars["temp"]
                bar.set(0.4)  # Placeholder
                label.configure(text="40°C")
            
            if "power" in self.metric_bars:
                bar, label = self.metric_bars["power"]
                if info.get("battery"):
                    bar.set(info["battery"]["percent"] / 100)
                    label.configure(text=f"{info['battery']['percent']}%")
                else:
                    bar.set(0.87)
                    label.configure(text="87%")
            
            # Update uptime
            uptime = info.get("uptime", 0)
            days, rem = divmod(int(uptime), 86400)
            hours, rem = divmod(rem, 3600)
            mins = rem // 60
            if days > 0:
                self.uptime_label.configure(text=f"⏱ Uptime: {days}d {hours}h {mins}m")
            else:
                self.uptime_label.configure(text=f"⏱ Uptime: {hours}h {mins}m")
            
        except Exception as e:
            print(f"Metrics update error: {e}")
        
        self.root.after(2000, self.update_system_metrics)
    
    # ==================== TASKS ====================
    
    def get_tasks(self) -> List[Dict]:
        return self.tasks
    
    def add_task(self, text: str):
        self.tasks.append({"text": text, "done": False, "created": datetime.datetime.now().isoformat()})
        DataManager.save_json(Config.TASKS_FILE, self.tasks)
        self.refresh_tasks()
        self.refresh_recent_tasks()
    
    def toggle_task(self, index: int):
        if 0 <= index < len(self.tasks):
            self.tasks[index]["done"] = not self.tasks[index]["done"]
            DataManager.save_json(Config.TASKS_FILE, self.tasks)
            self.refresh_tasks()
            self.refresh_recent_tasks()
    
    def delete_task(self, index: int):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            DataManager.save_json(Config.TASKS_FILE, self.tasks)
            self.refresh_tasks()
            self.refresh_recent_tasks()
    
    def refresh_tasks(self):
        colors = Config.COLORS
        
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()
        
        if not self.tasks:
            ctk.CTkLabel(self.tasks_scroll, text="No tasks. Add one to get started!",
                        text_color=colors["text_muted"], font=("JetBrains Mono", 12)).pack(pady=20)
            return
        
        for i, task in enumerate(self.tasks):
            row = ctk.CTkFrame(self.tasks_scroll, fg_color=colors["bg_card_hover"], corner_radius=8)
            row.pack(fill="x", pady=3)
            
            check = ctk.CTkCheckBox(row, text=task["text"], 
                                   text_color=colors["text_primary"] if not task["done"] else colors["text_muted"],
                                   font=("JetBrains Mono", 12),
                                   command=lambda idx=i: self.toggle_task(idx))
            check.pack(side="left", padx=15, pady=10)
            if task["done"]:
                check.select()
            
            del_btn = ctk.CTkButton(row, text="×", width=30, height=30,
                                   fg_color="transparent", hover_color=colors["accent_red"],
                                   font=("Arial", 16), command=lambda idx=i: self.delete_task(idx))
            del_btn.pack(side="right", padx=10)
    
    def refresh_recent_tasks(self):
        colors = Config.COLORS
        
        for widget in self.recent_tasks_list.winfo_children():
            widget.destroy()
        
        recent = [t for t in self.tasks if not t.get("done")][:5]
        
        if not recent:
            ctk.CTkLabel(self.recent_tasks_list, text="No tasks yet.\nSay 'add task...'",
                        text_color=colors["text_muted"], font=("JetBrains Mono", 10)).pack(pady=10)
            return
        
        for task in recent:
            ctk.CTkLabel(self.recent_tasks_list, text=f"• {task['text'][:30]}...",
                        text_color=colors["text_secondary"], font=("JetBrains Mono", 10),
                        anchor="w").pack(fill="x", pady=2)
    
    def prompt_add_task(self):
        dialog = ctk.CTkInputDialog(text="Enter task:", title="Add Task")
        result = dialog.get_input()
        if result:
            self.add_task(result)
    
    # ==================== REMINDERS ====================
    
    def get_reminders(self) -> List[Dict]:
        return self.reminders
    
    def add_reminder(self, text: str, time_str: str = None):
        self.reminders.append({
            "text": text, 
            "time": time_str or datetime.datetime.now().isoformat(),
            "created": datetime.datetime.now().isoformat()
        })
        DataManager.save_json(Config.REMINDERS_FILE, self.reminders)
        self.refresh_reminders()
    
    def delete_reminder(self, index: int):
        if 0 <= index < len(self.reminders):
            del self.reminders[index]
            DataManager.save_json(Config.REMINDERS_FILE, self.reminders)
            self.refresh_reminders()
    
    def refresh_reminders(self):
        colors = Config.COLORS
        
        for widget in self.reminders_scroll.winfo_children():
            widget.destroy()
        
        if not self.reminders:
            ctk.CTkLabel(self.reminders_scroll, text="No reminders. Set one to stay organized!",
                        text_color=colors["text_muted"], font=("JetBrains Mono", 12)).pack(pady=20)
            return
        
        for i, reminder in enumerate(self.reminders):
            row = ctk.CTkFrame(self.reminders_scroll, fg_color=colors["bg_card_hover"], corner_radius=8)
            row.pack(fill="x", pady=3)
            
            ctk.CTkLabel(row, text="🔔", font=("Segoe UI Emoji", 14)).pack(side="left", padx=(15, 5), pady=10)
            ctk.CTkLabel(row, text=reminder["text"], text_color=colors["text_primary"],
                        font=("JetBrains Mono", 12)).pack(side="left", pady=10)
            
            del_btn = ctk.CTkButton(row, text="×", width=30, height=30,
                                   fg_color="transparent", hover_color=colors["accent_red"],
                                   font=("Arial", 16), command=lambda idx=i: self.delete_reminder(idx))
            del_btn.pack(side="right", padx=10)
    
    def prompt_add_reminder(self):
        dialog = ctk.CTkInputDialog(text="Enter reminder:", title="Add Reminder")
        result = dialog.get_input()
        if result:
            self.add_reminder(result)
    
    # ==================== NOTES ====================
    
    def add_note(self):
        dialog = ctk.CTkInputDialog(text="Enter note:", title="Quick Note")
        result = dialog.get_input()
        if result:
            self.notes.append({"text": result, "created": datetime.datetime.now().isoformat()})
            if len(self.notes) > 10:
                self.notes = self.notes[-10:]
            DataManager.save_json(Config.NOTES_FILE, self.notes)
            self.refresh_notes()
    
    def refresh_notes(self):
        colors = Config.COLORS
        
        for widget in self.notes_list.winfo_children():
            widget.destroy()
        
        # Filter valid notes and display
        valid_notes = [note for note in self.notes if isinstance(note, dict) and 'text' in note]
        
        if not valid_notes:
            ctk.CTkLabel(self.notes_list, text="No notes yet",
                        text_color=colors["text_muted"], font=("JetBrains Mono", 9),
                        anchor="w").pack(fill="x", pady=1)
            return
        
        for note in valid_notes[-5:]:
            note_text = note.get('text', 'Unknown')[:25]
            ctk.CTkLabel(self.notes_list, text=f"📝 {note_text}...",
                        text_color=colors["text_secondary"], font=("JetBrains Mono", 10),
                        anchor="w").pack(fill="x", pady=1)
    
    # ==================== FILES ====================
    
    def navigate_to_path(self, path: str):
        try:
            new_path = Path(path).expanduser()
            if new_path.exists() and new_path.is_dir():
                self.current_path = new_path
                self.path_var.set(str(self.current_path))
                self.refresh_files()
        except Exception as e:
            self.log_to_console(f"Navigation error: {e}", "error")
    
    def refresh_files(self):
        colors = Config.COLORS
        
        for widget in self.files_scroll.winfo_children():
            widget.destroy()
        
        # Parent directory button
        if self.current_path.parent != self.current_path:
            parent_btn = ctk.CTkButton(
                self.files_scroll, text="📁 ..", anchor="w",
                fg_color=colors["bg_card_hover"], hover_color=colors["accent_cyan"],
                text_color=colors["text_primary"], font=("JetBrains Mono", 12),
                height=35, corner_radius=6,
                command=lambda: self.navigate_to_path(str(self.current_path.parent))
            )
            parent_btn.pack(fill="x", pady=2)
        
        files = self.system.list_files(str(self.current_path))
        
        for f in files[:50]:
            icon = "📁" if f["is_dir"] else "📄"
            
            btn = ctk.CTkButton(
                self.files_scroll, text=f"{icon} {f['name']}", anchor="w",
                fg_color="transparent", hover_color=colors["bg_card_hover"],
                text_color=colors["text_primary"], font=("JetBrains Mono", 11),
                height=32, corner_radius=4,
                command=lambda p=f["path"], is_dir=f["is_dir"]: self.file_action(p, is_dir)
            )
            btn.pack(fill="x", pady=1)
    
    def file_action(self, path: str, is_dir: bool):
        if is_dir:
            self.navigate_to_path(path)
        else:
            self.system.open_file(path)
    
    # ==================== HISTORY ====================
    
    def refresh_history(self):
        colors = Config.COLORS
        
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        
        history = DataManager.load_json(Config.HISTORY_FILE, [])
        
        if not history:
            ctk.CTkLabel(self.history_scroll, text="No command history yet.",
                        text_color=colors["text_muted"], font=("JetBrains Mono", 12)).pack(pady=20)
            return
        
        for item in reversed(history[-50:]):
            row = ctk.CTkFrame(self.history_scroll, fg_color=colors["bg_card_hover"], corner_radius=6)
            row.pack(fill="x", pady=2)
            
            timestamp = item.get("timestamp", "")[:19].replace("T", " ")
            ctk.CTkLabel(row, text=timestamp, text_color=colors["text_muted"],
                        font=("JetBrains Mono", 9), width=130).pack(side="left", padx=10, pady=8)
            
            ctk.CTkLabel(row, text=item.get("command", ""), text_color=colors["text_primary"],
                        font=("JetBrains Mono", 11), anchor="w").pack(side="left", fill="x", expand=True, pady=8)
            
            rerun_btn = ctk.CTkButton(row, text="▶", width=30, height=25,
                                     fg_color="transparent", hover_color=colors["accent_green"],
                                     font=("Arial", 12),
                                     command=lambda c=item.get("command", ""): self.execute_command(c))
            rerun_btn.pack(side="right", padx=10)
    
    def clear_history(self):
        DataManager.save_json(Config.HISTORY_FILE, [])
        self.refresh_history()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  ORION OS NAVIGATOR v{Config.VERSION}")
    print(f"  Advanced AI Command Center")
    print(f"{'='*50}\n")
    
    # Check for Gemini API key
    if not Config.GEMINI_API_KEY:
        print("=" * 60)
        print("NOTE: GEMINI_API_KEY not set. AI features will be disabled.")
        print("To enable AI features:")
        print("  1. Get your API key from: https://makersuite.google.com/app/apikey")
        print("  2. Set environment variable:")
        print("     Windows: set GEMINI_API_KEY=your-api-key")
        print("     Linux/Mac: export GEMINI_API_KEY='your-api-key'")
        print("=" * 60)
        print()
    
    app = OrionApp()
    app.run()
