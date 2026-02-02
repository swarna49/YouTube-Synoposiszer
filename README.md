# YouTube Synoposiszer 🎥

A powerful web application that generates long, detailed synopses of YouTube videos using AI. It handles transcripts directly when available and falls back to local audio transcription using OpenAI Whisper when they are not.

## Features
- **Detailed Synopses:** Generates long, high-quality summaries using the BART model.
- **Auto-Transcription:** If a video lacks transcripts, it automatically downloads audio and transcribes it using OpenAI Whisper.
- **Multi-language Support:** Translate the summary into English, French, Spanish, Hindi, Telugu, or Marathi.
- **Premium UI:** A clean, modern interface designed for ease of use.
- **Robust Error Handling:** Handles common YouTube API issues like "no element found" or regional restrictions.

## Tech Stack
- **Backend:** Flask (Python)
- **AI Models:** 
  - `facebook/bart-large-cnn` (Summarization)
  - `openai-whisper` (Transcription)
- **APIs/Libraries:** 
  - `youtube-transcript-api`
  - `yt-dlp` (Audio downloading)
  - `deep-translator` (Translation)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/swarna49/YouTube-Synoposiszer.git
   cd YouTube-Synoposiszer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg:**
   Whisper and yt-dlp require FFmpeg to be installed on your system.
   - **Windows:** `choco install ffmpeg` or download from ffmpeg.org
   - **Mac:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg`

4. **Run the app:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

## Important Note
The first time you run a summary, the app will download the BART model (approx. 1.6GB) and the Whisper model. This may take a few minutes depending on your connection.
