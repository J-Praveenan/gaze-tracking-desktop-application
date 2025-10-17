# utils/common.py
import pyttsx3
import threading
import json
from pathlib import Path

# ==========================================================
# Persistent state file
# ==========================================================
BASE_DIR = Path(__file__).resolve().parents[1]  # one level above utils
DATA_DIR = BASE_DIR / "Data"
VOICE_FILE = DATA_DIR / "voice_control.json"

engine_lock = threading.Lock()
video_playing = False
current_speech_thread = None


def _load_voice_settings():
    """Load voice settings from JSON file, or set defaults if missing."""
    DATA_DIR.mkdir(exist_ok=True)
    if VOICE_FILE.exists():
        try:
            with open(VOICE_FILE, "r") as f:
                data = json.load(f)
                return {
                    "voice_tips_enabled": data.get("voice_tips_enabled", True),
                    "voice_action_confirmation": data.get("voice_action_confirmation", True),
                }
        except Exception:
            pass
    # Default if file missing or invalid
    default_data = {
        "voice_tips_enabled": True,
        "voice_action_confirmation": True,
    }
    _save_voice_settings(default_data)
    return default_data


def _save_voice_settings(data):
    """Save the current voice control settings to file."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(VOICE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("⚠️ Failed to save voice_control.json:", e)


# Load at startup
_voice_settings = _load_voice_settings()
voice_tips_enabled = _voice_settings["voice_tips_enabled"]
voice_action_confirmation = _voice_settings["voice_action_confirmation"]


# ==========================================================
# Voice functions
# ==========================================================
def stop_speech():
    """Stop any currently running voice output immediately."""
    global current_speech_thread
    with engine_lock:
        try:
            tmp_engine = pyttsx3.init()
            tmp_engine.stop()
        except Exception:
            pass
    current_speech_thread = None


def speak(text):
    """Speak text asynchronously (fresh engine each time)."""
    global current_speech_thread
    stop_speech()

    def _run():
        with engine_lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 175)
                engine.setProperty('volume', 1.0)
                for v in engine.getProperty('voices'):
                    if "female" in v.name.lower():
                        engine.setProperty('voice', v.id)
                        break
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print("TTS Error:", e)

    t = threading.Thread(target=_run, daemon=True)
    current_speech_thread = t
    t.start()


def speak_if_allowed(text):
    """Speak only if voice tips are enabled and no video is playing."""
    global voice_tips_enabled, video_playing
    print(f"[VoiceTip] enabled={voice_tips_enabled}, video_playing={video_playing}, text={text}")
    if not voice_tips_enabled or video_playing:
        return
    speak(text)


def speak_action_confirmation(text):
    """Speak only if action confirmations are enabled."""
    global voice_action_confirmation, video_playing
    print(f"[VoiceConfirm] enabled={voice_action_confirmation}, video_playing={video_playing}, text={text}")
    if not voice_action_confirmation or video_playing:
        return
    speak(text)


# ==========================================================
# Public helpers for updating settings
# ==========================================================
def set_voice_tips(enabled: bool):
    """Enable/disable voice tips and save to file."""
    global voice_tips_enabled
    voice_tips_enabled = enabled
    _save_voice_settings({
        "voice_tips_enabled": voice_tips_enabled,
        "voice_action_confirmation": voice_action_confirmation
    })


def set_voice_action_confirmation(enabled: bool):
    """Enable/disable voice action confirmation and save to file."""
    global voice_action_confirmation
    voice_action_confirmation = enabled
    _save_voice_settings({
        "voice_tips_enabled": voice_tips_enabled,
        "voice_action_confirmation": voice_action_confirmation
    })
