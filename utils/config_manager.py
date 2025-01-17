# utils/config_manager.py
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import os
import json
from utils.exceptions import ConfigurationError

@dataclass
class ModelConfig:
    voice: str
    lang: str
    model_type: str
    base_model_path: Optional[str] = None
    tts_config_path: Optional[str] = None
    tts_model_path: Optional[str] = None
    vocoder_config_path: Optional[str] = None
    vocoder_model_path: Optional[str] = None
    checkpoint_name: Optional[str] = None
    load: bool = False
    use_cuda: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'ModelConfig':
        return cls(**{
            k: v for k, v in data.items() 
            if k in cls.__annotations__
        })

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = self._load_config()
        self._apply_env_overrides()
        self._validate()
        
    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Config file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config: {e}")

    def _apply_env_overrides(self):
        """Override config values with environment variables"""
        # Global settings
        if 'USE_CUDA' in os.environ:
            for model in self._config['models']:
                model['use_cuda'] = os.environ['USE_CUDA'] == '1'

        # Models root override
        if 'MODELS_ROOT' in os.environ:
            self._config['models_root'] = os.environ['MODELS_ROOT']

    def _validate(self):
        """Validate the loaded configuration"""
        if 'languages' not in self._config:
            raise ConfigurationError("Missing 'languages' section")
        if 'models' not in self._config:
            raise ConfigurationError("Missing 'models' section")

    @property
    def models(self) -> List[dict]:
        """Get list of model configs"""
        return self._config['models']

    @property
    def languages(self) -> Dict[str, str]:
        """Get supported languages mapping"""
        return self._config['languages']

    @property
    def models_root(self) -> str:
        """Get models root directory"""
        return self._config.get('models_root', 'models')

    def use_cuda(self) -> bool:
        """Get CUDA setting"""
        env_cuda = os.getenv('USE_CUDA', '0')
        return env_cuda == '1'

    def get_model_config(self, voice: str) -> Optional[dict]:
        """Get specific model configuration by voice name"""
        for model in self.models:
            if model['voice'] == voice:
                return model
        return None