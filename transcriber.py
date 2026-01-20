"""Whisper API transcription module."""

import io
from openai import OpenAI
from config import OPENAI_API_KEY, WHISPER_MODEL


class Transcriber:
    """Transcribes audio using OpenAI Whisper API."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found. Please set it in .env file."
            )
        self._client = OpenAI(api_key=OPENAI_API_KEY)

    def transcribe(self, audio_buffer: io.BytesIO) -> str:
        """
        Transcribe audio buffer to text.

        Args:
            audio_buffer: WAV audio data as BytesIO buffer

        Returns:
            Transcribed text string
        """
        if audio_buffer.getbuffer().nbytes == 0:
            return ""

        try:
            # Reset buffer position
            audio_buffer.seek(0)

            # Create a file-like object with a name attribute
            audio_buffer.name = "audio.wav"

            response = self._client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_buffer,
            )

            return response.text.strip()

        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
