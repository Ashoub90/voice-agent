import os
import time
import httpx
from contextlib import asynccontextmanager

from livekit.agents import Agent, AgentSession
from livekit.agents.llm import LLM
from livekit.plugins import deepgram, elevenlabs, silero


API_URL = "http://localhost:8000/chat/"


class BookingLLM(LLM):

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

            print("🎤 USER:", user_text)

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    API_URL,
                    json={
                        "session_id": "voice-session",
                        "message": user_text,
                    }
                )

            reply = res.json().get("reply", "")

            print("🤖 AGENT:", reply)

            async def stream():
                for word in reply.split():
                    yield word + " "

            yield stream()

        except Exception as e:
            async def err():
                yield f"error: {str(e)}"
            yield err()


class BookingAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful medical booking assistant."
        )


# 🔥 ARABIC AGENT
def get_agent_ar():
    return AgentSession(
        llm=BookingLLM(),
        stt=deepgram.STT(language="ar"),
        tts=elevenlabs.TTS(
            model="eleven_flash_v2_5",
            voice_id=os.getenv("ELEVENLABS_VOICE_ID_AR")
        ),
        vad=silero.VAD.load(min_silence_duration=0.3)
    ), BookingAssistant()


# 🔥 ENGLISH AGENT
def get_agent_en():
    return AgentSession(
        llm=BookingLLM(),
        stt=deepgram.STT(language="en"),
        tts=elevenlabs.TTS(
            model="eleven_flash_v2_5",
            voice_id=os.getenv("ELEVENLABS_VOICE_ID_EN")
        ),
        vad=silero.VAD.load(min_silence_duration=0.3)
    ), BookingAssistant()