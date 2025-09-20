import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import tempfile
import time
import pyautogui
import webbrowser
import os
import pyttsx3

# Load Whisper model
model = whisper.load_model("base")  # or "small" for better results

# Zoom meeting invite URL
ZOOM_MEETING_URL = "https://us05web.zoom.us/j/86178818611?pwd=8haoz2Xi6r1kaAIz281b460gryYbtb.1"

# === Helper functions ===
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def record_audio(duration=6, fs=16000):
    # speak("Speak now")
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    print("Recording complete.")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(temp_file.name, fs, recording)
    return temp_file.name

def transcribe_command(audio_path):
    result = model.transcribe(audio_path)
    return result["text"].strip().lower()

def execute_voice_command(command):
    print("Transcribed Command:", command)

    if "open zoom" in command:
        speak("Opening Zoom meeting")
        webbrowser.open(ZOOM_MEETING_URL)
        time.sleep(10)  # wait for browser to open

        # Gaze + Blink simulation mode (step control flags)
        return "awaiting_zoom_popup"
    
    elif "open powerpoint" in command:
        speak("Opening PowerPoint")
        os.startfile(r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE")
        time.sleep(3)  # wait for PowerPoint to open
        pyautogui.press('enter')
        time.sleep(2) 
        pyautogui.press('tab')
    
    elif "open media player" in command:
        speak("Opening Media Player")
        # os.startfile(r"shell:AppsFolder\\Microsoft.ZuneMusic_8wekyb3d8bbwe!Microsoft.ZuneMusic")
        os.system('start powershell "Start-Process shell:AppsFolder\\Microsoft.ZuneMusic_8wekyb3d8bbwe!Microsoft.ZuneMusic"')
        time.sleep(5)  # wait for PowerPoint to open
        # pyautogui.press('tab')
        # pyautogui.press('tab')
        
    elif "open snake game" in command:
        speak("Opening Snake vs Fruit")
        os.startfile(r"C:\Users\DELL\OneDrive\Desktop\Snake Vs Fruits - Shortcut.lnk")
        pyautogui.press('tab')
        pyautogui.press('tab')
        pyautogui.press('enter')

    elif "open whatsapp" in command:
        speak("Opening WhatsApp")
        os.system('start powershell "Start-Process shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"')
        
    elif "open file explorer" in command or "open folder" in command:
        speak("Opening File Explorer")
        os.system('start explorer')
        time.sleep(2)  # wait for File Explorer to open
        pyautogui.press('down')

    elif "open youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
        time.sleep(6)
        pyautogui.press('/')
        time.sleep(1)
        query_audio = record_audio()
        query = transcribe_command(query_audio)
        pyautogui.typewrite(query, interval=0.05)
        pyautogui.press('enter')

    elif "close window" in command:
        pyautogui.hotkey('alt', 'f4')

    # else:
        # speak("Sorry, I didn't understand the command.")

    return None



# === Main Loop ===
if __name__ == "__main__":
    while True:
        audio_path = record_audio()
        result = transcribe_command(audio_path)

        if any(kw in result for kw in ["exit", "stop"]):
            speak("Exiting voice control")
            break

        step = execute_voice_command(result)

        # Example control flow flag you can feed into your gaze system
        if step == "awaiting_zoom_popup":
            speak("Please look left or right to select, then blink to confirm.")
            
            
            
