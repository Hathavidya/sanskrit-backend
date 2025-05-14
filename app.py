
import os
from flask import Flask, request, jsonify
from google.cloud import speech
from pydub import AudioSegment
import tempfile

app = Flask(__name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "civic-origin-451606-c9-67f5030ed1b4.json"
client = speech.SpeechClient()

def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=44100,
        language_code="hi-IN"
    )
    response = client.recognize(config=config, audio=audio)
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript
    return transcript

def calculate_match(expected, actual):
    expected = expected.strip().lower()
    actual = actual.strip().lower()
    return 100 if expected in actual else 0

@app.route("/transcribe", methods=["POST"])
def handle_transcription():
    if 'audio' not in request.files or 'expected' not in request.form:
        return jsonify({'error': 'Missing audio or expected text'}), 400
    audio_file = request.files['audio']
    expected = request.form['expected']
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_webm:
        audio_file.save(temp_webm.name)
    temp_flac = tempfile.NamedTemporaryFile(suffix=".flac", delete=False)
    AudioSegment.from_file(temp_webm.name).export(temp_flac.name, format="flac")
    transcript = transcribe_audio(temp_flac.name)
    score = calculate_match(expected, transcript)
    return jsonify({ "transcript": transcript, "matchPercent": score })
