import { useEffect, useState } from "react";

export default function App() {
  const [messages, setMessages] = useState([
    { sender: "ai", text: "Welcome to Renidy. How can I assist you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // 👤 Static user ID (could be stored in localStorage for multi-session)
  const userId = "user-123"; // Replace with dynamic ID if needed

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          message: input,
        }),
      });

      const data = await res.json();

      const aiResponse = {
        sender: "ai",
        text: data.response,
        escalate: data.escalate,
      };

      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: "Something went wrong. Please try again later." },
      ]);
    }

    setInput("");
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-blue-50 flex items-center justify-center px-4">
      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl p-6 flex flex-col">
        <h1 className="text-3xl font-bold mb-6 text-center text-blue-700">Renidy Funeral Planner</h1>

        <div className="flex-1 overflow-y-auto space-y-4 mb-6 max-h-[60vh] pr-2">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`max-w-[75%] p-3 rounded-xl text-sm ${
                msg.sender === "user"
                  ? "bg-blue-600 text-white ml-auto"
                  : "bg-gray-100 text-gray-800 mr-auto"
              }`}
            >
              {msg.text}
              {msg.escalate && (
                <div className="text-xs text-red-500 mt-1">Escalated to human support</div>
              )}
            </div>
          ))}
          {loading && (
            <div className="text-sm text-gray-400 italic">Renidy is typing…</div>
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <button
            onClick={sendMessage}
            className="bg-blue-600 text-white px-6 py-2 rounded-full hover:bg-blue-700 transition"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
