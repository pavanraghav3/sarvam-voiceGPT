import React, { useEffect, useState } from "react";
import axios from "axios";
import ChatSidebar from "./components/ChatSidebar.tsx";
import ChatWindow from "./components/ChatWindow.tsx";
import VoiceRecorder from "./VoiceRecorder.tsx";
import "./App.css";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  audio?: string;
}

interface Chat {
  _id: string;
  created_at: string;
  messages?: Message[];
}

const App: React.FC = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch all chats on mount
  useEffect(() => {
    axios.get("http://localhost:5000/chats").then((res) => {
      setChats(res.data.reverse()); // newest first
      if (res.data.length > 0) setSelectedChatId(res.data[0]._id);
    });
  }, []);

  // Fetch messages when chat changes
  useEffect(() => {
    if (selectedChatId) {
      axios.get(`http://localhost:5000/chats/${selectedChatId}`).then((res) => {
        setMessages(res.data.messages || []);
      });
    }
  }, [selectedChatId]);

  const handleSelectChat = (chatId: string) => {
    setSelectedChatId(chatId);
  };

  const handleNewChat = () => {
    axios.post("http://localhost:5000/chats").then((res) => {
      setChats((prev) => [
        { _id: res.data.chat_id, created_at: new Date().toISOString() },
        ...prev,
      ]);
      setSelectedChatId(res.data.chat_id);
      setMessages([]);
    });
  };

  const handleDeleteChat = (chatId: string) => {
    axios.delete(`http://localhost:5000/chats/${chatId}`).then(() => {
      setChats(prev => prev.filter(chat => chat._id !== chatId));
      if (selectedChatId === chatId) {
        // Select another chat or clear messages
        if (chats.length > 1) {
          const nextChat = chats.find(chat => chat._id !== chatId);
          setSelectedChatId(nextChat?._id || null);
          setMessages([]);
        } else {
          setSelectedChatId(null);
          setMessages([]);
        }
      }
    });
  };

  // Callback for new messages from VoiceRecorder
  const handleNewMessages = (userMsg: Message, assistantMsg: Message) => {
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
  };

  // Disable VoiceRecorder if no chat is selected
  const hasActiveChat = !!selectedChatId;

  return (
    <div className="app-container dark-theme">
      <ChatSidebar
        chats={chats}
        selectedChatId={selectedChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />
      <div className="main-chat-area">
        <ChatWindow messages={messages} />
        <VoiceRecorder
          chatId={selectedChatId}
          onNewMessages={handleNewMessages}
          disabled={!hasActiveChat}
        />
        {!hasActiveChat && (
          <div className="no-chat-message" style={{
            textAlign: "center",
            color: "#aaa",
            marginTop: "16px",
            fontSize: "1.1em"
          }}>
            No chats available. Click <b>New Chat</b> to start a conversation.
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
