#!/usr/bin/env python3
"""
ORION OS NAVIGATOR - Functionality Test Script
Tests all major command categories to verify they work correctly.
"""

import requests
import json
import time
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:5000"

def test_command(command: str, description: str):
    """Test a single command"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/command",
            json={"command": command, "speak": False},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data.get("response", "No response")
                print(f"✅ SUCCESS")
                print(f"Response: {result[:200]}...")  # First 200 chars
                return True, result
            else:
                error = data.get("error", "Unknown error")
                print(f"❌ FAILED: {error}")
                return False, error
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Backend server not running!")
        print(f"   Start it with: python scripts/api_server.py")
        return False, "Connection error"
    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT: Command took too long")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e)

def main():
    """Run all functionality tests"""
    print("\n" + "="*60)
    print("ORION OS NAVIGATOR v3.0 - FUNCTIONALITY TEST SUITE")
    print("="*60)
    print("\n⚠️  Make sure the backend server is running:")
    print("   python scripts/api_server.py")
    print("\nPress Enter to start testing...")
    input()
    
    results = {
        "system": [],
        "camera": [],
        "processes": [],
        "files": [],
        "browser": [],
        "ai": [],
        "productivity": []
    }
    
    # SYSTEM COMMANDS
    print("\n" + "🔧 SYSTEM COMMANDS".center(60))
    results["system"].append(test_command("system info", "System Information"))
    results["system"].append(test_command("volume 50", "Set Volume to 50%"))
    time.sleep(1)  # Small delay between commands
    
    # CAMERA COMMANDS (may fail if no camera)
    print("\n" + "📷 CAMERA COMMANDS".center(60))
    results["camera"].append(test_command("camera preview", "Open Camera Preview"))
    time.sleep(1)
    
    # PROCESS MANAGEMENT
    print("\n" + "⚙️  PROCESS MANAGEMENT".center(60))
    results["processes"].append(test_command("processes", "List Processes"))
    results["processes"].append(test_command("top processes cpu", "Top Processes by CPU"))
    time.sleep(1)
    
    # FILE OPERATIONS
    print("\n" + "📁 FILE OPERATIONS".center(60))
    home = str(Path.home())
    results["files"].append(test_command(f"list files {home}", "List Files in Home Directory"))
    time.sleep(1)
    
    # BROWSER COMMANDS
    print("\n" + "🌐 BROWSER COMMANDS".center(60))
    results["browser"].append(test_command("search python tutorial", "Google Search"))
    time.sleep(2)  # Browser commands may take longer
    
    # AI COMMANDS (requires GEMINI_API_KEY)
    print("\n" + "🤖 AI COMMANDS".center(60))
    print("⚠️  Note: AI commands require GEMINI_API_KEY")
    results["ai"].append(test_command("ask ai what is python", "AI Chat"))
    time.sleep(2)
    
    # PRODUCTIVITY
    print("\n" + "📝 PRODUCTIVITY".center(60))
    results["productivity"].append(test_command("add task test task", "Add Task"))
    results["productivity"].append(test_command("show tasks", "Show Tasks"))
    results["productivity"].append(test_command("calculate 25 * 4", "Calculate"))
    results["productivity"].append(test_command("time", "Get Time"))
    results["productivity"].append(test_command("date", "Get Date"))
    time.sleep(1)
    
    # SUMMARY
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = 0
    total_passed = 0
    
    for category, tests in results.items():
        passed = sum(1 for success, _ in tests if success)
        total = len(tests)
        total_tests += total
        total_passed += passed
        
        status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
        print(f"{status} {category.upper():15} {passed}/{total} passed")
    
    print("="*60)
    print(f"OVERALL: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed!")
        return 0
    elif total_passed > 0:
        print("⚠️  Some tests failed. Check output above for details.")
        return 1
    else:
        print("❌ All tests failed. Check backend server connection.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

