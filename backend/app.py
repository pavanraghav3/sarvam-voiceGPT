from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import wave
import contextlib
import subprocess
import tempfile
import base64
import datetime
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO
from chat_routes import chat_bp
from db import create_new_chat, add_message_to_chat
from sarvam_api import SarvamAPI
from llm_api import LLM_API

# Load environment variables first
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.register_blueprint(chat_bp)

# ------ Helper Functions ------
def is_valid_wav(file_storage):
    """Validate if uploaded file is a proper WAV file"""
    try:
        file_storage.stream.seek(0)
        data = file_storage.read()
        buffer = BytesIO(data)
        with contextlib.closing(wave.open(buffer, 'rb')) as f:
            return True
    except Exception as e:
        print(f"Invalid WAV file: {str(e)}")
        return False
    finally:
        file_storage.stream.seek(0)

def convert_to_wav(input_bytes):
    """Convert audio bytes to WAV using ffmpeg with detailed error logging."""
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_in, \
             tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_out:

            temp_in.write(input_bytes)
            temp_in.flush()

            result = subprocess.run(
                [
                    'ffmpeg',
                    '-y',
                    '-i', temp_in.name,
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    temp_out.name
                ],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"FFmpeg Error (stderr):\n{result.stderr}")
                return None

            with open(temp_out.name, 'rb') as f:
                return f.read()

    except Exception as e:
        print(f"Conversion failed: {str(e)}")
        return None
    finally:
        if 'temp_in' in locals():
            os.unlink(temp_in.name)
        if 'temp_out' in locals():
            os.unlink(temp_out.name)

# ------ Configuration ------
print("="*40)
print(f"Sarvam API Key: {os.getenv('SARVAM_API_KEY')}")
print(f"OpenAI API Key: {os.getenv('OPENAI_API_KEY')}")
print("="*40)

# Initialize APIs
sarvam_api = SarvamAPI()
llm_api = LLM_API()

# ------ Routes ------
@app.route('/')
def home():
    return "<h1>Backend is running</h1><p>Use /process-voice endpoint for voice interactions</p>"

@app.route('/process-voice', methods=['POST'])
def process_voice():
    try:
        audio_file = request.files.get('file')
        if not audio_file:
            return jsonify({"error": "No audio file provided"}), 400

        chat_id = request.form.get('chat_id') or create_new_chat()
        print(f"🚀 Using chat: {chat_id}")

        # Process audio file
        original_bytes = audio_file.read()
        audio_file.stream.seek(0)

        # Convert to WAV if needed
        if not is_valid_wav(audio_file):
            print("Attempting audio conversion...")
            converted_bytes = convert_to_wav(original_bytes)
            if not converted_bytes:
                return jsonify({"error": "Conversion failed"}), 400
            audio_file = BytesIO(converted_bytes)
            audio_file.name = "audio.wav"

        # Get user audio for storage
        audio_file.seek(0)
        user_audio_bytes = audio_file.read()
        user_audio_base64 = base64.b64encode(user_audio_bytes).decode('utf-8')

        # Speech-to-text
        audio_file.seek(0)
        stt_response = sarvam_api.speech_to_text(audio_file)
        if "error" in stt_response:
            return jsonify(stt_response), 500

        transcript = stt_response.get("transcript")
        if not transcript:
            return jsonify({"error": "No transcript returned"}), 500

        # Store user message with audio
        add_message_to_chat(chat_id, "user", {
            "text": transcript,
            "audio": user_audio_base64,
            "timestamp": datetime.datetime.utcnow()
        })

        # Get LLM response
        llm_response = llm_api.get_response(transcript)
        if isinstance(llm_response, dict) and "error" in llm_response:
            return jsonify(llm_response), 500

        # Store assistant response
        add_message_to_chat(chat_id, "assistant", {
            "text": llm_response,
            "timestamp": datetime.datetime.utcnow()
        })

        # Text-to-speech with detected language
        language_code = stt_response.get("language_code", "en-IN")
        tts_response = sarvam_api.text_to_speech(llm_response, language_code)
        if isinstance(tts_response, dict) and "error" in tts_response:
            return jsonify(tts_response), 500

        return jsonify({
            "chatId": chat_id,
            "userText": transcript,
            "userAudio": user_audio_base64,
            "responseText": llm_response,
            "responseAudio": tts_response,
            "languageCode": language_code
        })

    except Exception as e:
        print(f"Exception in /process-voice: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
