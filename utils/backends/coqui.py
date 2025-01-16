# utils/backends/coqui.py
import io
import logging
from TTS.utils.synthesizer import Synthesizer
from .base import TTSModelWrapper
import os

class CoquiWrapper(TTSModelWrapper):
    def __init__(self, model_config: dict):
        self.config = model_config
        self.synthesizer = None
        self.sample_rate_val = None
        self.models_root = os.getenv('MODELS_ROOT', 'models')
    
    def load_model(self) -> bool:
        try:
            tts_checkpoint = os.path.join(self.models_root, self.config['tts_model_path'])
            tts_config = os.path.join(self.models_root, self.config['tts_config_path'])
            
            vocoder_checkpoint = None
            vocoder_config = None
            if self.config.get('vocoder_model_path'):
                vocoder_checkpoint = os.path.join(self.models_root, self.config['vocoder_model_path'])
                vocoder_config = os.path.join(self.models_root, self.config['vocoder_config_path'])
            
            self.synthesizer = Synthesizer(
                tts_checkpoint=tts_checkpoint,
                tts_config_path=tts_config,
                vocoder_checkpoint=vocoder_checkpoint,
                vocoder_config=vocoder_config,
                use_cuda=self.config.get('use_cuda', False)
            )
            self.sample_rate_val = self.synthesizer.output_sample_rate
            return True
        except Exception as e:
            logging.error(f"Failed to load Coqui model: {e}")
            return False
    
    def synthesize(self, text: str) -> io.BytesIO:
        wavs = self.synthesizer.tts(text)
        out = io.BytesIO()
        self.synthesizer.save_wav(wavs, out)
        out.seek(0)  # Important: Reset buffer position to start
        return out
    
    @property
    def sample_rate(self) -> int:
        return self.sample_rate_val