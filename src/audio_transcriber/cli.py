#!/usr/bin/env python3
import argparse
from audio_transcriber.setup import setup, teardown
from audio_transcriber.transcriber import transcribe
from audio_transcriber.config import load_device_config


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
        config = load_device_config()
        transcribe(config.get("microphone_device_id"), config.get("system_audio_device_id"), args.summary)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
