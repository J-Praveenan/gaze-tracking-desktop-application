# Voice/voice_autodictation.py
import threading, time, winsound, pyautogui, pyperclip, keyboard
import uiautomation as uia
import pyttsx3

# reuse your local Whisper pipeline
from voice.transcription import transcribe_from_mic  # duration=5 by default

# ---- Tunables ----
SPEAK_PROMPT_TEXT = "Please speak your message."
LISTEN_DURATION_SEC = 5            # mic record duration for Whisper
DEBOUNCE_SEC = 2.0                 # avoid re-trigger loops when focus flickers
PASTE_DELAY_SEC = 0.05             # tiny delay before Ctrl+V

# Internal state
_last_trigger_ts = 0.0
_last_runtime_guard = 0.0
_engine = None
_handler_added = False
_lock = threading.Lock()

def _tts():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        # make it a bit faster, optional:
        rate = _engine.getProperty('rate')
        _engine.setProperty('rate', int(rate * 1.05))
    return _engine

def _is_text_input(ctrl: uia.Control):
    if not ctrl:
        return False
    # Typical editable controls: Edit, Document (e.g., browser rich editors, chat boxes)
    if ctrl.ControlType not in (uia.ControlType.EditControl, uia.ControlType.DocumentControl):
        return False
    if not ctrl.IsEnabled or not ctrl.IsKeyboardFocusable:
        return False
    return True

def _say(text: str):
    try:
        eng = _tts()
        eng.say(text)
        eng.runAndWait()
    except Exception:
        pass

def _paste_text(text: str):
    # Use clipboard + Ctrl+V for maximum compatibility
    pyperclip.copy(text or "")
    time.sleep(PASTE_DELAY_SEC)
    pyautogui.hotkey('ctrl', 'v')

def _capture_and_type():
    try:
        # 1) prompt (voice)
        _say(SPEAK_PROMPT_TEXT)
        winsound.Beep(1000, 120)

        # 2) mic -> whisper
        text = transcribe_from_mic(duration=LISTEN_DURATION_SEC)  # uses your offline whisper
        if not text:
            return

        # 3) paste into current field
        _paste_text(text)
        winsound.Beep(1500, 80)

    except Exception as e:
        # optional: log/print
        print("[auto-dictation] error:", e)

def _should_trigger_now():
    global _last_trigger_ts
    now = time.time()
    if (now - _last_trigger_ts) < DEBOUNCE_SEC:
        return False
    _last_trigger_ts = now
    return True

def _on_focus_change(sender, args):
    # Called by UIA thread on *any* focus change
    try:
        ctrl = uia.GetFocusedControl()
        if not _is_text_input(ctrl):
            return

        # Debounce
        if not _should_trigger_now():
            return

        # Run the capture+type in a worker so we don't block UIA
        threading.Thread(target=_capture_and_type, daemon=True).start()

    except Exception as e:
        print("[auto-dictation] focus-handler error:", e)

def start_voice_autodictation():
    """
    Register a global UIA FocusChanged handler.
    Whenever the user focuses a text box (Chrome search bar, Zoom chat box, WhatsApp message box, etc),
    we auto-prompt, record, transcribe, and paste.
    """
    global _handler_added
    with _lock:
        if _handler_added:
            return
        # Prime TTS early so first prompt is quick
        _ = _tts()

        # Add a focus-changed handler
        uia.AddFocusChangedEventHandler(_on_focus_change)
        _handler_added = True
        print("[auto-dictation] Focus listener started.")

        # Optional: also provide a manual hotkey (Ctrl+Shift+.)
        def _manual_trigger():
            if _should_trigger_now():
                threading.Thread(target=_capture_and_type, daemon=True).start()

        keyboard.add_hotkey('ctrl+shift+.', _manual_trigger)
        print("[auto-dictation] Hotkey Ctrl+Shift+. for manual dictation.")

def stop_voice_autodictation():
    global _handler_added
    with _lock:
        if _handler_added:
            try:
                uia.RemoveFocusChangedEventHandler(_on_focus_change)
            except Exception:
                pass
            _handler_added = False
            print("[auto-dictation] Focus listener stopped.")
