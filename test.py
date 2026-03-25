import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

speech_key = os.getenv("AZURE_TTS_KEY")
service_region = os.getenv("AZURE_TTS_REGION")

speech_config = speechsdk.SpeechConfig(
    subscription=speech_key,
    region=service_region
)

speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"

audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_config
)

text = "Hello, this is a test."

result = synthesizer.speak_text_async(text).get()

print(result.reason)