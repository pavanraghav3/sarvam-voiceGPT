import React, { useState, useRef } from "react";
import axios from "axios";

const VoiceRecorder: React.FC = () => {
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [userText, setUserText] = useState<string>("");
  const [responseText, setResponseText] = useState<string>("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const startRecording = async () => {
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = handleAudioData;

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);

      // Stop all tracks in the stream
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
    }
  };

  const handleAudioData = async () => {
    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("file", audioBlob);

    try {
      const response = await axios.post(
        "http://localhost:5000/process-voice",
        formData
      );
      const data = response.data;

      setUserText(data.userText);
      setResponseText(data.responseText);

      // Create audio from base64 string
      const audioSrc = `data:audio/wav;base64,${data.responseAudio}`;
      if (audioRef.current) {
        audioRef.current.src = audioSrc;
        audioRef.current.play();
      }
    } catch (error) {
      console.error("Error processing voice:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="voice-recorder-container">
      <h2>Voice Chat Assistant</h2>

      <div className="controls">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={isRecording ? "stop-btn" : "record-btn"}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>

        {isProcessing && <p>Processing your request...</p>}
      </div>

      <div className="conversation">
        {userText && (
          <div className="message user-message">
            <p>
              <strong>You:</strong> {userText}
            </p>
          </div>
        )}

        {responseText && (
          <div className="message assistant-message">
            <p>
              <strong>Assistant:</strong> {responseText}
            </p>
          </div>
        )}
      </div>

      <audio ref={audioRef} style={{ display: "none" }} />
    </div>
  );
};

export default VoiceRecorder;
