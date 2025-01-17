# utils/exceptions.py

class TTSAPIError(Exception):
    """Base exception for TTS API errors"""
    pass

class ModelLoadError(TTSAPIError):
    """Raised when a model fails to load"""
    pass

class SynthesisError(TTSAPIError):
    """Raised when text synthesis fails"""
    pass

class ConfigurationError(TTSAPIError):
    """Raised when there's an error in configuration"""
    pass

class PreprocessorError(TTSAPIError):
    """Raised when text preprocessing fails"""
    pass
