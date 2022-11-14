import os
import json
from importlib import import_module

# from TTS.utils.manage import ModelManager ##TODO: This could be enabled to load coqui models without pointing to path
from TTS.utils.synthesizer import Synthesizer

DEFAULT_PREPROCESSOR_MODULE = 'preprocessor'

def read_config(config_file):
    """Read JSON format configuration file"""
    with open(config_file, "r") as jsonfile: 
        data = json.load(jsonfile) 
        print("Config Read successful") 
    return data

def load_lang_preprocessor(lang, preprocessor_module_name='preprocessor'):
    try:
        preprocessor_module = import_module('utils.preprocessors.' + lang + '.' + preprocessor_module_name)
        preprocessor = lambda x: preprocessor_module.text_preprocess(x)
        return preprocessor
    except ModuleNotFoundError:
        print("WARNING: Couldn't load preprocessor", preprocessor_module_name, 'for lang', lang)
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
        print("WARNING: No Vocoder model or config specified. Loading with default vocoder.")
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

    return True, "Success"

def load_models(config_data, models_root, use_cuda=False):
    """Load models into memory"""
    loaded_models = {}

    # global synthesizer
    for model_config in config_data['models']:
        model_id = model_config['voice']
        model_data = {}
        model_data['lang'] = model_config['lang']
        model_data['voice'] = model_id
        
        if model_config['load']:
            print('Loading', model_config['voice'])

            model_data['lang'] = model_config.get('lang')
            #TODO: Get proper language name
            if model_data['lang'] in config_data['languages']:
                model_data['language'] = config_data['languages'][model_data['lang']]
            else:
                print("WARNING: Full language name not specified in configuration file")
            
            #Load TTS model (Only Coqui TTS support for now)
            if model_config['model_type'] == 'coqui':
                success, message = load_coqui_model(model_data, model_config, models_root, use_cuda)
                if not success:
                    print("ERROR:", message)
                    continue
            else:
                print("ERROR: Model type %s is currently not supported. Skipping load."%(model_config['model_type']))
                continue
            
            #Load language specific preprocessor (if any)
            preprocessor_module_name = model_config['preprocessor'] if 'preprocessor' in model_config else DEFAULT_PREPROCESSOR_MODULE
            model_data['preprocessor'] = load_lang_preprocessor(model_data['lang'], preprocessor_module_name)

            #Save model to loaded_models
            loaded_models[model_id] = model_data

            #TODO: This part is probably needed for multispeaker models. Not implementing as it's not needed for now
            # loaded_models[model_id]['use_multi_speaker'] = hasattr(synthesizer.tts_model, "num_speakers") and synthesizer.tts_model.num_speakers > 1
            # loaded_models[model_id]['speaker_manager'] = getattr(synthesizer.tts_model, "speaker_manager", None)
            # # TODO: set this from SpeakerManager
            # loaded_models[model_id]['use_gst'] = synthesizer.tts_config.get("use_gst", False)

    return loaded_models