from pathlib import Path
from audio_transcriber.models import (
    AudioRecorder,
    Transcriber,
    Summarizer,
    TranscribeSession,
    SoundDeviceRecorder,
    WhisperTranscriber,
    ClaudeSummarizer,
)

TRANSCRIPT_FILE = "transcript.txt"


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


def transcribe(
    session: TranscribeSession,
    recorder: AudioRecorder,
    transcriber: Transcriber,
    summarizer: Summarizer,
    transcript_file: str = TRANSCRIPT_FILE,
) -> None:
    """Main transcription workflow."""

    audio = recorder.record(session.mic_id, session.system_id)
    transcript = transcriber.transcribe(audio)
    print(transcript)
    save_transcript(transcript, transcript_file)

    if session.summarize:
        summarizer.summarize(transcript)
