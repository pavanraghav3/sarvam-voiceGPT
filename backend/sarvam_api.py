import requests
import os

class SarvamAPI:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.stt_endpoint = "https://api.sarvam.ai/speech-to-text-translate"
        self.tts_endpoint = "https://api.sarvam.ai/text-to-speech"

    def speech_to_text(self, audio_file):
        """Convert speech to text using Sarvam API"""
        headers = {"api-subscription-key": self.api_key}
        
        files = {
            'file': ('audio.wav', audio_file, 'audio/wav'),  # Proper file formatting
            'model': (None, 'saaras:v2'),
            'with_diarization': (None, 'false')
        }

        response = requests.post(
            self.stt_endpoint,
            headers=headers,
            files=files
        )
        
        if response.status_code == 200:
            return response.json()
        return {"error": f"Error: {response.status_code}", "message": response.text}

    def text_to_speech(self, text, language_code="en-IN"):
        """Convert text to speech using Sarvam API"""
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "target_language_code": language_code,
            "speaker": "anushka",
            "pitch": 0,
            "pace": 1.15,
            "loudness": 1.55,
            "speech_sample_rate": 16000,
            "model": "bulbul:v2"
        }

        response = requests.post(
            self.tts_endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json().get("audios", [""])[0]
        return {"error": f"Error: {response.status_code}", "message": response.text}
