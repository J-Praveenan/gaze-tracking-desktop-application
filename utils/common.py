# utils/common.py
import pyttsx3
import threading
import json
from pathlib import Path

# ==========================================================
# Unified Configuration File
# ==========================================================
BASE_DIR = Path(__file__).resolve().parents[1]  # one level above utils
DATA_DIR = BASE_DIR / "Data"
CONFIG_FILE = DATA_DIR / "configuration.json"

engine_lock = threading.Lock()
video_playing = False
current_speech_thread = None


# ==========================================================
# Helpers: Load & Save Configuration
# ==========================================================
def _load_config():
    """Load the unified configuration file, creating defaults if missing."""
    DATA_DIR.mkdir(exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # Default structure
    default = {
        "reminder": {"enabled": False, "duration": 10},
        "voice": {"tips_enabled": True, "action_confirmation": True},
        "tray": {"enabled": False},
        "camera": {"index": 0}
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(default, f, indent=4)

    return default


def _save_config(data):
    """Save entire configuration back to configuration.json."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("⚠️ Failed to save configuration.json:", e)


# ==========================================================
# Load Voice Settings at Startup
# ==========================================================
_config = _load_config()
voice_tips_enabled = _config.get("voice", {}).get("tips_enabled", True)
voice_action_confirmation = _config.get("voice", {}).get("action_confirmation", True)


# ==========================================================
# Voice Engine Functions
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
                engine.setProperty("rate", 175)
                engine.setProperty("volume", 1.0)
                for v in engine.getProperty("voices"):
                    if "female" in v.name.lower():
                        engine.setProperty("voice", v.id)
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
# Update Voice Settings (Persist in configuration.json)
# ==========================================================
def set_voice_tips(enabled: bool):
    """Enable/disable voice tips and save to unified configuration."""
    global voice_tips_enabled, _config
    voice_tips_enabled = enabled
    _config["voice"]["tips_enabled"] = enabled
    _save_config(_config)
    print(f"[CONFIG] Voice Tips set to: {enabled}")


def set_voice_action_confirmation(enabled: bool):
    """Enable/disable voice confirmations and save to unified configuration."""
    global voice_action_confirmation, _config
    voice_action_confirmation = enabled
    _config["voice"]["action_confirmation"] = enabled
    _save_config(_config)
    print(f"[CONFIG] Voice Action Confirmation set to: {enabled}")
