import os
import json
import logging
from importlib import import_module
from utils.exceptions import ModelLoadError, ConfigurationError
from .model_factory import TTSModelFactory

# from TTS.utils.manage import ModelManager ##TODO: This could be enabled to load coqui models without pointing to path
from TTS.utils.synthesizer import Synthesizer

DEFAULT_PREPROCESSOR_MODULE = 'preprocessor'
DEFAULT_FRAMERATE = 22050

logger = logging.getLogger(__name__)

def read_config(config_file):
    """Read JSON format configuration file"""
    with open(config_file, "r") as jsonfile: 
        data = json.load(jsonfile) 
        logger.info("Config Read successful") 
    return data

def load_lang_preprocessor(lang, preprocessor_module_name=DEFAULT_PREPROCESSOR_MODULE):
    try:
        preprocessor_module = import_module('utils.preprocessors.' + lang + '.' + preprocessor_module_name)
        preprocessor = lambda x: preprocessor_module.text_preprocess(x)
        return preprocessor
    except ModuleNotFoundError:
        logger.error(f"Couldn't load preprocessor {preprocessor_module_name} for lang {lang}")
        return None

def load_models(config_data: dict, models_root: str, use_cuda: bool = False):
    try:
        loaded_models = {}
        default_model_ids = {}
        
        for model_config in config_data['models']:
            model_id = model_config['voice']
            
            if not model_config.get('load', False):
                continue
                
            try:
                model_config['use_cuda'] = use_cuda
                model = TTSModelFactory.create_model(model_config)
                
                if not model.load_model():
                    raise ModelLoadError(f"Failed to load model {model_id}")
                    
                loaded_models[model_id] = {
                    'model': model,
                    'lang': model_config['lang'],
                    'voice': model_id,
                    'language': config_data['languages'].get(model_config['lang']),
                    'preprocessor': load_lang_preprocessor(
                        model_config['lang'],
                        model_config.get('preprocessor', 'preprocessor')
                    ),
                    'framerate': model.sample_rate
                }
                
                if (model_config.get('default_for_lang', False) or 
                    model_config['lang'] not in default_model_ids):
                    default_model_ids[model_config['lang']] = model_id
                    
                logging.info(f"Successfully loaded model {model_id}")
                
            except Exception as e:
                logging.error(f"Error loading model {model_id}: {e}")
                continue
        
        if not loaded_models:
            raise ModelLoadError("No models were successfully loaded")
            
        return loaded_models, default_model_ids
        
    except Exception as e:
        logging.error(f"Error in load_models: {e}")
        raise