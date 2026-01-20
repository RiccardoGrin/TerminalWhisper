"""Audio recording module using sounddevice."""

import io
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from config import SAMPLE_RATE, CHANNELS, DTYPE


class AudioRecorder:
    """Records audio from the microphone."""

    def __init__(self):
        self._chunks: list[np.ndarray] = []
        self._stream = None
        self._is_recording = False

    def _audio_callback(self, indata, frames, time, status):
        """Callback function called for each audio block."""
        if status:
            print(f"Audio status: {status}")
        if self._is_recording:
            self._chunks.append(indata.copy())

    def start(self):
        """Start recording audio."""
        self._chunks = []
        self._is_recording = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> io.BytesIO:
        """Stop recording and return audio as WAV buffer."""
        self._is_recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._chunks:
            return io.BytesIO()

        # Concatenate all chunks
        audio_data = np.concatenate(self._chunks, axis=0)

        # Convert to WAV format in memory
        buffer = io.BytesIO()
        wavfile.write(buffer, SAMPLE_RATE, audio_data)
        buffer.seek(0)

        return buffer

    @property
    def is_recording(self) -> bool:
        """Return whether recording is active."""
        return self._is_recording
