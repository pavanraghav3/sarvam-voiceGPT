from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import wave
import contextlib
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables first
load_dotenv()

# Add backend directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import modules after setting up paths
from sarvam_api import SarvamAPI
from llm_api import LLM_API

# Initialize Flask app
app = Flask(__name__)
CORS(app)

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
        # Create temporary input/output files (no auto-delete)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_in, \
             tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_out:

            # Write input bytes to temp file
            temp_in.write(input_bytes)
            temp_in.flush()

            # Run FFmpeg command
            result = subprocess.run(
                [
                    'ffmpeg',
                    '-y',  # Overwrite output
                    '-i', temp_in.name,
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    temp_out.name
                ],
                capture_output=True,
                text=True  # Capture stderr as text
            )

            # Check for errors
            if result.returncode != 0:
                print(f"FFmpeg Error (stderr):\n{result.stderr}")
                return None

            # Read converted WAV bytes
            with open(temp_out.name, 'rb') as f:
                return f.read()

    except Exception as e:
        print(f"Conversion failed: {str(e)}")
        return None
    finally:
        # Clean up temporary files
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
    """Basic homepage route"""
    return "<h1>Backend is running</h1><p>Use /process-voice endpoint for voice interactions</p>"

@app.route('/process-voice', methods=['POST'])
def process_voice():
    try:
        print("Request.files:", request.files)
        audio_file = request.files.get('file')
        if audio_file is None:
            return jsonify({"error": "No audio file provided"}), 400

        # Read original file bytes
        original_bytes = audio_file.read()
        audio_file.stream.seek(0)  # Reset stream position

        # Validate WAV format
        if not is_valid_wav(audio_file):
            print("Attempting audio conversion...")
            converted_bytes = convert_to_wav(original_bytes)
            if not converted_bytes:
                return jsonify({"error": "Failed to convert audio to WAV format"}), 400
            # Create new file-like object with converted audio
            audio_file = BytesIO(converted_bytes)
            audio_file.name = "audio.wav"  # Set filename for Sarvam API

        # Hardcode language to Indian English
        language_code = 'en-IN'

        # Process speech-to-text
        audio_file.seek(0)
        stt_response = sarvam_api.speech_to_text(audio_file)
        print("STT Response:", stt_response)

        if "error" in stt_response:
            return jsonify(stt_response), 500

        transcript = stt_response.get("transcript")
        if not transcript:
            return jsonify({"error": "No transcript returned from STT"}), 500

        # Process LLM response
        llm_response = llm_api.get_response(transcript)
        print("LLM Response:", llm_response)

        if isinstance(llm_response, dict) and "error" in llm_response:
            return jsonify(llm_response), 500

        # Process text-to-speech
        audio_base64 = sarvam_api.text_to_speech(llm_response, 'en-IN')
        print("TTS Response:", audio_base64)

        if isinstance(audio_base64, dict) and "error" in audio_base64:
            return jsonify(audio_base64), 500

        return jsonify({
            "userText": transcript,
            "responseText": llm_response,
            "responseAudio": audio_base64,
            "languageCode": language_code
        })

    except Exception as e:
        import traceback
        print("Exception in /process-voice:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
