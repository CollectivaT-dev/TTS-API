#!flask/bin/python
import io
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, send_file, jsonify, make_response
from typing import List
from TTS.config import load_config
from utils.utils import style_wav_uri_to_dict, universal_text_normalize, parse_sents
from utils.model_loader import read_config, load_models
from utils.exceptions import ConfigurationError
from utils.config_validator import validate_config
from pydub import AudioSegment
import tempfile
import json

app = Flask(__name__)

#Read environment variables
MODELS_ROOT = 'models'
CONFIG_JSON_PATH = os.getenv('TTS_API_CONFIG', 'config.json')
LOG_DIR = os.getenv('TTS_LOG_DIR', 'logs') 
LOG_PATH = os.getenv('TTS_LOG_PATH', 'app.log') 
USE_CUDA = True if os.getenv('USE_CUDA')=="1" else False
COQUI_CONFIG_JSON_PATH = "coqui-models.json"

#Constants
LONG_SILENCE_SEGMENT = AudioSegment.silent(duration=500)
SHORT_SILENCE_SEGMENT = AudioSegment.silent(duration=200)

# Configure logging
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the logging level
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
file_handler = RotatingFileHandler(os.path.join(LOG_DIR, LOG_PATH), maxBytes=1024*1024*5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

#Load config and models
try:
    config_data = read_config(CONFIG_JSON_PATH)
    validate_config(config_data)
except ConfigurationError as e:
    logging.error(f"Configuration error: {e}")
    raise
except Exception as e:
    logging.error(f"Error reading config: {e}")
    raise
loaded_models, default_model_ids = load_models(config_data, MODELS_ROOT, USE_CUDA)

logging.info(f"USE_CUDA: {USE_CUDA}")
logging.info("MODELS: " + ', '.join([f'{m} ({loaded_models[m]["lang"]})' if default_model_ids[loaded_models[m]["lang"]] == m else f'{m}' for m in loaded_models]))

#Standard responses
def error_response(message, status_code):
    """Return a JSON error message and HTTP status code."""
    return make_response(jsonify({'message': message}), status_code)

def success_response(data, status_code=200):
    """Return a JSON data and HTTP status code."""
    return make_response(jsonify(data), status_code)

# long_synthesize
# Synthesizes each paragraph with a pause in between. 
# Each sentence in paragraph is synthesized with method synthesize and merged with a short pause in between
def long_synthesize(text_paragraphs: List[str], voice: str):
    framerate = loaded_models[voice]['framerate']
    model = loaded_models[voice]['model']
    preprocessor = loaded_models[voice]['preprocessor']
    
    allsound = AudioSegment.empty()
    allsound += LONG_SILENCE_SEGMENT  # initial silence

    for paragraph in text_paragraphs:
        segments = parse_sents(paragraph)
        for s in segments:
            try:
                if preprocessor:
                    s = preprocessor(s)
                else:
                    #Normalize text with universal normalizer
                    s = universal_text_normalize(s)
                
                audiobytes = model.synthesize(s)
                
                # Skip WAV header (first 1024 bytes) to avoid clicking
                sound = AudioSegment(
                    data=audiobytes.getvalue()[1024:],  # Skip WAV header
                    sample_width=2,
                    frame_rate=framerate,
                    channels=1
                )

                allsound += sound + SHORT_SILENCE_SEGMENT
            except Exception as e:
                logging.warning(f"Couldn't synthesize segment |{s}|. Reason: {str(e)}")

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

@app.route("/api/voices", methods=["GET"])
def list_voices():
    logging.info("List voices request")

    try:
        voices_by_lang = {}
        for model_id in loaded_models:
            lang = loaded_models[model_id]['lang']
            if lang not in voices_by_lang:
                voices_by_lang[lang] = {'name':loaded_models[model_id]['language'], 'voices':{}}
            voices_by_lang[lang]['voices'][model_id] = {'default': True if default_model_ids[lang] == model_id else False,
                                                        'framerate': loaded_models[model_id]['framerate']}

        return success_response(voices_by_lang)
    except Exception as e:
        return error_response(str(e), 500)

# Endpoint to check if given voice and/or language is available within loaded models
@app.route("/api/check", methods=["GET"])
def check(voice=None, lang=None):
    if not voice and not lang:
        voice = request.args.get("voice")
        lang = request.args.get("lang")

    if not voice and not lang:
        # return {"error": "Request must specify voice or language"}, 400
        return error_response("Request must specify voice or language", 400)

    if voice and voice not in loaded_models:
        # return {"error": f"Voice {voice} not found"}, 404
        return error_response(f"Voice {voice} not found", 404)

    if lang:
        if voice and loaded_models[voice]['lang'] != lang:
            # return {"error": f"Voice {voice} is not in specified lang {lang}"}, 400
            return error_response(f"Voice {voice} is not in specified lang {lang}", 400)
        if lang not in default_model_ids:
            # return {"error": f"No model for language {lang}"}, 404
            return error_response(f"No model for language {lang}", 404)
        
        voice = default_model_ids[lang]  # Set default voice for the language
    else:
        lang = loaded_models[voice]['lang']

    # return {"voice": voice, "framerate": loaded_models[voice]['framerate']}, 200
    return success_response({"voice":voice, "lang": lang})


# Simple TTS endpoint. Gets plain text as input and returns WAV. (Not used by Gateway)
@app.route("/api/short", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        text = data.get('text')
        voice = data.get('voice')
        lang = data.get('lang')

        if not text:
            return error_response("Text must not be empty", 400)

        result = check(voice, lang)
        result_info = json.loads(result.data.decode('utf-8'))
        if result.status_code != 200:
            return error_response(result_info['message'], result.status_code)
        
        voice = result_info['voice']
        
        try:
            model = loaded_models[voice]['model']
            
            if loaded_models[voice]['preprocessor']:
                text = loaded_models[voice]['preprocessor'](text)
            else:
                text = universal_text_normalize(text)
            
            audio_buffer = model.synthesize(text)
            
            response = make_response(send_file(
                audio_buffer,
                mimetype="audio/wav",
                as_attachment=True,
                download_name="synthesized.wav"
            ))
            return response
            
        except SynthesisError as e:
            logging.error(f"Synthesis error: {str(e)}")
            return error_response("Failed to synthesize audio", 500)
            
    except Exception as e:
        logging.error(f"Unexpected error in tts endpoint: {str(e)}")
        return error_response("Internal server error", 500)

# # Endpoint that uses long_synthesize. Returns mp3 or uploads to given cloud URL
@app.route("/api/long", methods=["POST"])
def longtts():
    data = request.get_json()  # Get the JSON data
    if not data:
        return error_response('No data provided', 400)
    
    text_paragraphs = data.get('text_paragraphs')
    voice = data.get('voice')
    lang = data.get('lang')

    if not text_paragraphs or not "".join(text_paragraphs).strip():
        logging.warning("Text empty")
        return error_response("Text must not be empty", 400)

    result = check(voice, lang)
    result_info = json.loads(result.data.decode('utf-8'))
    
    if result.status_code != 200:
        return error_response(result_info['message'], result.status_code)

    voice = result_info['voice']

    logging.info(f"Long TTS request in voice: {voice} lang: {lang}")
    logging.info(f"#Segments: {len(text_paragraphs)} #characters: {len(''.join(text_paragraphs))}")

    try:
        audioseg = long_synthesize(text_paragraphs, voice)
        
        # Use a temporary file to hold the audio data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
            audioseg.export(tmpfile.name, format="mp3")
            tmpfile_path = tmpfile.name
        
        response = send_file(tmpfile_path, mimetype="audio/mp3", as_attachment=True)
        os.unlink(tmpfile_path)  # Clean up the temporary file after sending
        return response
    except Exception as e:
        logging.error(f"Error during synthesis: {str(e)}")
        return error_response("Failed to synthesize audio", 500)


def main():
    app.run(debug=True, host="::", port=5050)

if __name__ == "__main__":
    main()
