import os
import httpx
from contextlib import asynccontextmanager

from livekit.agents import Agent, AgentSession
from livekit.agents.llm import LLM
from livekit.plugins import deepgram, elevenlabs, silero

API_URL = "http://localhost:8000/chat/"


# =========================
# PHONE NORMALIZATION
# =========================
def normalize_phone(text: str) -> str:
    mapping = {
        "zero": "0", "oh": "0",
        "one": "1", "two": "2", "three": "3",
        "four": "4", "five": "5", "six": "6",
        "seven": "7", "eight": "8", "nine": "9"
    }

    words = text.lower().split()
    digits = []

    for w in words:
        if w in mapping:
            digits.append(mapping[w])
        elif w.isdigit():
            digits.append(w)

    if len(digits) >= 6:
        return "".join(digits)

    return text


# =========================
# LLM
# =========================
class BookingLLM(LLM):

    def __init__(self, room_name: str):
        super().__init__()
        self.room_name = room_name  # ✅ session isolation

    @asynccontextmanager
    async def chat(self, *, messages=None, input=None, **kwargs):
        try:
            chat_ctx = kwargs.get("chat_ctx")

            user_text = ""

            if chat_ctx:
                msgs = chat_ctx.messages()
                if msgs:
                    last_msg = msgs[-1]
                    raw = getattr(last_msg, "content", None) or getattr(last_msg, "text", "")
                    user_text = " ".join(map(str, raw)) if isinstance(raw, list) else str(raw)

            print("USER RAW:", user_text)

            normalized_text = normalize_phone(user_text)

            print("USER NORMALIZED:", normalized_text)

            # ✅ USE ROOM NAME AS SESSION ID
            session_id = self.room_name
            print("SESSION_ID:", session_id)

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    API_URL,
                    json={
                        "session_id": session_id,
                        "message": normalized_text,
                    }
                )

            reply = res.json().get("reply", "")

            print("AGENT:", reply)

            async def stream():
                for word in reply.split():
                    yield word + " "

            yield stream()

        except Exception as e:
            async def err():
                yield f"error: {str(e)}"
            yield err()


# =========================
# AGENT
# =========================
class BookingAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are a helpful medical booking assistant.\n"
                "Users may say phone numbers as words like 'zero one one'. "
                "You must interpret them as digits."
            )
        )


# =========================
# AGENTS
# =========================
def get_agent_ar(room_name: str):
    return AgentSession(
        llm=BookingLLM(room_name),
        stt=deepgram.STT(language="ar"),
        tts=elevenlabs.TTS(
            model="eleven_flash_v2_5",
            voice_id=os.getenv("ELEVENLABS_VOICE_ID_AR")
        ),
        vad=silero.VAD.load(min_silence_duration=0.3)
    ), BookingAssistant()


def get_agent_en(room_name: str):
    return AgentSession(
        llm=BookingLLM(room_name),
        stt=deepgram.STT(language="en"),
        tts=elevenlabs.TTS(
            model="eleven_flash_v2_5",
            voice_id=os.getenv("ELEVENLABS_VOICE_ID_EN")
        ),
        vad=silero.VAD.load(min_silence_duration=0.3)
    ), BookingAssistant()