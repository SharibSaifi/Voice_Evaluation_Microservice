# 🎙️ Voice Evaluation Microservice

This microservice processes spoken audio answers and provides structured feedback on:
- ✅ Pronunciation (accuracy & mispronounced words)
- ✅ Pacing (words per minute)
- ✅ Pauses (count, duration, and flagged long pauses)
- ✅ Filler words detection

---

## 🚀 Setup & Run Instructions

### 🔧 Prerequisites
- Python 3.8+
- FastAPI
- Uvicorn
- `requests` library
- AssemblyAI API Key (free signup at https://www.assemblyai.com/)

### 📦 Install Dependencies
```bash
pip install fastapi uvicorn requests python-multipart

🔑 Set Your AssemblyAI API Key

In the Python file (e.g., main.py), replace the placeholder:
API_KEY = "your_assemblyai_api_key_here"

▶️ Run the FastAPI Server

uvicorn main:app --reload
Server will run at: http://localhost:8000

🎧 Sample Audio Files Used

You can use short .mp3 or .wav audio clips of your own voice for testing.

Example test phrases:

"Hello, my name is Sharib. I basically just wanted to say something."
"Good morning everyone. I'm from Delhi Technological University. Thanks a lot.

🧪 Testing API Endpoints

✅ GET /
Returns a welcome message.

✅ POST /transcribe
Uploads audio and returns full analysis report.

⚙️ Form-data field:
file: Upload .wav or .mp3 audio file

📌 Assumptions and Notes

Audio must be in English (en_us) for accurate transcription.
Mispronounced words are based on a confidence threshold (< 0.85) provided by AssemblyAI.

Pacing is measured in words per minute (WPM) and rated against typical speaking ranges:
Slow: < 90 WPM
Normal: 90–150 WPM
Fast: > 150 WPM

Pauses are defined as pauses > 0.5s. Those > 1.0s are defined as Long pauses.

Filler word detection uses a static list (e.g., "basically", "actually", "like", "uh", "um").

API is intended for educational/demo purposes, not production use.

👨‍💻 Author

Sharib
Project: Voice Evaluation API with FastAPI + AssemblyAI
For educational use and API demo submissions
