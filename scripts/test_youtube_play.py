# Headless test for YouTube play handler
from orion_os_navigator import SystemController, GeminiAI, CommandProcessor

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

    tests = [
        "play Halka Halka in YouTube",
        "play Despacito on YouTube",
        "search youtube for classical music",
        "youtube",
        "open youtube"
    ]

    for t in tests:
        print('> COMMAND:', t)
        res = processor.process(t)
        print('->', res)

