# Text-to-speech API

This is a simple Text-to-speech (TTS) REST API based on the 🐸 [Coqui TTS demo server](https://github.com/coqui-ai/TTS/tree/dev/TTS/server). Additional features are:

- Loading multiple models at startup
- Model configuration specification with JSON format file (`config.json`)
- Easy docker installation
- CPU and GPU compatibility
- Modular and language specific text normalization 
- Multi-system support	
	- Coqui TTS
 	- Meta MMS (Huggingface)
	
## Demo

A demo app with Catalan, Galician and Ladino models is available at http://catotron.collectivat.cat. 

## Setup and installation

Start by cloning this repository and create your models directory:
```
git clone https://github.com/CollectivaT-dev/TTS-API.git
cd TTS-API
mkdir models
```

To run the API you need to first fetch your models and put them under the directory `models` (or know their exact path in your system). e.g.

```
TTS-API
    ↳ ...
    ↳ models
    	↳ my-tts-model.pth
        ↳ my-tts-model.config
        ↳ my-vocoder-model.pth
        ↳ my-vocoder-model.config
    ↳ ...
```

Official Coqui TTS models can be found in their [releases page](https://github.com/coqui-ai/TTS/releases).

Then, you need to setup the `config.json` file which contains information about your models. An example is provided below with explanations:

```
{
    "languages":{"en":"English", "es":"Spanish", "tr":"Turkish", "lad":"Ladino", "ca":"Catalan"}, <--- This is a dictionary mapping language codes to human-readable language name
    "models": [
        {
            "voice": "karen",			<--- Name of your voice
            "lang": "lad", 			<--- Language code
            "model_type": "coqui",  		<--- TTS system id
            "tts_config_path": "config.json",	<--- Path to TTS model configuration file 
            "tts_model_path": "checkpoint.pth",	<--- Path to TTS model checkpoint 
            "load": true 			<--- Flag to load at startup
        },
        {
            "voice": "pau",
            "lang": "ca",
            "model_type": "coqui",
            "tts_config_path": "pau-config.json",
            "tts_model_path": "pau-tts.pth.tar",
            "vocoder_config_path": "vocoder-config.json",	<--- Path to Vocoder model configuration file (if you have)
            "vocoder_model_path": "vocoder-model.pth.tar",	<--- Path to Vocoder checkpoint (if you have)
            "load": false
        }
    ]
}
```

As for paths, you can place full path or just its filename if it's placed under `models`.

### Run with docker compose (recommended)

This will take care of all installations for you.

```
docker compose build
docker compose up
```

To run on background 

```
docker compose up -d 
```

### Run with local installation

You might want to create a virtual environment before doing this option.

```
pip install -r requirements.txt
gunicorn server:app -b :5050 #or whatever port you like
```

or if you have everything already setup
```
./run_local.sh
```

### GPU inference

You can enable GPU for inference both running locally or with docker. 

#### Enabling GPU on docker

Make the following changes in `docker-compose.yml`

- Set `USE_CUDA` flag to 1
- Remove comments on nvidia driver setup ([consult here for more information](https://docs.docker.com/compose/gpu-support/))
```
...
      - USE_CUDA=1  #1 to enable GPU inference
    #Remove comment below to enable GPU inference
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1 #set to "all" to use all GPUs
              capabilities: [gpu]
    #Remove comment above to enable GPU inference
...
```

#### Enabling GPU on local run

In `run_local.sh` set the `USE_CUDA` flag to 1

## API usage

This section provides basic instructions on how to interact with the API after deployment.

### Endpoints

The API offers the following endpoints:

- **Voices List**:
  - **GET** `/api/voices`
  - Description: Retrieves a list of available voices and languages supported by the TTS service.

- **Synthesize Speech (Short)**:
  - **POST** `/api/short`
  - Description: Sends text to synthesize into speech and returns an audio file in WAV format. This endpoint is ideal for testing purposes with short text inputs. It can accept either a specific voice or a language code to use the default voice for that language.
  - Payload example:
    ```json
    {
      "text": "Hola, món!",
      "voice": "catotron-ona"
    }
    ```
    or
    ```json
    {
      "text": "Hola, món!",
      "lang": "ca"
    }
    ```

- **Long Synthesis**:
  - **POST** `/api/long`
  - Description: Processes longer texts or multiple sentences and returns a single concatenated audio file in MP3 format. Recommended for multi-sentence requests. Like the short endpoint, it can also accept either a voice or a language code.
  - Payload example:
    ```json
    {
      "text_paragraphs": ["Hola, món!", "Benvinguts al nostre servei."],
      "voice": "catotron-ona"
    }
    ```
    or
    ```json
    {
      "text_paragraphs": ["Hola, món!", "Benvinguts al nostre servei."],
      "lang": "ca"
    }
    ```

### How to Send Requests

You can use any HTTP client to send requests to these endpoints. Here's an example using `curl` for the short synthesis endpoint:

```bash
curl -X POST http://localhost:5050/api/short \
     -H 'Content-Type: application/json' \
     -d '{"text":"Hola, món!", "voice":"catotron-ona"}'
     --output hola.wav
```

### Response Handling

Responses from the API will either be JSON-formatted data containing the results or metadata, or audio files depending on the endpoint accessed. Ensure your client properly handles the expected type of response.

### Error Handling

Errors are returned as JSON objects with a `message` field describing the error, accompanied by an appropriate HTTP status code. For example:

```json
{
  "message": "El text no pot estar buit"
}
```

Make sure to check the status code and handle errors accordingly in your client application.

## Demo page

A simple user interface is served at [http://localhost:5050](http://localhost:5050). If you like a different header, just replace `static/header.png` with an image you like.

![Demo TTS interface](img/default-demo-page.png)

## Language specific text normalization

One usually needs to normalize certain textual expressions into their spoken form for proper synthesis. These expressions include:

- Addresses
- Telephone numbers
- Numbers
- E-mail addresses 

You can specify how these conversions should be done for your language by following the procedure:

1. Create a directory named with your language code under `utils/preprocessors`
2. Create a script called `preprocessor.py` under that directory
3. Define a function with the name `text_preprocess` inside `preprocessor.py` that takes the input text as input and returns the normalized form.

If you want to specify different preprocessors for different voices, you can add the field `preprocessor` to your model configution in `config.json` with the name of your preprocessor script. e.g. having `text_preprocess` defined under `utils/preprocessors/xx/my_preprocessor.py`, you need to specify the voice in the config as:

```
    {
        "voice": "my-voice",
        "lang": "xx",
        "model_type": "coqui",
        "preprocessor": "my_preprocessor",
        "tts_config_path": "xx/config.json",
        "tts_model_path": "xx/model.pth",
        "load": true
    }
```

You can see example preprocessors in the repository.

## Languages

### Galician

Models available in [Proxecto Nós's HuggingFace repository](https://huggingface.co/collections/proxectonos/tts-models-65cf35498df786a4d59bafa4)

If you're using a phonetic model that depends on Cotovia library, you need to make sure:

1. Have a processor with `amd64` or `i386` architecture
2. Create an empty directory with name `deb` in the project directory
3. Download binary packages `cotovia_0.5_<arch>.deb` and `cotovia-lang-gl_0.5_all.deb` to `deb` directory from https://sourceforge.net/projects/cotovia/files/Debian%20packages/ 

Then if you're running locally on a debian based machine, install cotovia manually using the commands:

```
dpkg -i deb/cotovia_0.5_amd64.deb
dpkg -i deb/cotovia-lang-gl_0.5_all.deb
```

If you prefer to run with docker, use the corresponding `Dockerfile` that installs them. You can execute the following commands to do that:

```
mv Dockerfile Dockerfile-nogl
mv docker/Dockerfile-gl-cotovia Dockerfile
```

### Ladino

Models available in [Ladino Data Hub](https://data.sefarad.com.tr/dataset/tts-training-dataset)

### Catalan

- [Catotron Ona](https://g4e5.c13.e2-2.dev/dataset-share/catotron-ona-fast-speech-v0.2.zip) - License: OpenRail, Data: UPC's [FestCat dataset](http://festcat.talp.cat/download.php) 
- Catotron Pau (coming soon)
