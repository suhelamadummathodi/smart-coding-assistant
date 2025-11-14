import React, { useState } from "react";
import API from "../api/axiosInstance";
import { Link } from "react-router-dom";


function Signup() {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await API.post("signup", formData);
      setMessage(res.data.message || "Signup successful! You can now log in.");
    } catch (error) {
      setMessage(error.response?.data?.detail || "Signup failed.");
    }
  };

  return (
    <div className="container mt-5">
      <h2>Signup</h2>
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
          <label>Email</label>
          <input
            type="email"
            name="email"
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
        <button type="submit" className="btn btn-primary">
          Signup
        </button>
        {message && <p className="mt-3 text-info">{message}</p>}
        <p className="mt-3">
            Already have an account? <Link to="/login">Login here</Link>.
        </p>
      </form>
    </div>
  );
}

export default Signup;
