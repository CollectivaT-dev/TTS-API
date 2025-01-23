# utils/config_validator.py
from typing import Dict, Any
from .exceptions import ConfigurationError

REQUIRED_MODEL_FIELDS = {
    'coqui': ['voice', 'lang', 'model_type', 'tts_config_path', 'tts_model_path'],
    'mms': ['voice', 'lang', 'model_type', 'base_model_path']
}

# Optional fields that should have specific types if present
OPTIONAL_FIELD_TYPES = {
    'mms': {
        'checkpoint_name': str,
        'use_cuda': bool,
        'load': bool
    },
    'coqui': {
        'vocoder_config_path': str,
        'vocoder_model_path': str,
        'preprocessor': str,
        'use_cuda': bool,
        'load': bool
    }
}

def validate_config(config: Dict[str, Any]) -> None:
    """Validate the configuration file"""
    if not isinstance(config, dict):
        raise ConfigurationError("Configuration must be a dictionary")
        
    if 'languages' not in config:
        raise ConfigurationError("Configuration must contain 'languages' section")
        
    if 'models' not in config:
        raise ConfigurationError("Configuration must contain 'models' section")
        
    for model_config in config['models']:
        model_type = model_config.get('model_type')
        if not model_type:
            raise ConfigurationError("Each model must specify 'model_type'")
            
        if model_type not in REQUIRED_MODEL_FIELDS:
            raise ConfigurationError(f"Unknown model_type: {model_type}")
            
        # Check required fields
        for field in REQUIRED_MODEL_FIELDS[model_type]:
            if field not in model_config:
                raise ConfigurationError(
                    f"Model {model_config.get('voice', 'unknown')} missing required field: {field}"
                )
        
        # Check optional fields have correct types if present
        if model_type in OPTIONAL_FIELD_TYPES:
            for field, expected_type in OPTIONAL_FIELD_TYPES[model_type].items():
                if field in model_config and not isinstance(model_config[field], expected_type):
                    raise ConfigurationError(
                        f"Field '{field}' in model {model_config.get('voice', 'unknown')} "
                        f"must be of type {expected_type.__name__}"
                    )