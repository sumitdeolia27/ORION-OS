import json
out = {}
try:
    import pyaudio
    out['pyaudio'] = getattr(pyaudio, '__version__', 'installed')
except Exception as e:
    out['pyaudio_error'] = str(e)
try:
    import speech_recognition as sr
    try:
        mics = sr.Microphone.list_microphone_names()
        out['microphones'] = mics
    except Exception as e:
        out['mic_list_error'] = str(e)
except Exception as e:
    out['sr_error'] = str(e)
print(json.dumps(out, ensure_ascii=False, indent=2))
