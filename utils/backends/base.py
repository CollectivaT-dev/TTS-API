# utils/backends/base.py
from abc import ABC, abstractmethod
import io

class TTSModelWrapper(ABC):
    """Base class for TTS model implementations"""
    
    @abstractmethod
    def __init__(self, model_config: dict):
        """Initialize the model wrapper with config"""
        pass
    
    @abstractmethod
    def load_model(self) -> bool:
        """Load the model into memory"""
        pass
    
    @abstractmethod
    def synthesize(self, text: str) -> io.BytesIO:
        """Convert text to speech, return audio buffer"""
        pass
    
    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Get model's output sample rate"""
        pass