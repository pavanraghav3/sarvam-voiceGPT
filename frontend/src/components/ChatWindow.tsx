import React, { useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string | { text: string }; // allow string or object
  timestamp: string;
  audio?: string; // optional base64 audio string
}

interface ChatWindowProps {
  messages: Message[];
}

// Helper function to extract text from content
function getMessageText(content: string | { text: string }) {
  if (typeof content === "object" && content !== null) {
    return content.text || "";
  }
  return content;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages }) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-window">
      {messages.map((msg, idx) => (
        <div key={idx} className={`chat-message ${msg.role}`}>
          <div className="chat-bubble">
            <span>{getMessageText(msg.content)}</span>
            {msg.audio && (
              <audio controls style={{ width: "100%", marginTop: 6 }}>
                <source src={`data:audio/wav;base64,${msg.audio}`} type="audio/wav" />
                Your browser does not support the audio element.
              </audio>
            )}
            <div className="chat-timestamp">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
};

export default ChatWindow;
