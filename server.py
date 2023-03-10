#!flask/bin/python
import io
import os

from flask import Flask, render_template, request, send_file, jsonify

from TTS.config import load_config

from utils.utils import style_wav_uri_to_dict, universal_text_normalize
from utils.model_loader import read_config, load_models

MODELS_ROOT = 'models'
CONFIG_JSON_PATH = os.getenv('TTS_API_CONFIG') if os.getenv('TTS_API_CONFIG') else 'config.json'
USE_CUDA = True if os.getenv('USE_CUDA')=="1" else False
COQUI_CONFIG_JSON_PATH = "coqui-models.json"

#load config and models
config_data = read_config(CONFIG_JSON_PATH)
print("USE_CUDA", USE_CUDA)
loaded_models, default_model_ids = load_models(config_data, MODELS_ROOT, USE_CUDA)
print("MODELS DICT\n", loaded_models)
print("DEFAULT MODELS\n", default_model_ids)

app = Flask(__name__)

@app.route("/")
def index():
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

@app.route("/api/tts", methods=["GET"])
def tts():
    text = request.args.get("text")
    voice = request.args.get("voice")
    lang = request.args.get("lang")
    # speaker_idx = request.args.get("speaker_id", "")
    print(f"TTS API REQUEST")
    print(f" > Input text: {text}")
    print(f" > Voice: {voice}")
    print(f" > Lang: {lang}")
    # print(" > Speaker Idx: {}".format(speaker_idx))

    if not text:
        print(f"REQUEST ERROR: Text must not be empty")
        return jsonify({'message':f"Text must not be empty"}), 400

    if voice:
        #Check if voice is loaded
        if not voice in loaded_models:
            print(f"REQUEST ERROR: Voice {voice} not found")
            return jsonify({'message':f"Voice {voice} not found"}), 400

        if lang:
            #Check if voice is in lang
            if not loaded_models[voice]['lang'] == lang:
                print(f"REQUEST ERROR: Voice {voice} is not in specified lang {lang}")
                return jsonify({'message':f"Voice {voice} is not in speficied lang {lang}"}), 400
    elif lang:
        #Get default voice for language
        if lang in default_model_ids:
            voice = default_model_ids[lang]
            print(f" > Default voice: {voice}")
        else:
            print(f"REQUEST ERROR: No model for language {lang}")
            return jsonify({'message':f"No model for language {lang}"}), 400
    else:
        print(f"REQUEST ERROR: Request must specify voice or language")
        return jsonify({'message':f"Request must specify voice or language"}), 400

    #Preprocess text with language specific preprocessor
    if loaded_models[voice]['preprocessor']:
        text = loaded_models[voice]['preprocessor'](text)
        
    #Normalize text with universal normalizer
    text = universal_text_normalize(text)

    print(" > Preprocessed text:", text)

    if not text:
        print(f"REQUEST ERROR: Invalid text")
        return jsonify({'message':f"Invalid text"}), 400

    #wavs = loaded_models[voice]['synthesizer'].tts(preprocessed_text, speaker_name=speaker_idx, style_wav=style_wav)
    wavs = loaded_models[voice]['synthesizer'].tts(text)
    out = io.BytesIO()
    loaded_models[voice]['synthesizer'].save_wav(wavs, out)
    return send_file(out, mimetype="audio/wav")


def main():
    app.run(debug=True, host="::", port=5002)


if __name__ == "__main__":
    main()
