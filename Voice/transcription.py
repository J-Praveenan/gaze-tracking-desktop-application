from pathlib import Path
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import time
import threading
import pyttsx3

# === Voice Model ===
MODEL_PATH = Path(__file__).resolve().parents[1] / "Voice_Model"
MODEL_PATH_POSIX = MODEL_PATH.as_posix()

model = AutoModelForSpeechSeq2Seq.from_pretrained(MODEL_PATH_POSIX, local_files_only=True)
processor = AutoProcessor.from_pretrained(MODEL_PATH_POSIX, local_files_only=True)

asr_model = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    generate_kwargs={
        "task": "transcribe",
        "language": "en"
    }
)

# === Helper Functions ===
_speak_lock = threading.Lock()

def speak(text):
    """Thread-safe TTS"""
    with _speak_lock:
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS ERROR] {e}")


def transcribe_from_mic(duration=10):
    fs = 16000
    print("🎤 Listening...")

    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        wav.write(temp_wav.name, fs, recording)
        result = asr_model(temp_wav.name)

    text = result["text"].strip().lower()
    print(f"🗣 Recognized: {text}")

    # if len(text.split()) <= 2:
    #     print("⚠️ Ignored low-confidence result:", text)
    #     return ""
    
    UNWANTED_PHRASES = [
    "please type your message here.",
    "type your message here.",
    "your message here.",
    "message here.",
    "thank you.",
    "thanks.",
    ]

    if text in UNWANTED_PHRASES:
        print("⚠️ Ignored unwanted phrase:", text)
        return ""


    return text

# === Voice Command Handler ===
def handle_voice_command(command: str):
    """Parse spoken commands and trigger global gaze toggle."""
    from app import App  # import here to avoid circular imports
    from frontend.pages.home import pause_gaze_control, resume_gaze_control

    cmd = command.lower().strip()

    try:
        app = App._instance  # get running app instance
    except:
        app = None

    # ========== START GAZE CONTROL ==========
    if "start gaze control" in cmd:
        print("[VOICE] Triggered: Start gaze control")
        speak("Starting gaze control")

        try:
            from frontend.pages.home import start_mouse_control
            start_mouse_control()
        except Exception as e:
            print("[VOICE ERROR] Failed to start mouse control:", e)

        return True


    # ========== STOP GAZE CONTROL ==========
    elif "stop gaze control" in cmd:
        print("[VOICE] Triggered: Stop gaze control")
        speak("Stopping gaze control")

        try:
            from frontend.pages.home import launch_gaze_app
            launch_gaze_app(enable_mouse_control=False)
        except Exception as e:
            print("[VOICE ERROR] Failed to stop mouse control:", e)

        return True





# === Background Voice Listener ===
def listen_for_gaze_commands():
    """Continuously listens for 'start gaze control' or 'stop gaze control'."""
    print("[VOICE] Listening thread started — awaiting voice commands...")
    speak("Voice control activated. You can say start gaze control or stop gaze control.")

    while True:
        try:
            command = transcribe_from_mic()
            if not command:
                continue

            handled = handle_voice_command(command)
            if not handled:
                print("[VOICE] No matching command.")
        except KeyboardInterrupt:
            print("[VOICE] Listener stopped by user.")
            break
        except Exception as e:
            print(f"[VOICE ERROR] {e}")
            time.sleep(2)

# === Start listener in background thread (if imported into app) ===
def start_voice_listener_thread():
    threading.Thread(target=listen_for_gaze_commands, daemon=True).start()
