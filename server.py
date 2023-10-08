#!flask/bin/python
import io
import os
import logging
from flask import Flask, render_template, request, send_file, jsonify

from TTS.config import load_config
from utils.utils import style_wav_uri_to_dict, universal_text_normalize
from utils.model_loader import read_config, load_models

#Read environment variables
MODELS_ROOT = 'models'
CONFIG_JSON_PATH = os.getenv('TTS_API_CONFIG') if os.getenv('TTS_API_CONFIG') else 'config.json'
USE_CUDA = True if os.getenv('USE_CUDA')=="1" else False
COQUI_CONFIG_JSON_PATH = "coqui-models.json"

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s')

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the desired log level for console output

# Create a formatter for console output
console_formatter = logging.Formatter('%(levelname)s | %(message)s')

# Set the formatter for the console handler
console_handler.setFormatter(console_formatter)

# Add the console handler to the root logger
root_logger = logging.getLogger()
root_logger.addHandler(console_handler)

#Load config and models
config_data = read_config(CONFIG_JSON_PATH)
loaded_models, default_model_ids = load_models(config_data, MODELS_ROOT, USE_CUDA)

# Configure the root logger
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s')

logging.info(f"USE_CUDA: {USE_CUDA}")
logging.info("MODELS: " + ', '.join([f'{m} ({loaded_models[m]["lang"]})' if default_model_ids[loaded_models[m]["lang"]] == m else f'{m}' for m in loaded_models]))

@app.route("/")
def index():
    logging.info('Index page view')

    return render_template(
        "index.html",
        show_details=True,
        use_multi_speaker=True,
        voices={k:loaded_models[k]['language'] for k in loaded_models.keys()},
        use_gst=False,
    )

@app.route("/details")
def details():
    voice = request.args.get("voice")

    if voice not in loaded_models:
        model = {}
        model_config={}
        vocoder_config={}
    else:
        model = loaded_models[voice]
        model_config = load_config(model['tts_config_path'])
        if model['vocoder_config_path'] is not None and os.path.isfile(model['vocoder_config_path']):
            vocoder_config = load_config(model['vocoder_config_path'])
        else:
            vocoder_config = None

    return render_template(
        "details.html",
        show_details=True,
        model_config=model_config,
        vocoder_config=vocoder_config,
        args=model,
    )

@app.route("/api/tts/voices", methods=["GET"])
def list_voices():
    logging.info("List voices request")

    voices_by_lang = {}
    for model_id in loaded_models:
        lang = loaded_models[model_id]['lang']
        if lang not in voices_by_lang:
            voices_by_lang[lang] = {'name':loaded_models[model_id]['language'], 'voices':{}}
        voices_by_lang[lang]['voices'][model_id] = {'default': True if default_model_ids[lang] == model_id else False,
                                                    'framerate': loaded_models[model_id]['framerate']}

    return voices_by_lang, 200

@app.route("/api/tts/check", methods=["GET"])
def check(voice=None, lang=None):    
    if not voice and not lang:
        voice = request.args.get("voice")
        lang = request.args.get("lang")

    logging.info(f"Check request voice: {voice}, lang: {lang}")

    if voice:
        #Check if voice is loaded
        if not voice in loaded_models:
            logging.warning(f"Voice {voice} not found")
            return jsonify({'message':f"Voice {voice} not found"}), 400

        if lang:
            #Check if voice is in lang if both are specified
            if not loaded_models[voice]['lang'] == lang:
                logging.warning(f"Bad request - Voice {voice} is not in specified lang {lang}")
                return jsonify({'message':f"Voice {voice} is not in speficied lang {lang}"}), 400
    elif lang:
        #Get default voice for language
        if lang in default_model_ids:
            voice = default_model_ids[lang]
            logging.info(f"Voice found: {voice}")
        else:
            logging.warning(f"No model for language {lang}")
            return jsonify({'message':f"No model for language {lang}"}), 400
    else:
        logging.warning("Request must specify voice or language")
        return jsonify({'message':f"Request must specify voice or language"}), 400

    return {"voice": voice, "framerate": loaded_models[voice]['framerate']}, 200

@app.route("/api/tts", methods=["GET"])
def tts():
    text = request.args.get("text")
    voice = request.args.get("voice")
    lang = request.args.get("lang")
    # speaker_idx = request.args.get("speaker_id", "")
    logging.info(f"TTS REQUEST in voice: {voice} lang {lang}")
    logging.info(f"Text: {text}")
    # print(" > Speaker Idx: {}".format(speaker_idx))

    if not text:
        logging.warning("Text empty")
        return jsonify({'message':f"Text must not be empty"}), 400

    r, status = check(voice, lang)

    if not status == 200:
        return r, status

    voice = r['voice']

    #Preprocess text with language specific preprocessor
    if loaded_models[voice]['preprocessor']:
        text = loaded_models[voice]['preprocessor'](text)
        
    #Normalize text with universal normalizer
    text = universal_text_normalize(text)

    logging.info(f"Preprocessed text: {text}")

    if not text:
        logging.warning(f"Invalid text for synthesis")
        return jsonify({'message':f"Invalid text"}), 400

    #wavs = loaded_models[voice]['synthesizer'].tts(preprocessed_text, speaker_name=speaker_idx, style_wav=style_wav)
    wavs = loaded_models[voice]['synthesizer'].tts(text)
    out = io.BytesIO()
    loaded_models[voice]['synthesizer'].save_wav(wavs, out)
    logging.info("Sending out wav")
    return send_file(out, mimetype="audio/wav")


def main():
    app.run(debug=True, host="::", port=5002)


if __name__ == "__main__":
    main()
