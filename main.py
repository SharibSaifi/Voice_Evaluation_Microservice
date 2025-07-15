from fastapi import FastAPI, UploadFile, File, HTTPException
import requests
import time

app  =  FastAPI()

# API Key from AssemblyAI
API_KEY  =  "d236abc849a64c74b039ccbd2747bdd5"

# Headers used when making requests to AssemblyAI
HEADER  =  {
    "authorization" : API_KEY,
    "content-type" : "application/json"
}

# Set a minimum confidence level for correct pronunciation
MIN_CONFIDENCE  =  0.85

# Simple home page
@app.get("/")
def root():
    return {"message":"Welcome to the Voice Evaluation Application"}

# Main endpoint to handle transcription and analysis
@app.post("/transcribe")
async def voice_evaluation(file: UploadFile  =  File(...)):
    # Step 1: Check if uploaded file is an audio file
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code = 400, detail = "Please upload a valid audio file (.mp3 or .wav).")

    try:
        # Step 2: Upload the audio file to AssemblyAI
        audio_raw_data  =  await file.read()
        upload_response  =  requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers  =  {
                "authorization": API_KEY
            },
            data  =  audio_raw_data
        )

        if upload_response.status_code !=   200:
            raise HTTPException(status_code  =  500, detail  =  "Audio upload failed.")

        audio_response_url  =  upload_response.json()["upload_url"]

        # Step 3: Request transcription with punctuation and formatting
        transcription_request  =  {
            "audio_url": audio_response_url,
            "punctuate": True,
            "format_text": True,
            "language_code": "en_us"
        }

        transcription_response  =  requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers = HEADER,
            json = transcription_request
        )

        if transcription_response.status_code !=   200:
            raise HTTPException(status_code = 500, detail = "Transcription request failed.")

        transcript_id  =  transcription_response.json()["id"]
        poll_url  =  f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

        # Step 4: Poll AssemblyAI until the transcription is ready
        while True:
            polling_response  =  requests.get(poll_url, headers = HEADER)
            result  =  polling_response.json()

            if result["status"]  ==  "completed":
                break
            elif result["status"]  ==  "error":
                raise HTTPException(status_code = 500, detail = "Transcription failed.")

            time.sleep(2)  # Wait 2 seconds before polling again

        words_data  =  result.get("words", [])
        words  =  []

        for txt in words_data :
            words.append({
                "word": txt["text"],
                "start": txt["start"] / 1000, # Convert ms to seconds
                "end": txt["end"] / 1000, # Convert ms to seconds
                "confidence": txt["confidence"] 
            })

        if not words:
            raise HTTPException(status_code=400, detail="No words found in audio.")

        audio_duration  =  words[-1]["end"] # Duration = end time of last word

        # Step 6: Pronunciation analysis
        confidences  =  [txt["confidence"] for txt in words]
        average_score  =  sum(confidences) / len(confidences)
        pronunciation_score  =  round(average_score * 100)

        # Collect mispronounced words
        mispronounced_words  =  [
            {
                "word": txt["word"],
                "start": txt["start"],
                "end": txt["end"],
                "confidence": txt["confidence"]
            }
            for txt in words if txt["confidence"] < MIN_CONFIDENCE
        ]

        # Step 7: Calculate speaking pace (words per minute)
        total_words  =  len(words)
        if audio_duration > 0:
            WPM = round((total_words / audio_duration) * 60)
        else:
            WPM = 0

        # Give feedback based on pace
        if WPM < 90:
            pace_feedback  =  "Too slow."
        elif WPM > 150:
            pace_feedback  =  "Too fast."
        else:
            pace_feedback  =  "Your speaking pace is appropriate."

        # Step 8: Detect pauses and long pauses
        pause_count = 0
        total_pause_duration = 0.0
        pause_durations = []       
        long_pauses = []          

        for i in range(1, total_words):
            prev_word = words[i - 1]
            curr_word = words[i]
            pause = curr_word["start"] - prev_word["end"]

            # Detect pauses longer than 0.5 seconds between words
            if pause > 0.5:
                pause_count += 1
                total_pause_duration += pause
                pause_durations.append(round(pause, 2))

                # Detect long pauses (e.g., > 1.0 sec)
                if pause > 1.0:
                    long_pauses.append(
                        f"Pause of {pause:.2f}s between '{prev_word['word']}' and '{curr_word['word']}'"
                    )

        # Give pause feedback
        if pause_count >=  5 or total_pause_duration > 5:
            pause_feedback  =  "Try to improve fluency as too many or long pauses detected."
        elif pause_count >=  2:
            pause_feedback  =  "Try to reduce pauses to improve fluency."
        else:
            pause_feedback  =  "You maintained good fluency with few or no pauses."

        # Step 9: Natural language summary
        Final_Feedback  =  []

        if WPM < 90:
            Final_Feedback.append("You spoke a bit slowly.")
        elif WPM > 150:
            Final_Feedback.append("You spoke a bit fast.")
        else:
            Final_Feedback.append("You spoke at a good pace.")

        if mispronounced_words:
            unclear_words  =  ", ".join(txt["word"] for txt in mispronounced_words)
            Final_Feedback.append(f"Focus on pronouncing {unclear_words}. ")
        else:
            Final_Feedback.append("Your pronunciation was generally clear.")

        if pause_count >=  2:
            Final_Feedback.append("Try to reduce long pauses for smoother speech.")
        else:
            Final_Feedback.append("Your fluency was good with few or no pauses.")

        # Final feedback
        feedback  =  " ".join(Final_Feedback)

        # Step 10: Detect Filler Words
        FILLER_WORDS = {"um", "uh", "like", "you know", "so", "actually", "basically", "right", "i mean", "well"}
        transcript_text = result.get("text", "").lower()
        spoken_words = transcript_text.split()

        filler_counts = {}
        total_filler_count = 0

        for word in spoken_words:
            word_clean = word.strip(",.?!")  # Remove punctuation
            if word_clean in FILLER_WORDS:
                filler_counts[word_clean] = filler_counts.get(word_clean, 0) + 1
                total_filler_count += 1

        # Filler usage percentage
        filler_percentage = round((total_filler_count / len(spoken_words)) * 100, 2) if spoken_words else 0

        if filler_percentage > 40:
            filler_words_feedback = "Your current speech pattern shows High usage of filler words, which may significantly affect how your message is received."

        elif filler_percentage > 25:
            filler_words_feedback = "Filler words are showing up often to potentially distract from your message. Consider pausing instead of inserting Filler words."

        elif filler_percentage > 10:
            filler_words_feedback = "There's some use of filler words, which is natural in conversation. With a bit more practice, you can polish your speaking flow."

        else:
            filler_words_feedback = "Excellent job! Your speech is clear and concise with minimal reliance on filler words. You’re maintaining strong verbal control."

        # Step 12: Return final result
        return {
            "Transcripted_audio": result.get("text", ""),
            "Words": words,
            "Audio_duration_in_seconds": audio_duration,
            "Pronunciation_score": pronunciation_score,
            "Mispronounced_words": mispronounced_words,
            "Words_per_minute": WPM,
            "Pace_feedback": pace_feedback,
            "Pause_count": pause_count,
            "Pause_durations": pause_durations,
            "Long_pauses_more_than_a_second": long_pauses,         
            "Total_pause_duration_in_seconds": round(total_pause_duration, 2),
            "Pause_feedback": pause_feedback,
            "Filler_words_used": filler_counts,
            "Total_filler_word_count": total_filler_count,
            "Filler_word_percentage": filler_percentage,
            "Feedback_of_using_filler_words" : filler_words_feedback,
            "Final_feedback": feedback
        }

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code = 500, detail = "An unexpected error occurred during processing of the audio file.")