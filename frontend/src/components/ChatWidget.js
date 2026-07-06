import React, { useState } from "react";
import client from "../api/client";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi! Ask me things like \"who repairs street lights?\" or \"what is my complaint status?\"" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim()) return;
    const question = input;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    try {
      const res = await client.post("/chatbot/ask", { question });
      const sourceNote = res.data.sources?.length ? ` (source: ${res.data.sources.join(", ")})` : "";
      setMessages((m) => [...m, { role: "bot", text: res.data.answer + sourceNote }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "bot", text: "Sorry, I couldn't reach the assistant right now." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-widget" style={{ height: open ? 420 : 46 }}>
      <div className="chat-header" onClick={() => setOpen(!open)}>
        <span>💬 Ask the Grievance Assistant</span>
        <span>{open ? "▼" : "▲"}</span>
      </div>
      {open && (
        <>
          <div className="chat-body">
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>{m.text}</div>
            ))}
            {loading && <div className="chat-msg bot">Thinking...</div>}
          </div>
          <div className="chat-input-row">
            <input
              value={input}
              placeholder="Type your question..."
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
            />
            <button onClick={send}>Send</button>
          </div>
        </>
      )}
    </div>
  );
}
