import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import PromptForm from "../components/PromptForm";
import Header from "../components/Header";
import "./Home.css";

function Home() {
  const [selectedChat, setSelectedChat] = useState(null);
  const [updatedChat, setUpdatedChat] = useState(null);
  

  return (
    <div className="home-container">
      <Sidebar 
        onSelectChat={setSelectedChat}
        updatedChat={updatedChat}
        newChat={selectedChat}
      />
      <div className="main-content">
        <Header />
        <PromptForm
          selectedChat={selectedChat}
          onSessionUpdated={setUpdatedChat}
          onNewSessionCreated={(newChat) => setSelectedChat(newChat)}
        />
      </div>
    </div>
  );
}

export default Home;
