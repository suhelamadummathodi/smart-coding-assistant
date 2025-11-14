// src/components/ChatMessage.jsx
import React, { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import ReactMarkdown from "react-markdown";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import "./ChatMessage.css";

export default function ChatMessage({ msg, username }) {
  const [copied, setCopied] = useState(false);

  // Regex to detect ```lang\ncode``` blocks
  const codeRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = codeRegex.exec(msg.content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: msg.content.slice(lastIndex, match.index) });
    }
    parts.push({ type: "code", lang: match[1] || "text", content: match[2] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < msg.content.length) {
    parts.push({ type: "text", content: msg.content.slice(lastIndex) });
  }

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1000);
  };

  return (
    <div className={`chat-bubble ${msg.sender_type === "user" ? "user" : "ai"}`}>
      <strong>{msg.sender_type === "user" ? username : "AI Assistant"}</strong>
      <div className="mt-1">
        {parts.map((p, idx) =>
          p.type === "text" ? (
            <ReactMarkdown key={idx}>{p.content}</ReactMarkdown>
          ) : (
            <div key={idx} className="code-block-wrapper">
              <SyntaxHighlighter language={p.lang} style={oneDark} showLineNumbers>
                {p.content}
              </SyntaxHighlighter>
              <button className="copy-btn" onClick={() => handleCopy(p.content)}>
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          )
        )}
      </div>
    </div>
  );
}
