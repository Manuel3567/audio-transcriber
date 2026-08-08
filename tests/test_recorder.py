import numpy as np
import pytest
from audio_transcriber.recorder import SoundDeviceRecorder


def test_concatenates_multiple_chunks_from_both_streams():
    """Verify multiple chunks from both streams are concatenated correctly."""
    recorder = SoundDeviceRecorder()

    mic_chunks = [
        np.ones((100, 1), dtype=np.float32) * 0.1,
        np.ones((100, 1), dtype=np.float32) * 0.1,
        np.ones((100, 1), dtype=np.float32) * 0.1,
    ]
    sys_chunks = [
        np.ones((100, 2), dtype=np.float32) * 0.1,
        np.ones((100, 2), dtype=np.float32) * 0.1,
        np.ones((100, 2), dtype=np.float32) * 0.1,
    ]

    result = recorder._merge_and_normalize(mic_chunks, sys_chunks)

    assert result is not None
    assert len(result) == 300


def test_returns_none_on_empty_chunks():
    """Verify returns None if either stream is empty."""
    recorder = SoundDeviceRecorder()

    sys_chunks = [np.ones((100, 2), dtype=np.float32)]
    assert recorder._merge_and_normalize([], sys_chunks) is None

    mic_chunks = [np.ones((100, 1), dtype=np.float32)]
    assert recorder._merge_and_normalize(mic_chunks, []) is None


def test_handles_mismatched_stream_lengths():
    """Verify uses min_len when mic and system streams have different lengths."""
    recorder = SoundDeviceRecorder()

    mic_chunks = [np.ones((2000, 1), dtype=np.float32) * 0.2]
    sys_chunks = [np.ones((1500, 2), dtype=np.float32) * 0.4]

    result = recorder._merge_and_normalize(mic_chunks, sys_chunks)

    # Should use min_len (1500)
    assert result is not None
    assert len(result) == 1500

def test_normalize_audio_scales_to_target_rms():
    """Verify audio is normalized to target RMS level."""
    recorder = SoundDeviceRecorder()

    audio = np.ones(16000, dtype=np.float32) * 0.5
    normalized = recorder._normalize_audio(audio)

    rms = np.sqrt(np.mean(normalized ** 2))
    assert abs(rms - 0.1) < 0.01


def test_normalize_audio_clips_to_range():
    """Verify audio is clipped to [-1, 1]."""
    recorder = SoundDeviceRecorder()

    audio = np.array([0.5, -0.5, 2.0, -3.0], dtype=np.float32)
    normalized = recorder._normalize_audio(audio)

    assert np.all(normalized >= -1.0)
    assert np.all(normalized <= 1.0)


def test_normalize_audio_handles_zero_rms():
    """Verify normalize handles silent audio."""
    recorder = SoundDeviceRecorder()

    audio = np.zeros(16000, dtype=np.float32)
    normalized = recorder._normalize_audio(audio)

    assert np.array_equal(normalized, audio)
