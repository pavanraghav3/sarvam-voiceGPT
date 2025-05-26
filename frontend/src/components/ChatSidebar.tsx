import React from "react";

interface ChatSidebarProps {
  chats: { _id: string; created_at: string }[];
  selectedChatId: string | null;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  chats,
  selectedChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
}) => {
  return (
    <div className="sidebar">
      <button className="new-chat-btn" onClick={onNewChat}>
        + New Chat
      </button>
      <div className="chat-list">
        {chats.map((chat) => (
          <div
            key={chat._id}
            className={`chat-list-item ${
              selectedChatId === chat._id ? "selected" : ""
            }`}
            onClick={() => onSelectChat(chat._id)}
            style={{ position: "relative" }}
          >
            <div className="chat-title">Chat {chat._id.slice(-4)}</div>
            <div className="chat-date">
              {new Date(chat.created_at).toLocaleString()}
            </div>
            {/* Delete button, only visible on hover */}
            <button
              className="delete-chat-btn"
              onClick={e => {
                e.stopPropagation();
                onDeleteChat(chat._id);
              }}
              title="Delete chat"
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatSidebar;
