import re
import os
from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import yt_dlp
import whisper
from deep_translator import GoogleTranslator

# Disable TensorFlow
os.environ["TRANSFORMERS_NO_TF"] = "1"

app = Flask(__name__)

# Supported languages
supported_languages = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "hi": "Hindi",
    "te": "Telugu",
    "mr": "Marathi"
}

# ================= Summarizer =================
class TextSummarizer:
    def __init__(self, model_name="facebook/bart-large-cnn"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.summarizer = pipeline(
            "summarization",
            model=self.model,
            tokenizer=self.tokenizer,
            framework="pt"
        )

    def chunk_text(self, text, max_tokens=1000):
        sentences = text.split(". ")
        chunks, current_chunk = [], []
        total_tokens = 0

        for sentence in sentences:
            tokens = len(self.tokenizer.encode(sentence))
            if total_tokens + tokens <= max_tokens:
                current_chunk.append(sentence)
                total_tokens += tokens
            else:
                if current_chunk:
                    chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                total_tokens = tokens

        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")

        return chunks

    def summarize(self, text, max_length=500, min_length=150):
        chunks = self.chunk_text(text)
        summaries = []

        for chunk in chunks:
            # Explicitly truncate and handle long chunks to prevent index errors
            result = self.summarizer(
                chunk,
                max_length=max_length,
                min_length=min_length,
                truncation=True,
                do_sample=False
            )
            summaries.append(result[0]["summary_text"])

        return " ".join(summaries)

# ================= Translator =================
class TextTranslator:
    def translate(self, text, target_lang):
        return GoogleTranslator(source="auto", target=target_lang).translate(text)

# ================= Helpers =================
def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def download_audio(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{video_id}.%(ext)s",
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    return f"{video_id}.mp3"

def transcribe_audio_whisper(audio_file):
    model = whisper.load_model("tiny")
    result = model.transcribe(audio_file)
    return result["text"]

# ================= Flask Route =================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            video_url = request.form.get("video_url")
            language_choice = request.form.get("language")

            video_id = extract_video_id(video_url)
            if not video_id:
                return render_template(
                    "index.html",
                    error="Invalid YouTube URL",
                    languages=supported_languages
                )

            summarizer = TextSummarizer()

            # ----------------- Transcript Handling -----------------
            text = ""
            try:
                # Try fetching via API first
                try:
                    if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        # Try to find English, then any available manual or auto-generated
                        try:
                            transcript = transcript_list.find_transcript(["en"])
                        except:
                            # Fallback to the first available transcript if English isn't found
                            transcript = next(iter(transcript_list))
                        
                        text = " ".join([t["text"] for t in transcript.fetch()])
                    elif hasattr(YouTubeTranscriptApi, "get_transcript"):
                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                        text = " ".join([t["text"] for t in transcript])
                    else:
                        raise Exception("No transcript API method available")
                
                except Exception as api_err:
                    print(f"Transcript API failed: {api_err}. Falling back to Whisper...")
                    audio_file = download_audio(video_id)
                    text = transcribe_audio_whisper(audio_file)
                    if os.path.exists(audio_file):
                        os.remove(audio_file)

            except Exception as e:
                print(f"All transcription methods failed: {e}")
                raise e

            # ----------------- Summarize -----------------
            summary = summarizer.summarize(text)

            # ----------------- Translate -----------------
            if language_choice != "en":
                translator = TextTranslator()
                summary = translator.translate(summary, language_choice)

            return render_template(
                "index.html",
                summary=summary,
                languages=supported_languages
            )

        except Exception as e:
            return render_template(
                "index.html",
                error=str(e),
                languages=supported_languages
            )

    return render_template("index.html", languages=supported_languages)

# ================= Main =================
if __name__ == "__main__":
    app.run(debug=True)
