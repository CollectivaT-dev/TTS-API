# tests/test_config.py
import pytest
from utils.config_manager import ConfigManager
from utils.exceptions import ConfigurationError

def test_config_loading(mock_config_file):
    """Test basic config loading"""
    config_manager = ConfigManager(mock_config_file)
    assert len(config_manager.models) == 2
    assert 'en' in config_manager.languages
    assert 'rmz' in config_manager.languages

def test_models_root_default(mock_config_file):
    """Test default models_root value"""
    config_manager = ConfigManager(mock_config_file)
    assert config_manager.models_root == 'models'

def test_use_cuda_from_env(mock_config_file, monkeypatch):
    """Test CUDA setting from environment variable"""
    monkeypatch.setenv('USE_CUDA', '1')
    config_manager = ConfigManager(mock_config_file)
    assert config_manager.use_cuda() == True

def test_invalid_config_file():
    """Test handling of invalid config file"""
    with pytest.raises(ConfigurationError):
        ConfigManager('nonexistent_config.json')