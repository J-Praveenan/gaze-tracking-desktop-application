import pyttsx3
import pyautogui
import time
import keyboard
from voice.transcription import transcribe_from_mic
import uiautomation as auto
from uiautomation import UIAutomationInitializerInThread
import win32gui

def is_zoom_chat_open():
        root = auto.GetRootControl()
        for win in root.GetChildren():
            try:
                if win.ClassName == "ConfMultiTabContentWndClass":  # Zoom meeting window
                    for child in win.GetChildren():
                        try:
                            print("Child:", child.ControlTypeName, "| Name:", child.Name, "| ClassName:", child.ClassName)
                            if "chat" in (child.Name or "").lower() or "message" in (child.Name or "").lower():
                                return True
                        except Exception:
                            continue  # skip if child is stale
            except Exception:
                continue  # skip if win is stale
        return False


def is_text_field_focused():
    element = auto.GetFocusedControl()
    
    if element:
        
        # Standard text fields
        if element.ControlTypeName in ["Edit", "Document"]:
            return True
        # ✅ Chrome special case: search / address bar
        if element.ControlTypeName in ["EditControl", "ComboBoxControl"] and (
            "search" in element.Name.lower() or "address" in element.Name.lower()
        ):
            return True
        
        
         # Browser case: ChatGPT, Gmail, etc.
        if "chrome" in get_active_window_title().lower() or "edge" in get_active_window_title().lower():
            # Case 1: standard editable elements
            if element.ControlTypeName in ["EditControl", "PaneControl"]:
                return True
            # Case 2: webpage input (ChatGPT typing bar, Gmail body, etc.)
            if element.ControlTypeName == "DocumentControl" and element.ClassName == "Chrome_RenderWidgetHostHWND":
                return True
            
        
        # ✅ Teams chat & participants            
        if "teams" in get_active_window_title().lower():
            if element.ControlTypeName == "EditControl":
                name = (element.Name or "").lower()
                if any(key in name for key in ["type a message", "reply", "message", "type a name", "search"]):
                    return True               
              
        # ✅ Zoom special case: chat / main window
        if is_zoom_chat_open():
            return True
        
        
    # For Testing window and child elements
    root = auto.GetRootControl()
    for win in root.GetChildren():
        try:
            if  get_active_window_title().lower():  # Zoom meeting window
                print("Active Window Title:", get_active_window_title().lower())
                for child in win.GetChildren():
                    try:
                        print("Child:", child.ControlTypeName, "| Name:", child.Name, "| ClassName:", child.ClassName)
                        if "chat" in (child.Name or "").lower() or "message" in (child.Name or "").lower():
                            return True
                    except Exception:
                        continue  # skip if child is stale
        except Exception:
            continue  # skip if win is stale
           
    
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
    text = transcribe_from_mic(duration=3)
    time.sleep(0.5)
    pyautogui.typewrite(text, interval=0.05)
    
    
def run_voice_typing_loop():
    print("🟢 Voice Typing Loop Started...")

    with UIAutomationInitializerInThread():  # ✅ Initialize UIAutomation for this thread
        while True:
            if is_text_field_focused():
                print("✅ Native text input focused!")
                voice_typing()
    
            if keyboard.is_pressed("esc"):
                print("🛑 ESC pressed. Stopping.")
                break

            time.sleep(0.5)                                                                                                                                      
              


if __name__ == "__main__":
    print("🟢 Voice Typing Watcher started. Click on any text field to begin (or press ESC to stop)...")
    
    while True:
        if is_text_field_focused():
            print("✅ Native text input focused!")
            voice_typing()
            break
    
        if keyboard.is_pressed("esc"):
            print("🛑 ESC pressed. Stopping.")
            break
        time.sleep(0.5)


 