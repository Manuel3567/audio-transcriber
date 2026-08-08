from pathlib import Path
from dataclasses import dataclass
import numpy as np
import whisper
from audio_transcriber.protocols import (
    AudioRecorder,
    Transcriber,
    Summarizer,
)

WHISPER_MODEL = "large"
LANGUAGE = "de"
TRANSCRIPT_FILE = "transcript.txt"

@dataclass
class TranscribeSession:
    """Configuration for a transcription session."""
    mic_id: int | None
    system_id: int | None
    summarize: bool = False

class WhisperTranscriber:
    """Real Whisper transcriber implementation."""
    def __init__(self, model_name: str = WHISPER_MODEL, language: str = LANGUAGE):
        self.model_name = model_name
        self.language = language
        self._model = None

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio with Whisper."""
        print("🎯 Transcribing...")
        if self._model is None:
            self._model = whisper.load_model(self.model_name)
        result = self._model.transcribe(audio, language=self.language)
        return result["text"]


def save_transcript(transcript: str, transcript_file: str = TRANSCRIPT_FILE) -> Path:
    """Save transcript to file with auto-incrementing name. Return the saved path."""
    base_path = Path(transcript_file)
    counter = 1
    while (base_path.parent / f"{base_path.stem}_{counter}{base_path.suffix}").exists():
        counter += 1

    file_path = base_path.parent / f"{base_path.stem}_{counter}{base_path.suffix}"
    with open(file_path, "w") as f:
        f.write(transcript + "\n")
    print(f"✓ Saved to {file_path}")
    return file_path


def run_transcription_session(
    session: TranscribeSession,
    recorder: AudioRecorder,
    transcriber: Transcriber,
    summarizer: Summarizer,
) -> None:
    """Main transcription workflow."""

    audio = recorder.record(session.mic_id, session.system_id)
    transcript = transcriber.transcribe(audio)
    print(transcript)
    save_transcript(transcript)

    if session.summarize:
        summarizer.summarize(transcript)
