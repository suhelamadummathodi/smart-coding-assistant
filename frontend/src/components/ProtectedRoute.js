import React from "react";
import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  
  if(!token) {
    return <Navigate to="/login" />;
  }
  try{
    const decoded = jwtDecode(token);
    const currentTime = Date.now() / 1000; // in seconds
    
    if (decoded.exp && decoded.exp < currentTime) {
      // Token expired → clear it and redirect to login
      localStorage.removeItem("token");
      return <Navigate to="/login" replace />;
    }

    return children;

  }
  catch(err) {
    // Invalid token format → remove it
    localStorage.removeItem("token");
    return <Navigate to="/login" />;
  }
};

export default ProtectedRoute;
