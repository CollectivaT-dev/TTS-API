#!flask/bin/python
import io
import os
import logging
from flask import Flask, render_template, request, send_file, jsonify
from typing import List
from TTS.config import load_config
from utils.utils import style_wav_uri_to_dict, universal_text_normalize
from utils.model_loader import read_config, load_models
from pydub import AudioSegment
from nltk.tokenize import sent_tokenize
import tempfile

app = Flask(__name__)

#Read environment variables
MODELS_ROOT = 'models'
CONFIG_JSON_PATH = os.getenv('TTS_API_CONFIG', 'config.json')
LOG_PATH = os.getenv('TTS_LOG_PATH', 'app.log') 
USE_CUDA = True if os.getenv('USE_CUDA')=="1" else False
COQUI_CONFIG_JSON_PATH = "coqui-models.json"

#Constants
LONG_SILENCE_SEGMENT = AudioSegment.silent(duration=500)
SHORT_SILENCE_SEGMENT = AudioSegment.silent(duration=200)
TMP_AUDIO_PATH = '../audio-cache'
CLOUD_AUDIO_FORMAT = 'mp3'

# Configure logging
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s')

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


logging.info(f"USE_CUDA: {USE_CUDA}")
logging.info("MODELS: " + ', '.join([f'{m} ({loaded_models[m]["lang"]})' if default_model_ids[loaded_models[m]["lang"]] == m else f'{m}' for m in loaded_models]))

def synthesize(text:str, voice:str):
    out = 0
    success = 0
    detail = "success"

    #Preprocess text with language specific preprocessor
    if loaded_models[voice]['preprocessor']:
        text = loaded_models[voice]['preprocessor'](text)
        
    #Normalize text with universal normalizer
    text = universal_text_normalize(text)

    logging.info(f"Preprocessed text: {text}")

    if not text:
        logging.warning(f"Invalid text for synthesis")
        detail = "Invalid text for synthesis"
        return out, success, detail

    try:
        #wavs = loaded_models[voice]['synthesizer'].tts(preprocessed_text, speaker_name=speaker_idx, style_wav=style_wav)
        wavs = loaded_models[voice]['synthesizer'].tts(text)
        out = io.BytesIO()
        loaded_models[voice]['synthesizer'].save_wav(wavs, out)
        logging.info("Success")
        success = 1
    except Exception as e:
        detail = str(e)

    return out, success, detail

#Text normalization functions

#TODO: Clean text (stub)
def clean_sent(text:str):
    #TODO
    return text

#Parse sentences from text (uses NLTK sent_tokenize)
def parse_sents(text:str):
    sents = []
    sent_candidates = sent_tokenize(text.strip())
    clean_sents = [clean_sent(s) for s in sent_candidates]
    return clean_sents 

#Synthesizes and merges a list of strings using method synthesize
def long_synthesize(text_paragraphs:List[str], voice:str):
    framerate = loaded_models[voice]['framerate']
    allsound = AudioSegment.empty()

    for paragraph in text_paragraphs:
        segments = parse_sents(paragraph)
        for s in segments:
            audiobytes, success, detail = synthesize(text=s, voice=voice)
        
            if success:
                sound = AudioSegment(
                    # raw audio data (bytes)
                    data=audiobytes.getvalue()[1024:],
                    # 2 byte (16 bit) samples
                    sample_width=2,
                    # 16 kHz frame rate
                    frame_rate=framerate, 
                    # mono
                    channels=1
                )

                allsound += sound + SHORT_SILENCE_SEGMENT
            else:
                logging.warning(f"Couldn't synthesize segment |{s}|. Reason: {detail}")

        allsound += LONG_SILENCE_SEGMENT

    return allsound

# APP ENDPOINTS

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
def check(voice:str=None, lang:str=None):    
    if not voice and not lang:
        voice = request.args.get("voice")
        lang = request.args.get("lang")

    # logging.info(f"Check request voice: {voice}, lang: {lang}")

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


@app.route("/api/short", methods=["GET"])
def tts():
    text = request.args.get("text")
    voice = request.args.get("voice")
    lang = request.args.get("lang")
    # speaker_idx = request.args.get("speaker_id", "")
    logging.info(f"Short TTS request in voice: {voice} lang: {lang}")
    logging.info(f"Requested text: {text}")
    # print(" > Speaker Idx: {}".format(speaker_idx))

    if not text:
        logging.warning("Text empty")
        return jsonify({'message':f"Text must not be empty"}), 400

    r, status = check(voice, lang)

    if not status == 200:
        return r, status

    voice = r['voice']

    out, success, detail = synthesize(text, voice)
    if success:
        return send_file(out, mimetype="audio/wav")
    else: 
        return jsonify({'message':detail}), 400


@app.route("/api/long", methods=["GET"])
def longtts():
    text = request.args.get("text")
    voice = request.args.get("voice")
    lang = request.args.get("lang")
    # speaker_idx = request.args.get("speaker_id", "")
    logging.info(f"Long TTS request in voice: {voice} lang: {lang}")
    logging.info(f"Requested text: {text}")
    # print(" > Speaker Idx: {}".format(speaker_idx))

    if not text:
        logging.warning("Text empty")
        return jsonify({'message':f"Text must not be empty"}), 400

    r, status = check(voice, lang)

    if not status == 200:
        return r, status

    voice = r['voice']

    audioseg = long_synthesize([text], voice)
    
    # Use a temporary file to hold the audio data
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
        audioseg.export(tmpfile.name, format="mp3")
        tmpfile_path = tmpfile.name
    
    # Serve the temporary file with send_file, setting as_attachment to True to prompt download
    response = send_file(tmpfile_path, mimetype="audio/mp3")
    
    # Optionally, remove the temporary file if you don't need it after sending
    os.unlink(tmpfile_path)

    return response



def main():
    app.run(debug=True, host="::", port=5002)


if __name__ == "__main__":
    main()
