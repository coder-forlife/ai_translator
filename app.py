from flask import Flask, render_template, request, redirect, url_for
from openai import OpenAI
import os
import time
import tempfile

app = Flask(__name__)


api_key = open("API_KEY.txt", "r").read().strip()
client = OpenAI(api_key=api_key)

transcription_text = ""

@app.route("/audio_to_text", methods=["GET", "POST"])
def audio_to_text_post():
    global transcription_text
    
    if request.method == "POST":
        audio_file = request.files.get("audio_file")
        if audio_file:
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    audio_file.save(tmp.name)
                    
                   
                    with open(tmp.name, "rb") as af:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=af
                        )
                    transcription_text = transcript.text
            except Exception as e:
                transcription_text = f"Error: {str(e)}"
        else:
            transcription_text = "No file uploaded."
            
    return render_template("index.html", transcript_text=transcription_text)


@app.route("/translate", methods=["POST"])
def translate():
    if request.method == "POST":
        text = request.form.get("transcript_text")    
        target_language = request.form.get("language")  

        # 3. Updated ChatCompletion Syntax
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a translator. Translate the given text to {target_language}. Return only the translated text, nothing else."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        translated_text = response.choices[0].message.content

        print("Original:   ", text)
        print("Language:   ", target_language)
        print("Translated: ", translated_text)

        return render_template("index.html",
                               transcript_text=text,
                               translated_text=translated_text,
                               language=target_language)
                               

@app.route("/audio_generate", methods=["POST"])
def generate_audio():
    if request.method == "POST":
        transcripttxt = request.form.get("transcript_text")
        text          = request.form.get("translated_text")
        voice_name    = request.form.get("agent")

        
        filename   = f"speech_{int(time.time())}.mp3"
        audio_path = os.path.join("static", "audio", filename)

        
        os.makedirs(os.path.join("static", "audio"), exist_ok=True)

        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice_name,
                input=text
            )

            
            response.stream_to_file(audio_path)
            print(f"Success! Audio saved: {audio_path}")

        except Exception as e:
            print(f"Error: {e}")
            filename = None

    return render_template("index.html",
                           transcript_text=transcripttxt,
                           translated_text=text,
                           audio_file=filename,
                           selected_agent=voice_name)  

if __name__ == "__main__":
    app.run(debug=True)
