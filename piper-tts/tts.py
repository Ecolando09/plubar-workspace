#!/usr/bin/env python3
"""Piper TTS for bedtime stories - Local, privacy-focused"""
import subprocess
import json
from pathlib import Path

VOICE_DIR = Path("/root/.openclaw/workspace/piper-tts/voices")
PIPER_BIN = Path("/root/.openclaw/workspace/piper-tts/venv/bin/piper")

def synthesize(text: str, output_path: str, voice: str = "en_US-amy-low"):
    """Generate audio from text"""
    voice_path = VOICE_DIR / f"{voice}.onnx"
    config_path = VOICE_DIR / f"{voice}.onnx.json"
    
    # Write text to temp file
    text_file = Path(output_path).with_suffix(".txt")
    text_file.write_text(text)
    
    # Run piper
    subprocess.run([
        str(PIPER_BIN),
        "-m", str(voice_path),
        "-c", str(config_path),
        "-f", output_path,
        "-i", str(text_file)
    ], check=True)
    
    # Clean up temp text file
    text_file.unlink()
    
    return output_path

if __name__ == "__main__":
    # Test with a bedtime story
    story = """Once upon a time, in a magical forest full of twinkling stars, 
    there lived a little owl named Plubar. Plubar had big golden eyes and 
    soft grey feathers. Every night, Plubar would fly through the forest, 
    singing gentle songs to help all the baby animals fall asleep."""
    
    synthesize(story, "/root/.openclaw/workspace/piper-tts/bedtime-story.wav")
    print("✅ Generated: /root/.openclaw/workspace/piper-tts/bedtime-story.wav")
