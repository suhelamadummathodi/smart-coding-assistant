import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api", // backend base URL
});

// Add JWT token automatically if user is logged in
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ✅ Handle 401 (Unauthorized) globally
API.interceptors.response.use(
  (response) => response, // Just return the response if it's fine
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid → logout user
      localStorage.removeItem("token");
      // Redirect to login page
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);


export const fetchSessions = () =>
  API.get('/sessions');

export const fetchSessionsByProject = (projectId) =>
  API.get(`/sessions/projects/${projectId}`);

export const createSessionObj = (data) =>
  API.post("/sessions", data);

export const fetchMessages = (sessionId) =>
  API.get(`/messages/${sessionId}`);

export const sendMessage = (sessionId, messageData) =>
  API.post(`/messages`, messageData);

export const renameSession = (sessionId, newTitle) =>
  API.put(`/sessions/${sessionId}`, { title: newTitle });

export const deleteSession = (sessionId) =>
  API.delete(`/sessions/${sessionId}`);

export default API;
