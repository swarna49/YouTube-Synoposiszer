import re
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import yt_dlp  
import whisper
from googletrans import Translator 
class TextSummarizer:
    def _init_(self, model_name="facebook/bart-large-cnn"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.summarizer = pipeline("summarization", model=self.model, tokenizer=self.tokenizer)
    def chunk_text(self, text, max_length=1024):
        sentences = text.split('. ')
        current_chunk = []
        total_length = 0
        chunks = []
        for sentence in sentences:
            sentence_length = len(self.tokenizer.encode(sentence))
            if total_length + sentence_length <= max_length:
                current_chunk.append(sentence)
                total_length += sentence_length
            else:
                chunks.append(". ".join(current_chunk) + '.')
                current_chunk = [sentence]
                total_length = sentence_length
        if current_chunk:
            chunks.append(". ".join(current_chunk) + '.')
        return chunks
    def summarize(self, text, max_length=1000, min_length=100):  
        chunks = self.chunk_text(text)
        summaries = []
        for chunk in chunks:
            inputs = self.tokenizer(chunk, return_tensors="pt", max_length=1024, truncation=True, padding=True)
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            summaries.append(summary)
        return " ".join(summaries)
class TextTranslator:
    def _init_(self):
        self.translator = Translator()  
    def translate(self, text, dest_language):
        translation = self.translator.translate(text, dest=dest_language)
        return translation.text
def extract_video_id(url):
    video_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(video_id_pattern, url)
    return match.group(1) if match else None
def download_audio(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{video_id}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            audio_file = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return audio_file
    except Exception as e:
        print(f"Error downloading audio: {e}")
        raise
def transcribe_audio_whisper(audio_file):
    try:
        model = whisper.load_model("tiny")  
        result = model.transcribe(audio_file)
        return result["text"]
    except Exception as e:
        print(f"Error transcribing audio with Whisper: {e}")
        raise
url = 'https://youtu.be/n434ha4QwU0?si=DE2L4w6o0JrswaHU'
video_id = extract_video_id(url)
if video_id:
    try:   
        supported_languages = {
            'en': 'English',
            'fr': 'French',
            'es': 'Spanish',
            'hi': 'Hindi',
            'te': 'Telugu',
            'mr': 'Marathi'
        }
        print(f"Supported languages: {', '.join([f'{k} ({v})' for k, v in supported_languages.items()])}")
        language_choice = input("Enter the target language code (e.g., 'en' for English): ").strip()
        if language_choice not in supported_languages:
            raise ValueError("Unsupported language code. Please enter a valid code.")
        summarizer = TextSummarizer()
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            description = ''
            for x in transcript:
                sentence = x['text']
                description += f'{sentence}\n'
        except (TranscriptsDisabled, NoTranscriptFound):
            print("Transcripts are disabled or not available. Downloading audio for transcription...")
            audio_file = download_audio(video_id)
            description = transcribe_audio_whisper(audio_file)
            os.remove(audio_file)  
        summary = summarizer.summarize(description)
        if language_choice == 'en':
            print("Transcript Summary (in English):")
            print(summary)
        else:
            translator = TextTranslator()
            translated_summary = translator.translate(summary, language_choice)
            print(f"Transcript Summary (Translated to {supported_languages[language_choice]}):")
            print(translated_summary)
    except VideoUnavailable:
        print(f"The video with ID: {video_id} is unavailable.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
else:
    print(f"Invalid YouTube URL: {url}")