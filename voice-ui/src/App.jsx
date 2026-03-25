import { useState, useRef } from "react";
import { Room, RoomEvent } from "livekit-client";

export default function App() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("Idle");

  const roomRef = useRef(null);

  const addMessage = (text, sender) => {
    setMessages((prev) => [...prev, { text, sender }]);
  };

  // 🎤 MIC STYLE (animated)
  const getMicStyle = () => {
    let color = "#64748b";
    let animation = "none";

    if (status === "Listening...") {
      color = "#22c55e";
      animation = "pulse 1.5s infinite";
    }

    if (status === "Speaking...") {
      color = "#eab308";
      animation = "pulse 0.8s infinite";
    }

    return {
      width: "80px",
      height: "80px",
      borderRadius: "50%",
      background: color,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: "26px",
      animation: animation,
      boxShadow: `0 0 25px ${color}`,
      border: "none",
      cursor: "pointer",
      transition: "all 0.3s ease"
    };
  };

  const startCall = async (lang) => {
    try {
      setStatus("Connecting...");

      const identity = "user_" + crypto.randomUUID();
      const roomName = "room_" + crypto.randomUUID();

      const res = await fetch(
        `http://127.0.0.1:8000/livekit-token?identity=${identity}&room=${roomName}&lang=${lang}`
      );

      const data = await res.json();

      const room = new Room();
      roomRef.current = room;

      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === "audio") {
          const el = track.attach();
          el.autoplay = true;
          document.body.appendChild(el);
        }
      });

      room.on(RoomEvent.TranscriptionReceived, (segments, participant) => {
        segments.forEach((seg) => {
          if (seg.final) {
            if (participant?.isLocal) {
              addMessage(seg.text, "user");
              setStatus("Listening...");
            } else {
              addMessage(seg.text, "agent");
              setStatus("Speaking...");
            }
          }
        });
      });

      await room.connect(
        "wss://ai-voice-agent-nuhvffaa.livekit.cloud",
        data.token
      );

      await room.localParticipant.setMicrophoneEnabled(true);

      setConnected(true);
      setStatus("Listening...");

    } catch (err) {
      console.error(err);
      setStatus("Error");
    }
  };

  const endCall = async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      setConnected(false);
      setStatus("Idle");
    }
  };

  return (
    <div style={{
      height: "100vh",
      background: "linear-gradient(135deg, #0f172a, #1e293b)",
      color: "white",
      display: "flex",
      flexDirection: "column"
    }}>

      {/* HEADER */}
      <div style={{
        padding: "16px",
        borderBottom: "1px solid rgba(255,255,255,0.1)",
        display: "flex",
        justifyContent: "space-between"
      }}>
        <h2>AI Booking Assistant</h2>
        <span style={{ color: connected ? "#4ade80" : "#f87171" }}>
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      {/* STATUS */}
      <div style={{
        textAlign: "center",
        padding: "10px",
        fontSize: "14px",
        opacity: 0.8
      }}>
        {status}
      </div>

      {/* CHAT */}
      <div style={{
        flex: 1,
        padding: "20px",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        gap: "12px"
      }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              background: msg.sender === "user"
                ? "linear-gradient(135deg, #3b82f6, #2563eb)"
                : "rgba(255,255,255,0.05)",
              padding: "12px 16px",
              borderRadius: "18px",
              maxWidth: "60%",
              backdropFilter: "blur(6px)"
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* CONTROLS */}
      <div style={{
        padding: "20px",
        borderTop: "1px solid rgba(255,255,255,0.1)",
        display: "flex",
        justifyContent: "center",
        gap: "15px",
        alignItems: "center"
      }}>

        {!connected ? (
          <>
            <button
              onClick={() => startCall("en")}
              style={{
                padding: "12px 20px",
                borderRadius: "12px",
                background: "#22c55e",
                border: "none",
                cursor: "pointer"
              }}
            >
              Start English
            </button>

            <button
              onClick={() => startCall("ar")}
              style={{
                padding: "12px 20px",
                borderRadius: "12px",
                background: "#eab308",
                border: "none",
                cursor: "pointer"
              }}
            >
              Start Arabic
            </button>
          </>
        ) : (
          <button onClick={endCall} style={getMicStyle()}>
            🎤
          </button>
        )}
      </div>
    </div>
  );
}