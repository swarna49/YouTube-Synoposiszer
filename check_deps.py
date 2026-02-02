
try:
    import flask
    print("flask installed")
except ImportError:
    print("flask NOT installed")

try:
    import youtube_transcript_api
    print("youtube_transcript_api installed")
except ImportError:
    print("youtube_transcript_api NOT installed")

try:
    import transformers
    print("transformers installed")
except ImportError:
    print("transformers NOT installed")

try:
    import yt_dlp
    print("yt_dlp installed")
except ImportError:
    print("yt_dlp NOT installed")

try:
    import whisper
    print("whisper installed")
except ImportError:
    print("whisper NOT installed")

try:
    import deep_translator
    print("deep_translator installed")
except ImportError:
    print("deep_translator NOT installed")
