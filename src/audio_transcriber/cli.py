#!/usr/bin/env python3
import json
import argparse
from pathlib import Path
from audio_transcriber.setup import setup, teardown
from audio_transcriber.transcriber import run_transcription_session, TranscribeSession
from audio_transcriber.recorder import SoundDeviceRecorder
from audio_transcriber.transcriber import WhisperTranscriber
from audio_transcriber.summarizer import ClaudeSummarizer


def main():
    parser = argparse.ArgumentParser(prog="audio-transcriber", description="Record and transcribe audio")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("setup", help="Configure audio devices and install BlackHole")
    subparsers.add_parser("teardown", help="Uninstall BlackHole and remove configuration")
    transcribe_cmd = subparsers.add_parser("transcribe", help="Record and transcribe audio")
    transcribe_cmd.add_argument("--summary", action="store_true", help="Summarize with Claude")

    args = parser.parse_args()

    if args.command == "setup":
        setup()
    elif args.command == "teardown":
        teardown()
    elif args.command == "transcribe":
        config_path = Path.cwd() / "config.json"
        try:
            config = json.loads(config_path.read_text()) if config_path.exists() else {}
        except (json.JSONDecodeError, IOError):
            config = {}

        if config and config.get("microphone_device_id") and config.get("system_audio_device_id"):
            session = TranscribeSession(
                mic_id=config["microphone_device_id"],
                system_id=config["system_audio_device_id"],
                summarize=args.summary,
            )
            run_transcription_session(
                session,
                recorder=SoundDeviceRecorder(),
                transcriber=WhisperTranscriber(),
                summarizer=ClaudeSummarizer(),
            )
        else:
            print("❌ Device not configured. Run: audio-transcriber setup")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
