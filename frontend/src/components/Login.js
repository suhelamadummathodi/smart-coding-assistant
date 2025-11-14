import React, { useState } from "react";
import API from "../api/axiosInstance";
import { useNavigate, Link } from "react-router-dom";

function Login() {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await API.post("login", credentials);
      const token = res.data.access_token;
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      setMessage("Login successful!");
      navigate("/");
    } catch (error) {
      setMessage(error.response?.data?.detail || "Invalid credentials");
    }
  };

  return (
    <div className="container mt-5">
      <h2>Login</h2>
      <form onSubmit={handleSubmit} className="mt-3">
        <div className="mb-3">
          <label>Username</label>
          <input
            type="text"
            name="username"
            className="form-control"
            onChange={handleChange}
            required
          />
        </div>
        <div className="mb-3">
          <label>Password</label>
          <input
            type="password"
            name="password"
            className="form-control"
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn btn-success">
          Login
        </button>
        {message && <p className="mt-3 text-danger">{message}</p>}
        <p className="mt-3">
            Don't have an account? <Link to="/signup">Sign up here</Link>.
        </p>
      </form>
    </div>
  );
}

export default Login;
