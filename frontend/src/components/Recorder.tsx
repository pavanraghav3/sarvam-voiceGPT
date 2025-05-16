import React from "react";
import { AudioRecorder } from "react-audio-voice-recorder";

const Recorder = () => {
  const sendAudioToBackend = async (blob: Blob) => {
    const formData = new FormData();
    formData.append("audio", blob);
    formData.append("language", "en"); // or dynamically set this from UI

    try {
      const response = await fetch("http://localhost:5000/api/voice-chat", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      console.log("Transcription and Response:", data);

      // You can display `data.bot_text_local`, `data.user_text`, etc., in your UI
      const audio = new Audio(data.bot_audio_url);
      audio.play();
    } catch (error) {
      console.error("Error sending audio to backend:", error);
    }
  };

  return (
    <div>
      <h2>Record your voice</h2>
      <AudioRecorder
        onRecordingComplete={sendAudioToBackend}
        audioTrackConstraints={{
          noiseSuppression: true,
          echoCancellation: true,
        }}
        downloadOnSavePress={false}
        showVisualizer={true}
      />
    </div>
  );
};

export default Recorder;
