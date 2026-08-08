import json
from pathlib import Path
import pytest
from audio_transcriber.setup import save_config


def test_save_config(tmp_path):
    """Verify config is saved with correct structure."""
    config = {"microphone_device_id": 2, "system_audio_device_id": 5}
    config_file = tmp_path / "test_config.json"

    save_config(config, config_file)

    assert config_file.exists()
    saved = json.loads(config_file.read_text())
    assert saved == config
