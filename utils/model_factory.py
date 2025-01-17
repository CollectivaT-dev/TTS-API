# utils/model_factory.py
from typing import Dict, Type
import logging
from utils.exceptions import ConfigurationError
from .backends.base import TTSModelWrapper
from .backends.coqui import CoquiWrapper
from .backends.mms import MMSWrapper

class TTSModelFactory:
    _backend_map: Dict[str, Type[TTSModelWrapper]] = {
        'coqui': CoquiWrapper,
        'mms': MMSWrapper
    }
    
    @classmethod
    def register_backend(cls, name: str, backend_class: Type[TTSModelWrapper]):
        """Register a new backend implementation"""
        cls._backend_map[name] = backend_class
    
    @classmethod
    def create_model(cls, config: dict) -> TTSModelWrapper:
        """Create a model instance based on configuration"""
        model_type = config.get('model_type')
        if not model_type:
            raise ConfigurationError("model_type not specified in config")
            
        if model_type not in cls._backend_map:
            raise ConfigurationError(f"Unknown model_type: {model_type}")
            
        model_class = cls._backend_map[model_type]
        return model_class(config)