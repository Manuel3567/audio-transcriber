import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from audio_transcriber.cli import main


def test_setup_command(monkeypatch, capsys):
    """Verify 'setup' command calls setup function."""
    setup_called = []

    def mock_setup():
        setup_called.append(True)

    monkeypatch.setattr("audio_transcriber.cli.setup", mock_setup)
    monkeypatch.setattr("sys.argv", ["audio-transcriber", "setup"])

    main()
    assert setup_called


def test_teardown_command(monkeypatch):
    """Verify 'teardown' command calls teardown function."""
    teardown_called = []

    def mock_teardown():
        teardown_called.append(True)

    monkeypatch.setattr("audio_transcriber.cli.teardown", mock_teardown)
    monkeypatch.setattr("sys.argv", ["audio-transcriber", "teardown"])

    main()
    assert teardown_called


def test_transcribe_command_without_config(monkeypatch, capsys):
    """Verify transcribe handles missing config gracefully."""
    monkeypatch.setattr(
        "audio_transcriber.cli.load_device_config",
        lambda: {}
    )
    monkeypatch.setattr("sys.argv", ["audio-transcriber", "transcribe"])

    main()

    captured = capsys.readouterr()
    assert "Device not configured" in captured.out


def test_transcribe_command_with_config(monkeypatch):
    """Verify transcribe command calls transcribe with correct args."""
    transcribe_calls = []

    def mock_transcribe(mic_id, system_id, summarize=False):
        transcribe_calls.append((mic_id, system_id, summarize))

    monkeypatch.setattr(
        "audio_transcriber.cli.load_device_config",
        lambda: {"microphone_device_id": 2, "system_audio_device_id": 3}
    )
    monkeypatch.setattr("audio_transcriber.cli.transcribe", mock_transcribe)
    monkeypatch.setattr("sys.argv", ["audio-transcriber", "transcribe"])

    main()

    assert len(transcribe_calls) == 1
    assert transcribe_calls[0] == (2, 3, False)


def test_transcribe_command_with_summary_flag(monkeypatch):
    """Verify --summary flag is passed to transcribe."""
    transcribe_calls = []

    def mock_transcribe(mic_id, system_id, summarize=False):
        transcribe_calls.append((mic_id, system_id, summarize))

    monkeypatch.setattr(
        "audio_transcriber.cli.load_device_config",
        lambda: {"microphone_device_id": 2, "system_audio_device_id": 3}
    )
    monkeypatch.setattr("audio_transcriber.cli.transcribe", mock_transcribe)
    monkeypatch.setattr("sys.argv", ["audio-transcriber", "transcribe", "--summary"])

    main()

    assert len(transcribe_calls) == 1
    assert transcribe_calls[0] == (2, 3, True)


def test_no_command_shows_help(monkeypatch, capsys):
    """Verify no command shows help."""
    monkeypatch.setattr("sys.argv", ["audio-transcriber"])

    main()

    captured = capsys.readouterr()
    assert "usage:" in captured.out or "usage:" in captured.err
