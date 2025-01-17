# utils/backends/coqui.py
import io
import os
import logging
from TTS.utils.synthesizer import Synthesizer
from .base import TTSModelWrapper
from utils.exceptions import ModelLoadError, SynthesisError

class CoquiWrapper(TTSModelWrapper):
    """Wrapper for Coqui-TTS models"""
    
    def __init__(self, model_config: dict):
        """Initialize the Coqui wrapper with config
        
        Args:
            model_config (dict): Configuration dictionary containing model paths and settings
        """
        self.config = model_config
        self.synthesizer = None
        self.sample_rate_val = None
        self.models_root = os.getenv('MODELS_ROOT', 'models')
        
    def load_model(self) -> bool:
        """Load the Coqui model into memory
        
        Returns:
            bool: True if model loaded successfully
            
        Raises:
            ModelLoadError: If model loading fails
        """
        try:
            # Construct full paths
            tts_checkpoint = os.path.join(self.models_root, self.config['tts_model_path'])
            tts_config = os.path.join(self.models_root, self.config['tts_config_path'])
            
            if not os.path.exists(tts_checkpoint):
                raise ModelLoadError(f"TTS model not found at {tts_checkpoint}")
            if not os.path.exists(tts_config):
                raise ModelLoadError(f"TTS config not found at {tts_config}")
            
            # Handle vocoder paths if present
            vocoder_checkpoint = None
            vocoder_config = None
            if self.config.get('vocoder_model_path'):
                vocoder_checkpoint = os.path.join(self.models_root, self.config['vocoder_model_path'])
                vocoder_config = os.path.join(self.models_root, self.config['vocoder_config_path'])
                
                if not os.path.exists(vocoder_checkpoint):
                    raise ModelLoadError(f"Vocoder model not found at {vocoder_checkpoint}")
                if not os.path.exists(vocoder_config):
                    raise ModelLoadError(f"Vocoder config not found at {vocoder_config}")
            
            logging.info(f"Loading Coqui model {self.config.get('voice')} - TTS: {tts_checkpoint}")
            if vocoder_checkpoint:
                logging.info(f"With vocoder: {vocoder_checkpoint}")
            
            # Initialize synthesizer
            self.synthesizer = Synthesizer(
                tts_checkpoint=tts_checkpoint,
                tts_config_path=tts_config,
                vocoder_checkpoint=vocoder_checkpoint,
                vocoder_config=vocoder_config,
                use_cuda=self.config.get('use_cuda', False)
            )
            
            # Store sample rate
            self.sample_rate_val = self.synthesizer.output_sample_rate
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load Coqui model: {str(e)}"
            logging.error(error_msg)
            raise ModelLoadError(error_msg)
    
    def synthesize(self, text: str) -> io.BytesIO:
        """Synthesize text to speech
        
        Args:
            text (str): Text to synthesize
            
        Returns:
            io.BytesIO: WAV audio buffer
            
        Raises:
            SynthesisError: If synthesis fails
        """
        try:
            if not self.synthesizer:
                raise SynthesisError("Synthesizer not initialized. Call load_model() first.")
            
            # Generate audio
            wavs = self.synthesizer.tts(text)
            
            # Convert to WAV buffer
            out = io.BytesIO()
            self.synthesizer.save_wav(wavs, out)
            out.seek(0)
            
            return out
            
        except Exception as e:
            error_msg = f"Failed to synthesize text with Coqui model: {str(e)}"
            logging.error(error_msg)
            raise SynthesisError(error_msg)
    
    @property
    def sample_rate(self) -> int:
        """Get the model's output sample rate
        
        Returns:
            int: Sample rate in Hz
            
        Raises:
            ModelLoadError: If model not loaded
        """
        if self.sample_rate_val is None:
            raise ModelLoadError("Model not loaded. Call load_model() first.")
        return self.sample_rate_val