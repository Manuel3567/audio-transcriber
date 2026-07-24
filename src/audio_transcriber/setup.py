#!/usr/bin/env python3
import subprocess
import sys
import sounddevice as sd
from audio_transcriber.config import save_device_config


def ensure_blackhole_installed() -> None:
    """Install BlackHole if not already present."""
    if subprocess.run(["brew", "list", "blackhole-2ch"], capture_output=True).returncode != 0:
        print("Installing BlackHole...")
        subprocess.run(["brew", "install", "blackhole-2ch"], capture_output=True)
    print("✓ BlackHole ready")


def display_devices(devices: list) -> None:
    """Display all available audio devices."""
    print("\nAvailable audio devices:")
    for i, d in enumerate(devices):
        print(f"  {i}: {d['name']}")


def find_blackhole_device(devices: list) -> int | None:
    """Auto-detect BlackHole 2ch device, return ID or None."""
    for i, d in enumerate(devices):
        if "blackhole" in d["name"].lower() and "2ch" in d["name"].lower():
            return i
    return None


def prompt_for_microphone_id(devices: list) -> int:
    """Prompt user to select microphone device."""
    first_input = next((i for i, d in enumerate(devices) if d.get("max_input_channels", 0) > 0), None)
    default_prompt = f" [default: {first_input}]" if first_input is not None else ""

    while True:
        try:
            user_input = input(f"\nMicrophone device ID{default_prompt}: ").strip()
            mic_id = int(user_input) if user_input else first_input
            if 0 <= mic_id < len(devices):
                return mic_id
            print("Invalid device ID")
        except ValueError:
            print("Invalid input")


def prompt_for_blackhole_id(devices: list, auto_detected_id: int | None) -> int:
    """Prompt user for BlackHole device (with auto-detected default if available)."""
    if auto_detected_id is not None:
        print(f"Using BlackHole device {auto_detected_id}")
        return auto_detected_id

    while True:
        try:
            blackhole_id = int(input("BlackHole device ID: "))
            if 0 <= blackhole_id < len(devices):
                return blackhole_id
            print("Invalid device ID")
        except ValueError:
            print("Invalid input")


def display_setup_complete(mic_id: int, blackhole_id: int, devices: list) -> None:
    """Display completion message with next steps."""
    print(f"\n✓ Config saved!")
    print(f"  Microphone: {devices[mic_id]['name']}")
    print(f"  BlackHole: {devices[blackhole_id]['name']}")
    print("\nSetup instructions:")
    print("1. Open Audio MIDI Setup")
    print("2. Create Multi-Output Device with: BlackHole 2ch + your speaker/headphone")
    print("3. System Settings → Sound → Output → select Multiausgangsgerät")
    print("\nThen run: audio-transcriber transcribe")


def setup() -> None:
    """Orchestrate setup: install dependencies, configure devices, save config."""
    if sys.platform != "darwin":
        print("❌ macOS only")
        sys.exit(1)

    ensure_blackhole_installed()

    devices = sd.query_devices()
    display_devices(devices)

    blackhole_id = find_blackhole_device(devices)
    mic_id = prompt_for_microphone_id(devices)
    blackhole_id = prompt_for_blackhole_id(devices, blackhole_id)

    config = {"microphone_device_id": mic_id, "system_audio_device_id": blackhole_id}
    save_device_config(config)

    display_setup_complete(mic_id, blackhole_id, devices)
