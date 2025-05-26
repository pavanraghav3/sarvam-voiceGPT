import React, { useState, useRef } from "react";
import axios from "axios";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  audio?: string; // Optional base64 audio string
}

interface VoiceRecorderProps {
  chatId: string | null;
  onNewMessages: (userMsg: Message, assistantMsg: Message) => void;
  disabled?: boolean;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ chatId, onNewMessages, disabled = false }) => {
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const startRecording = async () => {
    if (disabled) return;
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
    if (chatId) formData.append("chat_id", chatId);

    try {
      const response = await axios.post(
        "http://localhost:5000/process-voice",
        formData
      );
      const data = response.data;

      // Build message objects with audio
      const userMsg: Message = {
        role: "user",
        content: data.userText,
        timestamp: new Date().toISOString(),
        audio: data.userAudio, // <-- include user audio
      };
      const assistantMsg: Message = {
        role: "assistant",
        content: data.responseText,
        timestamp: new Date().toISOString(),
        audio: data.responseAudio, // <-- include assistant TTS audio
      };

      // Update chat in parent
      onNewMessages(userMsg, assistantMsg);

      // Play assistant's audio
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
      <div className="voice-btn-center">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing || disabled}
          className={`voice-btn ${isRecording ? "recording" : ""}`}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>
        {isRecording && <div className="recording-sign">Recording...</div>}
        {isProcessing && <p>Processing your request...</p>}
      </div>
      <audio ref={audioRef} style={{ display: "none" }} />
    </div>
  );
};

export default VoiceRecorder;
