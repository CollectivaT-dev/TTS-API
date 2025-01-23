# tests/test_models.py
import pytest
import io
import numpy as np
from utils.backends.mms import MMSWrapper
from utils.exceptions import SynthesisError

def test_mms_wrapper_init():
    """Test MMS wrapper initialization"""
    config = {
        "voice": "test-mms",
        "lang": "rmz",
        "model_type": "mms",
        "base_model_path": "test_path"
    }
    wrapper = MMSWrapper(config)
    assert wrapper.config == config
    assert wrapper.sample_rate_val == 16000

class MockPipeline:
    def __call__(self, text):
        # Mimic transformers pipeline output
        return {
            "audio": [np.zeros(1000, dtype=np.float32)],
            "sampling_rate": 16000
        }

def test_mms_synthesis():
    """Test MMS wrapper synthesis"""
    config = {
        "voice": "test-mms",
        "lang": "rmz",
        "model_type": "mms",
        "base_model_path": "test_path"
    }
    wrapper = MMSWrapper(config)
    wrapper.synthesizer = MockPipeline()
    
    result = wrapper.synthesize("test text")
    assert isinstance(result, io.BytesIO)

def test_synthesis_without_model():
    """Test synthesis without loaded model"""
    config = {
        "voice": "test-mms",
        "lang": "rmz",
        "model_type": "mms",
        "base_model_path": "test_path"
    }
    wrapper = MMSWrapper(config)
    
    with pytest.raises(SynthesisError, match="Synthesizer not initialized"):
        wrapper.synthesize("test text")