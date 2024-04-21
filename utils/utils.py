import os
import json
from typing import Union
import string
from nltk.tokenize import sent_tokenize

ENDING_PUNCTUATION = ["?", ".", "!"] #TODO: Latin only

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

def universal_text_normalize(text: str):
    if all(x in string.punctuation for x in text):
        return ""
    text = text.strip()
    if not text[-1] in ENDING_PUNCTUATION:
        text = text + "."

    return text

#Parse sentences from text using NLTK sent_tokenize. (Warning: English-based)
def parse_sents(text:str):
    sents = []
    sent_candidates = sent_tokenize(text.strip())
    return sent_candidates 