## Challenges & Limitations

### System / Architecture
- Initially attempted a custom WebSocket-based voice pipeline for full control, but it became too complex to maintain (audio streaming, synchronization, state handling), leading to adoption of LiveKit.
- While LiveKit simplified real-time audio, it introduced challenges due to limited documentation for internal agent APIs, requiring significant trial-and-error to implement custom behaviors (e.g., TTS adapters, session handling).
- Voice sessions are stateful and language-bound, making it difficult to switch language mid-conversation. This required separate agents per language and early language selection in the UI.

### LLM + Tooling Limitations
- Early issues with LLM hallucinations (e.g., incorrect appointment IDs, wrong availability decisions) required enforcing:
  - strict tool usage rules
  - structured tool outputs
  - session-based state tracking
- Aligning prompt logic with backend tools was critical to avoid inconsistencies (AutoQA-style alignment issues).

### Speech (Hardest Part)
- Arabic TTS quality was the biggest challenge:
  - Mispronunciation of numbers, times, and names
  - Inconsistent tone and clarity
  - Required heavy preprocessing (formatting numbers, times, etc.)

- Comparison of TTS options:
  - ElevenLabs → 4.5/5 (best quality, expensive)
  - Azure TTS → 3/5 (stable but harder to integrate with LiveKit)
  - Local models → 2/5 (not production-ready for Arabic)

- Numeric speech (e.g., phone numbers, times) required manual formatting, as TTS engines do not handle structured data well.

### Multilingual Challenges
- Language detection needed to be “sticky” per session to prevent mid-conversation switching (e.g., Arabic → English randomly).
- Mixed-language inputs caused inconsistencies in both STT and TTS.
- Some responses appeared in text but were not spoken correctly due to TTS formatting mismatches.

### Conversation & State Issues
- Handling phone numbers in voice required:
  - normalization (spoken → digits)
  - confirmation loop
  - retry logic

- Without strict state control, the agent could:
  - repeatedly ask for the same input
  - send incomplete data to backend

- Real-time systems exposed race conditions between:
  - STT input
  - LLM response
  - TTS playback

### Performance & UX
- Latency is still noticeable due to:
  - STT → LLM → TTS pipeline chaining

- Streaming improves UX but introduces complexity in synchronization.

- VAD tuning (silence detection) required balancing:
  - responsiveness vs interruptions

### Current Limitations
- Language cannot be changed mid-session
- Arabic voice quality still not production-perfect
- TTS requires preprocessing (not plug-and-play)
- No persistent memory layer (planned via Redis)
- Limited channel support (currently web only)

### Future Improvements
- Redis for session memory and scalability
- WhatsApp / Messenger integration
- Better Arabic TTS handling (or hybrid approach)
- Smarter time/number formatting layer
- Multi-channel support (voice, chat, telephony)