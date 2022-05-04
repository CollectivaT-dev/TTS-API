#!flask/bin/python
import argparse
import io
import json
import os
import sys
from pathlib import Path
from typing import Union

from flask import Flask, render_template, request, send_file, Response, jsonify

from TTS.config import load_config
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer

from preprocessors.ladino_number_letter import num_let

MODELS_ROOT = 'models'
CONFIG_JSON_PATH = os.getenv('TTS_API_CONFIG') if os.getenv('TTS_API_CONFIG') else 'config.json'
COQUI_CONFIG_JSON_PATH = "coqui-models.json"

def read_config(config_file):
    """Read JSON format configuration file"""
    with open(config_file, "r") as jsonfile: 
        data = json.load(jsonfile) 
        print("Config Read successful") 
    return data

def load_models(config_data):
    """Load models into memory"""
    loaded_models = {}

    # global synthesizer
    for model_config in config_data['models']:
        model_id = model_config['voice']
        loaded_models[model_id] = {}
        loaded_models[model_id]['lang'] = model_config['lang']
        loaded_models[model_id]['voice'] = model_id
        
        if model_config['load']:
            print('Load', model_config['voice'])
            synthesizer = Synthesizer(
                tts_checkpoint=os.path.join(MODELS_ROOT, model_config['model_path']),
                tts_config_path=os.path.join(MODELS_ROOT, model_config['config_path']),
                tts_speakers_file=None,
                tts_languages_file=None,
                vocoder_checkpoint=None,
                vocoder_config=None,
                encoder_checkpoint="",
                encoder_config="",
                use_cuda=False,
            )
            loaded_models[model_id]['synthesizer'] = synthesizer

            # loaded_models[model_id]['use_multi_speaker'] = hasattr(synthesizer.tts_model, "num_speakers") and synthesizer.tts_model.num_speakers > 1
            # loaded_models[model_id]['speaker_manager'] = getattr(synthesizer.tts_model, "speaker_manager", None)
            # # TODO: set this from SpeakerManager
            # loaded_models[model_id]['use_gst'] = synthesizer.tts_config.get("use_gst", False)

    return loaded_models

#models and data
config_data = read_config(CONFIG_JSON_PATH)
loaded_models = load_models(config_data)

# load models #TODO: Make this multilingual, read configuration from config.json

app = Flask(__name__)


def style_wav_uri_to_dict(style_wav: str) -> Union[str, dict]:
    """Transform an uri style_wav, in either a string (path to wav file to be use for style transfer)
    or a dict (gst tokens/values to be use for styling)

    Args:
        style_wav (str): uri

    Returns:
        Union[str, dict]: path to file (str) or gst style (dict)
    """
    if style_wav:
        if os.path.isfile(style_wav) and style_wav.endswith(".wav"):
            return style_wav  # style_wav is a .wav file located on the server

        style_wav = json.loads(style_wav)
        return style_wav  # style_wav is a gst dictionary with {token1_id : token1_weigth, ...}
    return None


@app.route("/")
def index():
    return render_template(
        "index.html",
        show_details=True,
        use_multi_speaker=False,
        speaker_ids=None,
        use_gst=False,
    )


@app.route("/details")
def details():
    model_config = load_config(args.tts_config)
    if args.vocoder_config is not None and os.path.isfile(args.vocoder_config):
        vocoder_config = load_config(args.vocoder_config)
    else:
        vocoder_config = None

    return render_template(
        "details.html",
        show_details=args.show_details,
        model_config=model_config,
        vocoder_config=vocoder_config,
        args=args.__dict__,
    )

#Preprocessors #TODO: Put this to separate utils
def canBeNumber(n):
    try:
        int(n)
        return True
    except ValueError:
        # Not a number
        return False

def text_preprocess(text):
    text = text.strip()
    return ' '.join([num_let(int(t)) if canBeNumber(t) else t for t in text.split()])

@app.route("/api/tts", methods=["GET"])
def tts():
    text = request.args.get("text")
    voice = request.args.get("voice") #TODO
    speaker_idx = request.args.get("speaker_id", "")
    style_wav = request.args.get("style_wav", "")
    style_wav = style_wav_uri_to_dict(style_wav)
    print(" > Model input: {}".format(text))
    print(" > Voice: {}".format(voice))
    print(" > Speaker Idx: {}".format(speaker_idx))

    #TODO: Get language id from voice
    lang = 'lad'
    if not voice:
        voice='karen'

    #Preprocessing
    if lang == 'lad':
        text = text_preprocess(text)

    #TODO: get from models list
    if not voice in loaded_models:
        print("Voice not found", voice)
        return jsonify({'message':"Voice not found: %s"%voice}), 400
        #TODO: Return error

    wavs = loaded_models[voice]['synthesizer'].tts(text, speaker_name=speaker_idx, style_wav=style_wav)
    out = io.BytesIO()
    loaded_models[voice]['synthesizer'].save_wav(wavs, out)
    return send_file(out, mimetype="audio/wav")


def main():
    app.run(debug=True, host="::", port=5002)


if __name__ == "__main__":
    main()
