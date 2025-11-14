import React, { useCallback, useEffect, useState } from "react";
import API, { renameSession, deleteSession } from "../api/axiosInstance";
import "./Sidebar.css";
import {

// Sidebar.js
    FaEllipsisV,
    FaCheck,
    FaTimes,
    FaChevronDown,
    FaChevronRight
} from "react-icons/fa";

function Sidebar({ onSelectChat, updatedChat, newChat }) {
    // === Chat states ===
    const [chats, setChats] = useState([]);
    const [username, setUsername] = useState("");
    const [editingChatId, setEditingChatId] = useState(null);
    const [newTitle, setNewTitle] = useState("");
    const [menuOpenId, setMenuOpenId] = useState(null);
    const [activeChatId, setActiveChatId] = useState(null);
    const [activeProjectId, setActiveProjectId] = useState(null);

    // === Project states ===
    const [projects, setProjects] = useState([]);
    const [collapsedProjects, setCollapsedProjects] = useState({});
    const [showNewProject, setShowNewProject] = useState(false);
    const [newProjectName, setNewProjectName] = useState("");
    const [githubUrl, setGithubUrl] = useState("");
    const [zipFile, setZipFile] = useState(null);
    const [projectMenuOpenId, setProjectMenuOpenId] = useState(null);

    // Fetch projects and chats
    const fetchProjectsAndChats = useCallback(
        async (userId) => {
            try {
                const [projectsRes, chatsRes] = await Promise.all([
                    API.get('/projects/list'),
                    API.get('/sessions'),
                ]);
                setProjects(projectsRes.data.projects || []);
                setChats(chatsRes.data || []);
            } catch (err) {
                // eslint-disable-next-line no-console
                console.error("Failed to load projects or chats", err);
            }
        },
        []
    );

    useEffect(() => {
        const userData = localStorage.getItem("user");
        if (userData) {
            const user = JSON.parse(userData);
            setUsername(user.username || "");
            fetchProjectsAndChats(user.id);
        }
        // fetchProjectsAndChats is stable due to useCallback
    }, [fetchProjectsAndChats]);

    useEffect(() => {
        if (updatedChat && updatedChat.id) {
            setChats((prev) =>
                prev.map((chat) =>
                    chat.id === updatedChat.id ? { ...chat, title: updatedChat.title } : chat
                )
            );
        }
    }, [updatedChat]);

    // useEffect(() => {
    //     if (newChat && !chats.some((c) => c.id === newChat.id)) {
    //         setChats((prev) => [newChat, ...prev]);
    //         setActiveChatId(newChat.id);
    //     }
    //     // ok for chats in deps to avoid stale state
    // }, [newChat, chats]);

    useEffect(() => {
        if (
            newChat && 
            newChat.id &&                      // ✅ only add real sessions with valid ID
            !chats.some((c) => c.id === newChat.id)
        ) {
            setChats((prev) => [newChat, ...prev]);
            setActiveChatId(newChat.id);
        }
    }, [newChat, chats]);

    const handleNewChat = () => {
        setActiveChatId(null);
        onSelectChat(null);
        setActiveProjectId(null);
    };

    const handleRename = async (chatId) => {
        if (!newTitle.trim()) return;
        try {
            const res = await renameSession(chatId, newTitle.trim());
            setChats((prev) =>
                prev.map((chat) =>
                    chat.id === chatId ? { ...chat, title: res.data.title } : chat
                )
            );
            setEditingChatId(null);
            setNewTitle("");
        } catch (err) {
            // eslint-disable-next-line no-console
            console.error("Rename failed", err);
        }
    };

    const handleDelete = async (chatId) => {
        if (!window.confirm("Are you sure you want to delete this chat?")) return;
        try {
            await deleteSession(chatId);
            setChats((prev) => prev.filter((chat) => chat.id !== chatId));
            if (activeChatId === chatId) {
                onSelectChat(null);
                setActiveChatId(null);
            }
        } catch (err) {
            // eslint-disable-next-line no-console
            console.error("Delete failed", err);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/login";
    };

    // === Project Handlers ===
    const handleZipFile = (e) => setZipFile(e.target.files[0] || null);

    const attachProjectToSession = useCallback(
        async (projectId) => {
            if (activeChatId) {
                await API.put(`/sessions/${activeChatId}/`, { project_id: projectId });
                // If parent expects selected chat object, call accordingly
                onSelectChat((prev) => ({ ...prev, project_id: projectId }));
            } else {
                // create a new session attached to this project
                const userId = JSON.parse(localStorage.getItem("user")).id;
                const res = await API.post("/sessions", {
                    title: null,
                    project_id: projectId,
                    user_id: userId,
                });
                onSelectChat(res.data);
            }
        },
        [activeChatId, onSelectChat]
    );

    const createProjectAndAttach = async () => {
        if (!newProjectName.trim()) {
            alert("Enter project name");
            return;
        }

        const userData = localStorage.getItem("user");
        if (!userData) {
            alert("User not found");
            return;
        }
        const user = JSON.parse(userData);

        try {
            let project = null;

            if (zipFile) {
                const formData = new FormData();
                formData.append("upload", zipFile);
                formData.append("project_name", newProjectName);
                const res = await API.post('/projects/upload', formData, {
                    headers: { "Content-Type": "multipart/form-data" },
                });
                project = res.data.project;
            } else if (githubUrl.trim()) {
                const res = await API.post('/projects/clone', {
                    repo_url: githubUrl,
                    project_name: newProjectName,
                });
                project = res.data.project;
            } else {
                alert("Upload a ZIP or enter GitHub URL");
                return;
            }

            if (project && project.id) {
                await attachProjectToSession(project.id);
                await fetchProjectsAndChats(user.id);
            }

            setShowNewProject(false);
            setNewProjectName("");
            setGithubUrl("");
            setZipFile(null);
        } catch (err) {
            // eslint-disable-next-line no-console
            console.error("Project creation failed", err);
        }
    };

    const deleteProject = async (projectId) => {
        if (!window.confirm("Delete this project and all its sessions?")) return;
        try {
            await API.delete(`/projects/${projectId}`);
            setProjects((prev) => prev.filter((p) => p.id !== projectId));
            setChats((prev) => prev.filter((c) => c.project_id !== projectId));
            setProjectMenuOpenId(null);
        } catch (err) {
            // eslint-disable-next-line no-console
            console.error("Failed to delete project", err);
        }
    };

    const toggleCollapseProject = (projectId) => {
        setCollapsedProjects((prev) => ({ ...prev, [projectId]: !prev[projectId] }));
    };

    const renderChatItem = (chat) => (
        <li
            key={chat.id}
            className={`list-group-item d-flex justify-content-between align-items-center chat-item ${
                activeChatId === chat.id ? "active-chat" : ""
            }`}
            onMouseLeave={() => setMenuOpenId(null)}
        >
            {editingChatId === chat.id ? (
                <div className="d-flex align-items-center flex-grow-1">
                    <input
                        type="text"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        className="form-control form-control-sm me-2"
                        autoFocus
                    />
                    <FaCheck
                        className="text-success me-2"
                        style={{ cursor: "pointer" }}
                        onClick={() => handleRename(chat.id)}
                    />
                    <FaTimes
                        className="text-danger"
                        style={{ cursor: "pointer" }}
                        onClick={() => {
                            setEditingChatId(null);
                            setNewTitle("");
                        }}
                    />
                </div>
            ) : (
                <>
                    <div
                        className="flex-grow-1 me-2 text-truncate"
                        onClick={() => {
                            onSelectChat(chat);
                            setActiveChatId(chat.id);
                            setActiveProjectId(null);
                        }}
                        style={{ cursor: "pointer" }}
                    >
                        {chat.title || `Chat #${chat.id}`}
                    </div>

                    <div className="chat-options position-relative">
                        <FaEllipsisV
                            className="text-secondary chat-menu-icon"
                            style={{ cursor: "pointer" }}
                            onClick={() => setMenuOpenId((prev) => (prev === chat.id ? null : chat.id))}
                        />
                        {menuOpenId === chat.id && (
                            <div className="chat-dropdown position-absolute bg-white border rounded shadow-sm">
                                <div
                                    className="dropdown-item py-1 px-3 text-secondary"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => {
                                        setEditingChatId(chat.id);
                                        setNewTitle(chat.title || "");
                                        setMenuOpenId(null);
                                    }}
                                >
                                    Rename
                                </div>
                                <div
                                    className="dropdown-item py-1 px-3 text-danger"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => {
                                        handleDelete(chat.id);
                                        setMenuOpenId(null);
                                    }}
                                >
                                    Delete
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}
        </li>
    );

    return (
        <>
            <div className="sidebar bg-light border-end d-flex flex-column">
                <div className="p-3 border-bottom">
                    <button
                        className="btn btn-primary w-100"
                        type="button"
                        onClick={() => {setActiveChatId(null);
                                        setActiveProjectId(null);
                                      onSelectChat(null);
                                      setShowNewProject(true);}}
                    >
                        + New Project
                    </button>
                </div>

                <div className="p-3 border-bottom">
                    <button className="btn btn-primary w-100" type="button" onClick={handleNewChat}>
                        + New Chat
                    </button>
                </div>

                <div className="chats flex-grow-1 overflow-auto">
                    <h5 className="p-3">Projects</h5>
                    <ul className="list-group list-group-flush">
                        {projects.length > 0 ? (
                            projects.map((project) => {
                                const projectChats = chats.filter((c) => c.project_id === project.id);
                                return (
                                    <li key={project.id} className={`list-group-item project-item ${
                                        activeProjectId === project.id ? "active-project" : ""
                                      }`}>
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div
                                                className="flex-grow-1"
                                                onClick={() => {
                                                    onSelectChat({
                                                        project_id: project.id,
                                                        title: project.name,
                                                        isProjectHome: true,
                                                    });
                                                    setActiveProjectId(project.id);
                                                    setActiveChatId(null);
                                                }}
                                                style={{ cursor: "pointer" }}
                                            >
                                                {collapsedProjects[project.id] ? (
                                                    <FaChevronRight
                                                        className="me-2"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            toggleCollapseProject(project.id);
                                                        }}
                                                    />
                                                ) : (
                                                    <FaChevronDown
                                                        className="me-2"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            toggleCollapseProject(project.id);
                                                        }}
                                                    />
                                                )}
                                                {project.name}
                                            </div>

                                            <div className="chat-options position-relative">
                                                <FaEllipsisV
                                                    className="text-secondary"
                                                    onClick={() =>
                                                        setProjectMenuOpenId((prev) => (prev === project.id ? null : project.id))
                                                    }
                                                    style={{ cursor: "pointer" }}
                                                />
                                                {projectMenuOpenId === project.id && (
                                                    <div className="chat-dropdown position-absolute bg-white border rounded shadow-sm end-0">
                                                        <div
                                                            className="dropdown-item py-1 px-3 text-danger"
                                                            onClick={() => deleteProject(project.id)}
                                                        >
                                                            Delete
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {!collapsedProjects[project.id] && (
                                            <ul className="list-group list-group-flush ms-4 mt-2">
                                                {projectChats.length > 0 ? (
                                                    projectChats.map((chat) => renderChatItem(chat))
                                                ) : (
                                                    <li className="list-group-item text-muted">No chats yet</li>
                                                )}
                                            </ul>
                                        )}
                                    </li>
                                );
                            })
                        ) : (
                            <li className="list-group-item text-muted">No projects yet</li>
                        )}
                    </ul>

                    <h5 className="p-3 mt-3">Orphaned Chats</h5>
                    <ul className="list-group list-group-flush">
                        {chats.filter((c) => !c.project_id).length > 0 ? (
                            chats.filter((c) => !c.project_id).map((chat) => renderChatItem(chat))
                        ) : (
                            <li className="list-group-item text-muted">No orphaned chats</li>
                        )}
                    </ul>
                </div>

                <div className="p-3 border-top user-info d-flex justify-content-between align-items-center">
                    <strong>{username || "User"}</strong>
                    <button onClick={handleLogout} className="btn btn-outline-danger btn-sm" type="button">
                        Logout
                    </button>
                </div>
            </div>

            {/* === New Project Modal === */}
            {showNewProject && (
                <div className="project-modal-overlay" onClick={() => setShowNewProject(false)}>
                    <div className="project-modal bg-white shadow rounded p-4" onClick={(e) => e.stopPropagation()}>
                        <h5>Create New Project</h5>

                        <input
                            type="text"
                            className="form-control mb-2"
                            placeholder="Project Name"
                            value={newProjectName}
                            onChange={(e) => setNewProjectName(e.target.value)}
                        />

                        <div className="mt-3">
                            <label className="form-label">Upload ZIP:</label>
                            <input type="file" accept=".zip" onChange={handleZipFile} />
                        </div>

                        <div className="mt-3">
                            <label className="form-label">Or GitHub Repo URL:</label>
                            <input
                                type="text"
                                className="form-control"
                                placeholder="https://github.com/username/repo"
                                value={githubUrl}
                                onChange={(e) => setGithubUrl(e.target.value)}
                            />
                        </div>

                        <div className="mt-3 d-flex justify-content-end">
                            <button
                                className="btn btn-secondary me-2"
                                onClick={() => setShowNewProject(false)}
                                type="button"
                            >
                                Cancel
                            </button>
                            <button className="btn btn-primary" onClick={createProjectAndAttach} type="button">
                                Create & Upload
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

export default Sidebar;