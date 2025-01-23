# utils/backends/mms.py
import io
import logging
import os
from transformers import VitsModel, AutoTokenizer, pipeline
import torch
import numpy as np
import scipy.io.wavfile
from .base import TTSModelWrapper
from utils.exceptions import ModelLoadError, SynthesisError

class MMSWrapper(TTSModelWrapper):
    """Wrapper for Massively Multilingual Speech (MMS) models from HuggingFace
    
    This wrapper handles models that follow the HuggingFace transformers format,
    particularly VITS models fine-tuned using the MMS approach. It supports both
    base models and fine-tuned checkpoints.
    """
    
    def __init__(self, model_config: dict):
        """Initialize the MMS wrapper with config
        
        Args:
            model_config (dict): Configuration dictionary containing model paths and settings.
                               Must include 'base_model_path' and optionally 'checkpoint_name'
        """
        self.config = model_config
        self.model = None
        self.tokenizer = None
        self.synthesizer = None
        self.sample_rate_val = 16000  # MMS models typically use 16kHz
        self.models_root = os.getenv('MODELS_ROOT', 'models')
        
    def load_model(self) -> bool:
        """Load the MMS model and tokenizer into memory
        
        This method handles both the base model loading and optional checkpoint loading.
        It sets up the model pipeline for inference on the appropriate device (CPU/CUDA).
        
        Returns:
            bool: True if model loaded successfully
            
        Raises:
            ModelLoadError: If model loading fails for any reason
        """
        try:
            # Construct model path
            model_path = os.path.join(self.models_root, self.config['base_model_path'])
            if not os.path.exists(model_path):
                raise ModelLoadError(f"Model directory not found at {model_path}")
                
            logging.info(f"Loading MMS model from {model_path}")
            
            # Load model and tokenizer from HuggingFace format
            try:
                self.model = VitsModel.from_pretrained(model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            except Exception as e:
                raise ModelLoadError(f"Failed to load base model and tokenizer: {str(e)}")
            
            # Handle optional checkpoint loading
            if 'checkpoint_name' in self.config:
                checkpoint_path = os.path.join(model_path, self.config['checkpoint_name'])
                if os.path.exists(checkpoint_path):
                    try:
                        from safetensors.torch import load_file
                        checkpoint = load_file(checkpoint_path)
                        self.model.load_state_dict(checkpoint, strict=False)
                        logging.info(f"Loaded checkpoint from {checkpoint_path}")
                    except Exception as e:
                        raise ModelLoadError(f"Failed to load checkpoint: {str(e)}")
                else:
                    logging.warning(f"Checkpoint not found at {checkpoint_path}")
            
            # Set up inference device
            device = "cuda" if self.config.get('use_cuda', False) and torch.cuda.is_available() else "cpu"
            logging.info(f"Setting up MMS pipeline on device: {device}")
            
            # Create inference pipeline
            try:
                self.synthesizer = pipeline(
                    "text-to-speech",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=device
                )
            except Exception as e:
                raise ModelLoadError(f"Failed to create inference pipeline: {str(e)}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load MMS model: {str(e)}"
            logging.error(error_msg)
            raise ModelLoadError(error_msg)
    
    def synthesize(self, text: str) -> io.BytesIO:
        """Synthesize text to speech using the MMS model
        
        Args:
            text (str): Text to synthesize
            
        Returns:
            io.BytesIO: WAV audio buffer
            
        Raises:
            SynthesisError: If synthesis fails for any reason
        """
        try:
            if not self.synthesizer:
                raise SynthesisError("Synthesizer not initialized. Call load_model() first.")
            
            # Generate speech using the pipeline
            try:
                output = self.synthesizer(text.strip())
            except Exception as e:
                raise SynthesisError(f"Pipeline inference failed: {str(e)}")
            
            # Convert to WAV format in memory
            wav_buffer = io.BytesIO()
            try:
                scipy.io.wavfile.write(
                    wav_buffer,
                    rate=self.sample_rate_val,
                    data=output["audio"][0]
                )
                wav_buffer.seek(0)
            except Exception as e:
                raise SynthesisError(f"Failed to convert audio to WAV format: {str(e)}")
            
            return wav_buffer
            
        except Exception as e:
            error_msg = f"Failed to synthesize text with MMS model: {str(e)}"
            logging.error(error_msg)
            raise SynthesisError(error_msg)
    
    @property
    def sample_rate(self) -> int:
        """Get the model's output sample rate
        
        Returns:
            int: Sample rate in Hz (typically 16000 for MMS models)
            
        Raises:
            ModelLoadError: If model not loaded
        """
        if not self.synthesizer:
            raise ModelLoadError("Model not loaded. Call load_model() first.")
        return self.sample_rate_val