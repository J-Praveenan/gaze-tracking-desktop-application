import pyttsx3
import pyautogui
import time
import keyboard
from transcription import transcribe_from_mic
import uiautomation as auto
import win32gui

def is_text_field_focused():
    element = auto.GetFocusedControl()
    if element:
        print("Focused ControlTypeName:", element.ControlTypeName)
        return element.ControlTypeName in ["Edit", "Document"]
    return False

def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)

def speak(message):
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()
    

def voice_typing():
    speak("Please type your message here")
    time.sleep(0.5)
    text = transcribe_from_mic(duration=5)
    time.sleep(0.5)
    pyautogui.typewrite(text, interval=0.05)

if __name__ == "__main__":
    print("🟢 Voice Typing Watcher started. Click on any text field to begin (or press ESC to stop)...")
    
    while True:
        if is_text_field_focused():
            print("✅ Native text input focused!")
            voice_typing()
            break
        elif any(app in get_active_window_title() for app in ["Chrome", "WhatsApp", "Zoom", "Google Docs", "Word", "Slack"]):
            print(f"🔎 Typing app active: {get_active_window_title()}")
            voice_typing()
            break
        if keyboard.is_pressed("esc"):
            print("🛑 ESC pressed. Stopping.")
            break
        time.sleep(0.5)
