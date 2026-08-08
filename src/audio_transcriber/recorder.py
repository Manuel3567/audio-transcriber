import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
TARGET_RMS = 0.1


class SoundDeviceRecorder:
    """Real audio recorder using sounddevice."""
    def record(self, mic_id: int, system_id: int) -> np.ndarray | None:
        """Record from microphone and system audio until Ctrl+C, return normalized mono audio or None."""
        mic_chunks, sys_chunks = [], []

        def mic_callback(indata, frames, time, status):
            mic_chunks.append(indata.copy())

        def sys_callback(indata, frames, time, status):
            sys_chunks.append(indata.copy())

        print("🎤 Recording... (Ctrl+C to stop)")
        try:
            with sd.InputStream(device=mic_id, samplerate=SAMPLE_RATE, channels=1, callback=mic_callback):
                with sd.InputStream(device=system_id, samplerate=SAMPLE_RATE, channels=2, callback=sys_callback):
                    while True:
                        sd.sleep(100)
        except KeyboardInterrupt:
            print("⏹ Stopping...")

        return self._merge_and_normalize(mic_chunks, sys_chunks)

    def _merge_and_normalize(self, mic_chunks: list, sys_chunks: list) -> np.ndarray | None:
        """Merge microphone and system audio, then normalize."""
        if not mic_chunks or not sys_chunks:
            print("No audio recorded")
            return None

        mic_audio = np.concatenate(mic_chunks, axis=0).astype(np.float32).flatten()
        sys_audio = np.concatenate(sys_chunks, axis=0).astype(np.float32).flatten()

        sys_mono = sys_audio.reshape(-1, 2).mean(axis=1)
        min_len = min(len(mic_audio), len(sys_mono))

        merged = (mic_audio[:min_len] + sys_mono[:min_len]) / 2
        return self._normalize_audio(merged)

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to target RMS level."""
        rms = np.sqrt(np.mean(audio ** 2))
        if rms > 0:
            audio = audio * (TARGET_RMS / rms)
            audio = np.clip(audio, -1.0, 1.0)
        return audio