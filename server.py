#!flask/bin/python
import io
import os

from flask import Flask, render_template, request, send_file, jsonify

from TTS.config import load_config

from utils.utils import style_wav_uri_to_dict
from utils.model_loader import read_config, load_models

MODELS_ROOT = 'models'
CONFIG_JSON_PATH = os.getenv('TTS_API_CONFIG') if os.getenv('TTS_API_CONFIG') else 'config.json'
COQUI_CONFIG_JSON_PATH = "coqui-models.json"

#load config and models
config_data = read_config(CONFIG_JSON_PATH)
loaded_models = load_models(config_data, MODELS_ROOT)
print("MODELS DICT\n", loaded_models)

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
    # speaker_idx = request.args.get("speaker_id", "")
    print(" > Input text: {}".format(text))
    print(" > Voice: {}".format(voice))
    # print(" > Speaker Idx: {}".format(speaker_idx))

    #Check if voice is loaded
    if not voice in loaded_models:
        print("Voice not found", voice)
        return jsonify({'message':"Voice not found: %s"%voice}), 400

    #Preprocess text
    preprocessed_text = loaded_models[voice]['preprocessor'](text)
    print("Preprocessed text:", preprocessed_text)

    #wavs = loaded_models[voice]['synthesizer'].tts(preprocessed_text, speaker_name=speaker_idx, style_wav=style_wav)
    wavs = loaded_models[voice]['synthesizer'].tts(preprocessed_text)
    out = io.BytesIO()
    loaded_models[voice]['synthesizer'].save_wav(wavs, out)
    return send_file(out, mimetype="audio/wav")


def main():
    app.run(debug=True, host="::", port=5002)


if __name__ == "__main__":
    main()
