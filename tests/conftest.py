# tests/conftest.py
import pytest
import sys
import os
from pathlib import Path
import io
import json
import tempfile
import numpy

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import AFTER setting up path
from flask import Flask
from server import app
from utils.config_manager import ConfigManager

@pytest.fixture
def client():
    """Test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_client():
    """Test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_config_file():
    """Creates a temporary config file for testing"""
    config_content = {
        "languages": {"en": "English", "rmz": "Marma"},
        "models": [
            {
                "voice": "test-mms",
                "lang": "rmz",
                "model_type": "mms",
                "base_model_path": "test_path",
                "load": True
            },
            {
                "voice": "test-coqui",
                "lang": "en",
                "model_type": "coqui",
                "tts_config_path": "test_config.json",
                "tts_model_path": "test_model.pth",
                "load": True
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(config_content, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)

@pytest.fixture
def mock_model():
    """Creates a mock model for testing"""
    class MockModel:
        def synthesize(self, text):
            return io.BytesIO(b'\x00' * 1000)
        
        def load_model(self):
            return True
        
        @property
        def sample_rate(self):
            return 22050
    
    return MockModel()

@pytest.fixture
def mock_loaded_models(mock_model):
    """Creates mock loaded_models dictionary"""
    return {
        "test-mms": {
            "model": mock_model,
            "lang": "rmz",
            "voice": "test-mms",
            "language": "Marma",
            "preprocessor": None,
            "framerate": 22050
        },
        "test-coqui": {
            "model": mock_model,
            "lang": "en",
            "voice": "test-coqui",
            "language": "English",
            "preprocessor": None,
            "framerate": 22050
        }
    }

# Patch the loaded_models in the app context
@pytest.fixture(autouse=True)
def patch_loaded_models(mock_loaded_models, monkeypatch):
    """Automatically patch loaded_models in the app context"""
    import server
    monkeypatch.setattr(server, 'loaded_models', mock_loaded_models)
    monkeypatch.setattr(server, 'default_model_ids', {
        'rmz': 'test-mms',
        'en': 'test-coqui'
    })