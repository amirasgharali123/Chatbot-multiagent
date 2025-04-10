import { useState } from "react";

export default function App() {
  const [messages, setMessages] = useState([
    { sender: "ai", text: "Welcome to Renidy" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
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
    <div className="min-h-screen bg-gradient-to-b from-blue-100 to-gray-100 flex items-center justify-center px-4 py-6">
      <div className="w-full max-w-3xl bg-white rounded-3xl shadow-xl p-6 flex flex-col">
        <h1 className="text-2xl font-bold mb-4 text-center text-gray-800">Renidy Funeral Planner</h1>
        
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 max-h-[60vh] pr-2">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`max-w-[80%] p-3 rounded-xl text-sm ${
                msg.sender === "user"
                  ? "bg-blue-500 text-white self-end ml-auto"
                  : "bg-gray-200 text-gray-900 self-start mr-auto"
              }`}
            >
              {msg.text}
              {msg.escalate && (
                <div className="text-xs text-red-600 mt-1">Escalated to human support</div>
              )}
            </div>
          ))}
          {loading && (
            <div className="text-sm text-gray-400 italic">Renidy is typing…</div>
          )}
        </div>

        <div className="flex gap-2 mt-auto">
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
            className="bg-blue-500 text-white px-6 py-2 rounded-full hover:bg-blue-600 transition"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
