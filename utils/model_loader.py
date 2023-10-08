import os
import json
import logging
from importlib import import_module

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

def load_lang_preprocessor(lang, preprocessor_module_name='preprocessor'):
    try:
        preprocessor_module = import_module('utils.preprocessors.' + lang + '.' + preprocessor_module_name)
        preprocessor = lambda x: preprocessor_module.text_preprocess(x)
        return preprocessor
    except ModuleNotFoundError:
        logger.error(f"Couldn't load preprocessor {preprocessor_module_name} for lang {lang}")
        return None

def load_coqui_model(model_data, model_config, models_root="models", use_cuda=False):
    if model_config.get('tts_model_path'):
        tts_checkpoint_path = os.path.join(models_root, model_config['tts_model_path'])
        if model_config.get('tts_config_path'):
            tts_config_path = os.path.join(models_root, model_config['tts_config_path'])
        else:
            return False, "No TTS config path specified. Skipping model load"
    else:
        return False, "No TTS model path specified. Skipping model load"

    if model_config.get('vocoder_model_path') and model_config.get('vocoder_config_path'):
        vocoder_checkpoint_path = os.path.join(models_root, model_config['vocoder_model_path'])
        vocoder_config_path = os.path.join(models_root, model_config['vocoder_config_path'])
    else:
        logger.warning("No Vocoder model or config specified. Loading with default vocoder.")
        vocoder_checkpoint_path = None
        vocoder_config_path = None

    #initialize synthesizer
    try:
        synthesizer = Synthesizer(
            tts_checkpoint=tts_checkpoint_path,
            tts_config_path=tts_config_path,
            tts_speakers_file=None,
            tts_languages_file=None,
            vocoder_checkpoint=vocoder_checkpoint_path,
            vocoder_config=vocoder_config_path,
            encoder_checkpoint="",
            encoder_config="",
            use_cuda=use_cuda,
        )
    except Exception as e:
        return False, "Cannot initialize model (%s)"%(getattr(e, 'message', repr(e))
)

    model_data['synthesizer'] = synthesizer
    model_data['tts_checkpoint_path'] = tts_checkpoint_path
    model_data['tts_config_path'] = tts_config_path
    model_data['vocoder_checkpoint_path'] = vocoder_checkpoint_path
    model_data['vocoder_config_path'] = vocoder_config_path
    model_data['framerate'] = synthesizer.output_sample_rate

    return True, "Success"

def load_models(config_data, models_root, use_cuda=False):
    """Load models into memory"""
    loaded_models = {}
    default_model_ids = {}

    # global synthesizer
    for model_config in config_data['models']:
        model_id = model_config['voice']
        model_data = {}
        model_data['lang'] = model_config['lang']
        model_data['voice'] = model_id
        
        if model_config['load']:
            logger.info(f'Loading {model_id}')

            #Get language code
            model_data['lang'] = model_config.get('lang')

            #Get language name
            if model_data['lang'] in config_data['languages']:
                model_data['language'] = config_data['languages'][model_data['lang']]
            else:
                logger.warning(f"Full language name for '{model_data['lang']}' not specified in configuration file")
            
            #Load TTS model (Only Coqui TTS support for now)
            if model_config['model_type'] == 'coqui':
                success, message = load_coqui_model(model_data, model_config, models_root, use_cuda)
                if not success:
                    logger.error(message)
                    continue
            else:
                logger.error("Model type %s is currently not supported. Skipping load."%(model_config['model_type']))
                continue
            
            #Load language specific preprocessor (if any)
            preprocessor_module_name = model_config['preprocessor'] if 'preprocessor' in model_config else DEFAULT_PREPROCESSOR_MODULE
            model_data['preprocessor'] = load_lang_preprocessor(model_data['lang'], preprocessor_module_name)

            #Save model to loaded_models
            loaded_models[model_id] = model_data

            #Determine if model is default model for language
            if model_config.get('defualt_for_lang') or model_data['lang'] not in default_model_ids:
                default_model_ids[model_data['lang']] = model_data['voice']

            logger.info(f"Voice {model_id} for {model_data['language']} loaded successfully")

            #TODO: This part is probably needed for multispeaker models. Not implementing as it's not needed for now
            # loaded_models[model_id]['use_multi_speaker'] = hasattr(synthesizer.tts_model, "num_speakers") and synthesizer.tts_model.num_speakers > 1
            # loaded_models[model_id]['speaker_manager'] = getattr(synthesizer.tts_model, "speaker_manager", None)
            # # TODO: set this from SpeakerManager
            # loaded_models[model_id]['use_gst'] = synthesizer.tts_config.get("use_gst", False)

    return loaded_models, default_model_ids