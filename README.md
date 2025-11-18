# Smart Coding Assistant — Technical Specification

**Author:** Suhela M Ali  
**Date:** 20 October 2025  

---

## 1. Project Summary

Build a developer-focused **Smart Coding Assistant** — a platform that reads a codebase and provides contextual AI suggestions such as:

- Autocomplete  
- Refactors  
- Test generation  
- Documentation improvement  
- Code reviews  

**Primary goal:** Increase developer productivity and code quality while remaining extensible and privacy-first.

---

## 2. Goals

### Primary Goals
- Produce **high-quality code suggestions** and test scaffolds.  
- Provide accurate, **context-aware refactor recommendations**.  
- Ensure **code privacy** and safe processing.  

### Success Metrics
- Time saved on boilerplate generation: **≥ 20%** (self-reported).  
- Unit tests generated that pass or need minimal edits: **60%+** pass without manual edits.  

---

## 3. Target Users & Use Cases

### Target Users
- Backend & frontend developers  
- Students learning programming  
- Engineering teams  

### Key Use Cases
- Generate unit tests for functions/components  
- Suggest refactors and surface possible bugs  
- Generate or enhance documentation  
- Create small reference code snippets for unfamiliar APIs  
- Provide inline code completions specialized to the repository  

---

## 4. MVP Feature List (Must-Have)

### Core MVP Features
- **Project ingestion:** Upload or link a Git repo to index files and build a context store.  
- **Snippet prompt UI:** Web interface to provide snippet, select a file, or request tests/docs/refactor.  
- **LLM-backed generator:** Backend service that combines context with prompts and returns structured suggestions.  

---

## 5. Tech Stack Recommendations

### Backend
- **Language:** Python (FastAPI)  
- **LLM Client:** OpenAI-compatible SDKs, or adapters to local models (Hugging Face / inference endpoints)  
- **Vector DB:** FAISS  
- **Metadata Database:** PostgreSQL  

### Frontend
- **Framework:** React.js  

---

## 6. High-Level Architecture

### Components

#### Ingestor
- Scans repo, tokenizes code (functions/classes), extracts metadata  
- Generates embeddings  
- Stores in vector DB  

#### Context Server
- Given a file + cursor + prompt, retrieves top-k relevant chunks  
- Supplies chunks to LLM prompt builder  

#### LLM Orchestrator
- Builds composite prompt (system + examples + context)  
- Calls selected LLM model  

#### Post-Processor
- Applies lint/static checks  
- Formats output  
- Returns final suggestions to UI/IDE  

---

## 7. Data Model (Simplified)

### PostgreSQL Tables

| Table | Fields |
|-------|--------|
| **users** | id, email, hashed_key, created_at |
| **projects** | id, user_id, repo_url, name, created_at |
| **files** | id, project_id, path, content_hash, last_indexed |
| **chunks** | id, file_id, start_line, end_line, text |
| **embeddings** | chunk_id, vector_reference |

### Vector DB Contents
- Maps: `chunk_id → vector`

---

## 8. API Endpoints (Example)

### Auth
- **POST** `/api/auth/login` – Issue token  

### Projects & Ingestion
- **POST** `/api/projects` – Add project (Git URL or zip)  
- **POST** `/api/projects/{id}/index` – Start indexing  
- **GET** `/api/projects/{id}/status` – Get indexing status  

### Embeddings & Search (Admin)
- **POST** `/api/embeddings/query` – Retrieve top-k chunks  

---

## 9. Prompt Design (Pattern)

### System Message
> You are a senior software engineer assistant. Produce concise, correct code and clear explanations. When asked, generate unit tests in the project’s style and testing framework.

### Few-Shot Examples
- Provide **2–4 input → output** examples  

### User Prompt Includes
- File path  
- Relevant code chunks  
- Cursor location  
- Request (tests/docs/refactor/snippet)  
- Language or framework  

---

## 10. Indexing & Context Pipeline

1. Clone or upload repo  
2. Walk through files (ignore node_modules, venv, .git, binaries)  
3. Break files into chunks (functions, classes, or 200–400 token windows)  
4. Generate embeddings and upsert to vector DB  
5. Maintain mapping: chunk → vector_id  
6. Retrieve exact code lines during suggestion  

---

## 11. Future Improvements

- **Feedback logging:** Track accept/reject actions  
- **VS Code extension:** Send file + cursor to backend for suggestions  
- **Team collaboration:** Shared indexes & prompt fine-tuning  
- **Offline LLM support** for strict privacy  
- **Multi-language support**  
- **Learning loop:** Improve prompts using collected feedback  

---
