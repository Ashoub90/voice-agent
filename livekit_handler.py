import os
import httpx
import asyncio
import re
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from livekit.agents import Agent, AgentSession
from livekit.agents.llm import LLM
from livekit.plugins import deepgram, elevenlabs, silero

load_dotenv()

API_URL = "http://localhost:8000/chat/"

# =========================
# PHONE NORMALIZATION
# =========================
def normalize_phone(text: str) -> str:
    mapping = {
        "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3",
        "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "صفر": "0", "واحد": "1", "اتنين": "2", "اثنين": "2", "تلاتة": "3", "ثلاثة": "3",
        "اربعة": "4", "أربعة": "4", "خمسة": "5", "ستة": "6", "سبعة": "7", "تمانية": "8", "ثمانية": "8", "تسعة": "9"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    digits = []
    for w in words:
        if w in mapping: digits.append(mapping[w])
        elif w.isdigit(): digits.extend(list(w))
    if not digits: digits = re.findall(r'\d', text)
    return "".join(digits) if len(digits) >= 6 else ""

# =========================
# TTS FORMATTING UTILS
# =========================
def format_for_tts(text: str, is_arabic: bool) -> str:
    """Fixes digits, times, and years for natural speech."""
    
    # Remove any internal placeholder artifacts
    text = text.replace("YEAR_", "")

    arabic_digits_map = {
        "0": "صفر", "1": "واحد", "2": "اتنين", "3": "تلاتة", "4": "أربعة",
        "5": "خمسة", "6": "ستة", "7": "سبعة", "8": "تمانية", "9": "تسعة"
    }

    # 1. FIX TIMES (e.g., 11:00)
    def format_time_logic(match):
        hr, mn = match.groups()
        if is_arabic:
            prefix = "الساعة " if "الساعة" not in text else ""
            if mn and mn != "00":
                return f"{prefix}{hr} و {mn} دقيقة"
            return f"{prefix}{hr}"
        return f"{hr} {mn}" if mn and mn != "00" else f"{hr} o'clock"

    text = re.sub(r'(\d{1,2}):(\d{2})', format_time_logic, text)

    # 2. FIX DIGIT STRINGS (Phone numbers)
    def replace_with_words(match):
        val = match.group(0)
        # Protect years (4 digits starting with 19 or 20)
        if len(val) == 4 and (val.startswith("20") or val.startswith("19")):
            return val
        
        digits = list(val)
        if is_arabic:
            return " " + " ".join([arabic_digits_map.get(d, d) for d in digits]) + " "
        return " " + " ".join(digits) + " "

    # Apply to strings of 3+ digits
    text = re.sub(r'\d{3,}', replace_with_words, text)

    return re.sub(r'\s+', ' ', text).strip()

# =========================
# LLM CLASS
# =========================
class BookingLLM(LLM):
    def __init__(self, room_name: str):
        super().__init__()
        self.room_name = room_name
        self.phone_candidate = None
        self.phone_confirmed = False
        self.phone_sent = False 
        self.session_is_arabic = None # Sticky Language State

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

            # --- STICKY LANGUAGE DETECTION ---
            current_is_arabic = any("\u0600" <= c <= "\u06FF" for c in user_text)
            if self.session_is_arabic is None or (current_is_arabic and not self.session_is_arabic):
                self.session_is_arabic = current_is_arabic
            
            use_arabic = self.session_is_arabic
            lower = user_text.lower()

            # 1. DETECT CONFIRMATION
            if any(x in lower for x in ["yes", "نعم", "أيوة", "تمام", "ايوه", "أيووه"]) and self.phone_candidate:
                self.phone_confirmed = True

            if any(x in lower for x in ["no", "لا", "لأ", "مش ده"]):
                self.phone_candidate = None
                self.phone_confirmed = False
                self.phone_sent = False

            # 2. EXTRACT NEW NUMBER
            curr_normalized = normalize_phone(user_text)

            # 3. ASK FOR CONFIRMATION (Respects Sticky Language)
            if curr_normalized and not self.phone_confirmed:
                self.phone_candidate = curr_normalized
                if use_arabic:
                    raw_reply = f"هل هذا هو رقم تليفونك: {curr_normalized}؟"
                else:
                    raw_reply = f"Is this your phone number: {curr_normalized}?"
                
                formatted_reply = format_for_tts(raw_reply, use_arabic)
                async def stream():
                    for word in formatted_reply.split(): yield word + " "
                yield stream()
                return

            # 4. SEND TO BACKEND
            message_to_send = user_text
            
            if self.phone_confirmed and self.phone_candidate and not self.phone_sent:
                if use_arabic:
                    message_to_send = f"رقم التليفون المؤكد هو {self.phone_candidate}. ابحث عن الملف الآن."
                else:
                    message_to_send = f"Confirmed phone: {self.phone_candidate}. Perform lookup."
                self.phone_sent = True

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(API_URL, json={"session_id": self.room_name, "message": message_to_send})
            
            reply = res.json().get("reply", "")
            formatted_reply = format_for_tts(reply, use_arabic)

            async def stream():
                for word in formatted_reply.split(): yield word + " "
            yield stream()

        except Exception as e:
            async def err(): yield f"error: {str(e)}"
            yield err()

# =========================
# AGENT SETUP
# =========================
def get_agent_ar(room_name: str):
    return AgentSession(
        llm=BookingLLM(room_name),
        stt=deepgram.STT(language="ar"),
        tts=elevenlabs.TTS(model="eleven_multilingual_v2", voice_id=os.getenv("ELEVENLABS_VOICE_ID_AR")),
        vad=silero.VAD.load(min_silence_duration=1.0) # VAD Patience
    ), Agent(instructions="Helpful Medical Assistant.")

def get_agent_en(room_name: str):
    return AgentSession(
        llm=BookingLLM(room_name),
        stt=deepgram.STT(language="en"),
        tts=elevenlabs.TTS(model="eleven_flash_v2_5", voice_id=os.getenv("ELEVENLABS_VOICE_ID_EN")),
        vad=silero.VAD.load(min_silence_duration=1.0) # VAD Patience
    ), Agent(instructions="Helpful Medical Assistant.")