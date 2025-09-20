# realtime_voice_typing.py
import queue
import sounddevice as sd
import numpy as np
import pyautogui
import threading
import time
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pathlib import Path

# Load Whisper model locally
MODEL_PATH = Path(__file__).resolve().parents[1] / "Voice_Model"
model = AutoModelForSpeechSeq2Seq.from_pretrained(MODEL_PATH.as_posix(), local_files_only=True)
processor = AutoProcessor.from_pretrained(MODEL_PATH.as_posix(), local_files_only=True)

asr = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor
)

# --- Audio Queue ---
q = queue.Queue()
samplerate = 16000
blocksize = 1024   # ~64ms per block

def audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    q.put(indata.copy())

# --- Worker Thread ---
def transcriber_loop():
    buffer = np.zeros(0, dtype=np.int16)
    last_text = ""

    while True:
        try:
            block = q.get()
            buffer = np.concatenate((buffer, block.flatten()))

            # keep last ~3s of audio
            if len(buffer) > samplerate * 3:
                buffer = buffer[-samplerate * 3:]

            # run transcription every 1s
            if q.qsize() == 0:
                result = asr(buffer, chunk_length_s=3)
                text = result["text"].strip()

                # find what’s new
                if text.startswith(last_text):
                    new_part = text[len(last_text):]
                else:
                    new_part = text

                if new_part.strip():
                    print("Typing:", new_part)
                    pyautogui.typewrite(new_part + " ", interval=0.02)

                last_text = text
        except Exception as e:
            print("Error:", e)
            time.sleep(0.5)

# --- Main ---
def start_realtime_typing():
    threading.Thread(target=transcriber_loop, daemon=True).start()
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=samplerate, blocksize=blocksize, dtype='int16'):
        print("🎤 Real-time dictation started. Press Ctrl+C to stop.")
        while True:
            time.sleep(0.1)

if __name__ == "__main__":
    start_realtime_typing()
