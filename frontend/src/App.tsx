import { useEffect, useRef, useState } from "react";

export default function ChatApp() {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [conversationName, setConversationName] = useState("");
  const [errorAlert, setErrorAlert] = useState<{ show: boolean; message: string }>({ show: false, message: "" });
  const [conversations, setConversations] = useState<string[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const loadConversations = async () => {
      try {
        const res = await fetch("http://localhost:8000/conversations");
        if (res.ok) {
          const data = await res.json();
          setConversations(data.conversations);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadConversations();
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    setMessages((prev) => [...prev, input]);
    setInput("");
    setLoading(true);

    try {
      let reply = "";

      if (selectedConversation) {
        // Use the new API that handles everything
        const res = await fetch("http://localhost:8000/conversations/messages", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: selectedConversation, message: input }),
        });

        if (res.ok) {
          const data = await res.json();
          reply = data.reply;
        } else {
          setErrorAlert({ show: true, message: "Error sending message" });
          setLoading(false);
          return;
        }
      }

      setMessages((prev) => [...prev, reply]);
    } catch (err) {
      console.error(err);
      setErrorAlert({ show: true, message: "Server connection error" });
    } finally {
      setLoading(false);
    }
  };

  const createConversation = async () => {
    if (!conversationName.trim()) return;

    try {
      const res = await fetch("http://localhost:8000/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: conversationName }),
      });

      if (res.ok) {
        const data = await res.json();
        console.log("Conversation created:", data);
        setShowDialog(false);
        setConversationName("");
        // Reload the conversation list
        const convRes = await fetch("http://localhost:8000/conversations");
        if (convRes.ok) {
          const convData = await convRes.json();
          setConversations(convData.conversations);
          // Automatically select the new conversation
          setSelectedConversation(data.name);
          setMessages([]);
        }
      } else {
        setErrorAlert({ show: true, message: "Error creating conversation" });
      }
    } catch (err) {
      console.error(err);
      setErrorAlert({ show: true, message: "Server connection error" });
    }
  };

  const loadConversationMessages = async (name: string) => {
    try {
      const res = await fetch(`http://localhost:8000/conversations/${name}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages);
        setSelectedConversation(name);
      } else {
        setErrorAlert({ show: true, message: "Error loading messages" });
      }
    } catch (err) {
      console.error(err);
      setErrorAlert({ show: true, message: "Server connection error" });
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 text-white">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-gray-800 bg-black/30 backdrop-blur-xl">
        <div className="p-4 text-lg font-semibold border-b border-gray-800">
          💬 My Chats
        </div>
        <div className="flex-1 p-3 space-y-2 overflow-y-auto">
          <button
            onClick={() => setShowDialog(true)}
            className="w-full text-left px-3 py-2 rounded-lg bg-blue-600/90 hover:bg-blue-500 transition"
          >
            New chat
          </button>
          {conversations.map((conv) => (
            <button
              key={conv}
              onClick={() => loadConversationMessages(conv)}
              className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-800/60 transition ${
                selectedConversation === conv ? "bg-gray-800/60" : ""
              }`}
            >
              {conv}
            </button>
          ))}
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-col flex-1">
        {/* Header */}
        <div className="p-4 border-b border-gray-800 backdrop-blur bg-black/20">
          <h1 className="text-lg font-semibold">DentalBot</h1>
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {!selectedConversation ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-400 text-lg">Create a chat first or choose an existing one.</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-400 text-lg">Ask me what you need.</p>
            </div>
          ) : (
            <>
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex items-end gap-3 ${
                    index % 2 === 0 ? "justify-end" : "justify-start"
                  }`}
                >
                  {index % 2 === 1 && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center text-sm">
                      🤖
                    </div>
                  )}

                  <div
                    className={`max-w-2xl px-4 py-3 rounded-2xl shadow-lg whitespace-pre-wrap leading-relaxed ${
                      index % 2 === 0
                        ? "bg-blue-600/90 rounded-br-none"
                        : "bg-gray-800/80 rounded-bl-none"
                    }`}
                  >
                    {msg}
                  </div>

                  {index % 2 === 0 && (
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm">
                      👤
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-3 text-gray-400">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
                    🤖
                  </div>
                  <div className="flex space-x-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </>
          )}
        </div>

        {/* Input */}
        {selectedConversation && (
          <div className="p-4 border-t border-gray-800 bg-black/20 backdrop-blur">
            <div className="flex items-center gap-3 bg-gray-900/80 border border-gray-700 rounded-2xl px-4 py-2 shadow-inner focus-within:border-blue-500">
              <input
                className="flex-1 bg-transparent outline-none text-sm placeholder-gray-400"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Write a message..."
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              />

              <button
                onClick={sendMessage}
                disabled={loading}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 disabled:opacity-50 transition shadow"
              >
                Send
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Dialog to create conversation */}
      {showDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-semibold mb-4">New conversation</h2>
            <input
              type="text"
              value={conversationName}
              onChange={(e) => setConversationName(e.target.value)}
              placeholder="Conversation name"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white outline-none focus:border-blue-500 mb-4"
              onKeyDown={(e) => e.key === "Enter" && createConversation()}
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDialog(false);
                  setConversationName("");
                }}
                className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition"
              >
                Cancel
              </button>
              <button
                onClick={createConversation}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 transition"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Alert UI */}
      {errorAlert.show && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right">
          <div className="bg-red-900/90 border border-red-700 rounded-xl px-4 py-3 shadow-2xl backdrop-blur-sm flex items-center gap-3">
            <span className="text-red-400 text-xl">⚠️</span>
            <span className="text-white text-sm">{errorAlert.message}</span>
            <button
              onClick={() => setErrorAlert({ show: false, message: "" })}
              className="ml-2 text-red-400 hover:text-red-300 transition"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
