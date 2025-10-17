import pyttsx3
import threading

engine_lock = threading.Lock()
voice_tips_enabled = True
video_playing = False
current_speech_thread = None


def stop_speech():
    """Stop any currently running voice output immediately."""
    global current_speech_thread
    with engine_lock:
        try:
            # create temporary engine to send stop signal safely
            tmp_engine = pyttsx3.init()
            tmp_engine.stop()
        except Exception:
            pass
    current_speech_thread = None


def speak(text):
    """Speak text asynchronously (fresh engine each time)."""
    global current_speech_thread
    stop_speech()  # 🛑 stop any ongoing speech

    def _run():
        with engine_lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 175)
                engine.setProperty('volume', 1.0)
                voices = engine.getProperty('voices')
                # choose female voice if available
                for v in voices:
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
