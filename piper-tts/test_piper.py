#!/usr/bin/env python3
"""Test Piper TTS for bedtime stories"""
import json
from piper import PiperVoice

# Load voice
with open("/root/.openclaw/workspace/piper-tts/voices/en_US-amy-low.json", "r") as f:
    config = json.load(f)

voice = PiperVoice(
    config_path="/root/.openclaw/workspace/piper-tts/voices/en_US-amy-low.json",
    onnx_path="/root/.openclaw/workspace/piper-tts/voices/en_US-amy-low.onnx"
)

# Test with a bedtime story
text = "Once upon a time, in a magical forest full of twinkling stars, there lived a little owl named Plubar. Plubar had big golden eyes and soft grey feathers. Every night, Plubar would fly through the forest, singing gentle songs to help all the baby animals fall asleep."

# Generate audio
import io
import wave

audio_bytes = io.BytesIO()
voice.synthesize_to_file(
    text,
    audio_bytes,
    length_scale=1.0,
)
audio_bytes.seek(0)

# Save to file
with wave.open("/root/.openclaw/workspace/piper-tts/test-story.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(22050)
    wf.writeframes(audio_bytes.read())

print("✅ Generated: /root/.openclaw/workspace/piper-tts/test-story.wav")
