# 🎙️ Voice Agent (LiveKit AI Interface)

This project implements a real-time voice AI agent system using LiveKit, designed to work as a voice interface layer for the healthcare booking backend.

It enables users to interact with the system using natural speech (Arabic & English), powered by streaming STT, LLM, and TTS.

---

## 🧠 Overview

This project is part of a larger system:

Backend (logic, database, APIs):  
https://github.com/Ashoub90/ai-healthcare-booking-agent

Voice interface (this project):  
voice-agent

---

## ⚙️ Architecture

Browser (LiveKit client)
↓
LiveKit Cloud (WebRTC)
↓
LiveKit Agents (this project)
↓
FastAPI Backend (ai-healthcare-booking-agent)
↓
Database

---

## 🚀 Features

- Real-time voice interaction (WebRTC via LiveKit)
- Multilingual support (Arabic/English)
- AI-powered conversation via backend LLM
- Speech-to-text using Deepgram
- Text-to-speech using ElevenLabs
- Streaming audio with real-time responses
- Live transcription in UI (user + agent)
- Agent dispatching based on selected language

---

## 📂 Project Structure

voice-agent/
├── agent_worker_ar.py     (Arabic agent)
├── agent_worker_en.py     (English agent)
├── livekit_handler.py     (core agent logic)
├── index.html             (frontend client)
├── .env                   (API keys)
└── README.md

---

## 🧩 How It Works

1. User selects language in UI (Arabic or English)

2. Frontend requests token from backend:
   /livekit-token?identity=...&room=...&lang=...

3. Backend dispatches correct agent:
   booking-voice-ar or booking-voice-en

4. Agent joins LiveKit room and starts pipeline:
   STT → LLM → TTS

5. Voice conversation begins

---

## ▶️ Running the Project

1. Start backend (in ai-healthcare-booking-agent):

cd ai-healthcare-booking-agent
docker-compose up

---

2. Start agents (in separate terminals):

Arabic agent:
cd voice-agent
python agent_worker_ar.py start

English agent:
cd voice-agent
python agent_worker_en.py start

---

3. Run frontend:

Option A: VS Code Live Server  
Option B:

cd voice-agent
python -m http.server 5500

Open:
http://localhost:5500

---

## 🔐 Environment Variables

Create a .env file:

LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

DEEPGRAM_API_KEY=...

ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID_AR=...
ELEVENLABS_VOICE_ID_EN=...

---

## ⚠️ Notes

- Voice is fixed per session, so language must be selected before starting the call
- Each agent runs as a separate process
- Backend handles memory and session state (must be unique per user)

---

## 🔗 Related Project

Backend repository:
https://github.com/Ashoub90/ai-healthcare-booking-agent

This project acts as the voice layer for that backend.

---

## 📌 Future Improvements

- Proper session isolation per user
- Streaming partial transcripts (reduce lag)
- Dockerize agents
- Improve UI (chat-style interface)
- Multi-channel support (web, mobile, telephony)

---

## 💡 Summary

This project is the voice interface for the healthcare booking system, enabling fully conversational AI interactions using real-time audio.