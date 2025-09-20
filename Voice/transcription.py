from pathlib import Path
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile

# Step 1: Point to the local Whisper model directory
MODEL_PATH = Path(__file__).resolve().parents[1] / "Voice_Model"

# Step 2: Convert to POSIX-style string to avoid Hugging Face repo ID validation
MODEL_PATH_POSIX = MODEL_PATH.as_posix()

# Step 3: Load the model and processor locally
model = AutoModelForSpeechSeq2Seq.from_pretrained(MODEL_PATH_POSIX, local_files_only=True)
processor = AutoProcessor.from_pretrained(MODEL_PATH_POSIX, local_files_only=True)

# Step 4: Build ASR pipeline using local model
asr_model = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    generate_kwargs={
        "task": "transcribe",   # could also use "translate"
        "language": "en"        # force English transcription
    }
)

# Function to record and transcribe audio from mic
def transcribe_from_mic(duration=5):
    fs = 16000  # Sample rate
    print("Listening. ..")

    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        wav.write(temp_wav.name, fs, recording)
        result = asr_model(temp_wav.name)

    text = result["text"].strip()
    print("Recognized:", text)

    # 🔎 Filter out very short / low-confidence outputs
    if len(text.split()) <= 2:   # e.g. "you", "uh", "ok"
        print("⚠️ Ignored low-confidence result:", text)
        return ""   # return empty so nothing is typed

    return text


