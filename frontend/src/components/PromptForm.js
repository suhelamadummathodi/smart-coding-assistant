import React, { useEffect, useState, useRef } from "react";
import {
  sendMessage,
  fetchMessages,
  createSessionObj,
  fetchSessionsByProject,
} from "../api/axiosInstance";
import { FaRobot, FaSpinner } from "react-icons/fa";
import "./PromptForm.css";
import ChatMessage from "../components/ChatMessage";

function PromptForm({ selectedChat, onSessionUpdated, onNewSessionCreated }) {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("ollama");

  const [sessionMessages, setSessionMessages] = useState({});
  const [loadingSessions, setLoadingSessions] = useState({});
  const [projectSessions, setProjectSessions] = useState([]);

  const user = JSON.parse(localStorage.getItem("user"));
  const chatWindowRef = useRef(null);

  useEffect(() => {
    if (selectedChat) {
      if (selectedChat.isProjectHome) {
        loadProjectSessions(selectedChat.project_id);
      } else {
        loadMessages(selectedChat.id);
      }
    } else {
      // no selection -> clear messages
      setPrompt("");
      setSessionMessages({});
      setProjectSessions([]);
    }
  }, [selectedChat]);

  useEffect(() => {
    if (chatWindowRef.current && selectedChat && !selectedChat.isProjectHome) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [sessionMessages, selectedChat]);

  const loadMessages = async (sessionId) => {
    try {
      const res = await fetchMessages(sessionId);
      setSessionMessages((prev) => ({ ...prev, [sessionId]: res.data }));
    } catch (err) {
      console.error("Failed to load messages", err);
    }
  };

  const loadProjectSessions = async (projectId) => {
    try {
      const res = await fetchSessionsByProject(projectId);
      setProjectSessions(res.data);
    } catch (err) {
      console.error("Failed to load project sessions", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    let currentSessionId = selectedChat?.id;

    // If we're on the project's home page -> create a new session under that project
    if (selectedChat?.isProjectHome) {
      try {
        const res = await createSessionObj({
          title: null,
          project_id: selectedChat.project_id,
          user_id: user.id,
        });
        currentSessionId = res.data.id;
        onNewSessionCreated(res.data);
        // refresh list under project
        loadProjectSessions(selectedChat.project_id);
      } catch (err) {
        console.error("Failed to create new session under project", err);
        return;
      }
    } else if (!selectedChat) {
      // If no session selected -> create standalone session
      try {
        const res = await createSessionObj({
          title: null,
          project_id: null,
          user_id: user.id,
        });
        currentSessionId = res.data.id;
        onNewSessionCreated(res.data);
      } catch (err) {
        console.error("Failed to create new chat", err);
        return;
      }
    }

    const newMsg = {
      sender_type: "user",
      content: prompt,
      model_used: model,
      session_id: currentSessionId,
    };

    // optimistic UI
    setSessionMessages((prev) => {
      const msgs = prev[currentSessionId] || [];
      return { ...prev, [currentSessionId]: [...msgs, { ...newMsg, id: Date.now() }] };
    });
    setPrompt("");
    setLoadingSessions((prev) => ({ ...prev, [currentSessionId]: true }));

    try {
      const res = await sendMessage(currentSessionId, newMsg);
      const aiMsg = res.data.ai_message;
      const updatedSession = res.data.session;

      if (updatedSession?.id === currentSessionId) {
        setSessionMessages((prev) => {
          const msgs = prev[currentSessionId] || [];
          return { ...prev, [currentSessionId]: [...msgs, aiMsg] };
        });
      }

      if (updatedSession?.title) {
        onSessionUpdated(updatedSession);
      }
    } catch (err) {
      console.error("Error sending message:", err);
    } finally {
      setLoadingSessions((prev) => ({ ...prev, [currentSessionId]: false }));
    }
  };

  const handleTextareaChange = (e) => {
    setPrompt(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = e.target.scrollHeight + "px";
  };

  const handleProjectSessionClick = (session) => {
    onNewSessionCreated(session);
  };

  const messages =
    selectedChat && !selectedChat.isProjectHome
      ? sessionMessages[selectedChat.id] || []
      : [];

  const loading =
    selectedChat && !selectedChat.isProjectHome
      ? loadingSessions[selectedChat.id]
      : false;

  const isProjectHome = selectedChat?.isProjectHome;
  const hasProjectSessions = projectSessions.length > 0;

  return (
    <div className="chat-container d-flex flex-column h-100">
      {/* ===== Prompt form on TOP for Project Home ===== */}
      {isProjectHome && (
        <div className="project-top-form-wrapper col-6 mx-auto mt-3">
          <form onSubmit={handleSubmit} className="chat-input">
            <textarea
              className="form-control"
              value={prompt}
              onChange={handleTextareaChange}
              placeholder="Ask about this project or start a new session..."
              rows={1}
            />
            <div className="d-flex justify-content-between align-items-center mt-2">
              <select
                className="form-select w-auto"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                <option value="ollama">Ollama (Local)</option>
                <option value="openai">OpenAI (Cloud)</option>
              </select>

              <button className="btn btn-dark" disabled={loading}>
                <FaRobot className="me-2" />
                Send
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ===== Project sessions list (scrollable area below prompt) ===== */}
      {isProjectHome && (
        <div className="project-sessions-list col-6 mx-auto flex-grow-1 mt-3 mb-3">
          {hasProjectSessions ? (
            <ul className="list-group">
              {projectSessions.map((session) => (
                <li
                  key={session.id}
                  className="list-group-item list-group-item-action"
                  onClick={() => handleProjectSessionClick(session)}
                >
                  {session.title || `Chat #${session.id}`}
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center text-muted py-4">
              <p>No sessions yet for this project.</p>
              <p>Type a question above to create one.</p>
            </div>
          )}
        </div>
      )}

      {/* ===== Normal chat view (not project home) ===== */}
      {!isProjectHome && (
        <>
          <div className="chat-window flex-grow-1" ref={chatWindowRef}>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} msg={msg} username={user.username} />
            ))}
            {loading && (
              <div className="chat-bubble ai">
                <FaSpinner className="spin me-2" /> AI is thinking...
              </div>
            )}
          </div>

          <form
            onSubmit={handleSubmit}
            className={`chat-input col-8 mx-auto ${
              messages.length === 0 ? "my-auto" : "mt-auto mb-3"
            }`}
          >
            <textarea
              className="form-control"
              value={prompt}
              onChange={handleTextareaChange}
              placeholder="Type your message..."
              rows={1}
            />
            <div className="d-flex justify-content-between align-items-center mt-2">
              <select
                className="form-select w-auto"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                <option value="ollama">Ollama (Local)</option>
                <option value="openai">OpenAI (Cloud)</option>
                <option value="gemini">Gemini (Cloud)</option>
                <option value="claude">Claude (Cloud)</option>
              </select>

              <button className="btn btn-dark" disabled={loading}>
                <FaRobot className="me-2" />
                Send
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  );
}

export default PromptForm;
