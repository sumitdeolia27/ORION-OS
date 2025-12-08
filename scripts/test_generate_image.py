# Headless test for image generation fallback
from orion_os_navigator import SystemController, GeminiAI, CommandProcessor
from pathlib import Path
import time

class DummyVoice:
    def __init__(self):
        self.has_microphone = False
    def speak(self, text):
        pass
    def listen(self, timeout=5):
        return None

class DummyApp:
    def __init__(self):
        pass
    def add_task(self, t):
        pass
    def get_tasks(self):
        return []
    def add_reminder(self, text):
        pass

if __name__ == '__main__':
    system = SystemController()
    voice = DummyVoice()
    ai = GeminiAI()
    app = DummyApp()
    processor = CommandProcessor(system, voice, ai, app)

    cmd = 'make the image of cat'
    print('> COMMAND:', cmd)
    res = processor.process(cmd)
    print('->', res)

    # If file path returned, check existence
    m = None
    import re
    m = re.search(r"Generated placeholder image \(cat\): (.+)", res)
    if m:
        p = Path(m.group(1))
        print('File exists?', p.exists())
    else:
        print('No local image generated (AI might have responded).')
