import re
import os
import subprocess

COTOVIA_IN_TXT_PATH = 'text.txt'
COTOVIA_OUT_TRA_PATH = 'text.tra'
TRA3 = True

PUNCLIST = [';', '?', '¿', ',', ':', '.', '!', '¡']

SIMULATE_COTOVIA = False

def canBeNumber(n):
    try:
        int(n)
        return True
    except ValueError:
        # Not a number
        return False

def accent_convert(phontrans):
    transcript = re.sub('a\^','á',phontrans)
    transcript = re.sub('e\^','é',transcript)
    transcript = re.sub('i\^','í',transcript)
    transcript = re.sub('o\^','ó',transcript)
    transcript = re.sub('u\^','ú',transcript)
    transcript = re.sub('E\^','É',transcript)
    transcript = re.sub('O\^','Ó',transcript)
    return transcript

def remove_tra3_tags(phontrans):
    s = re.sub(r'#(.+?)#', r'', phontrans)
    s = re.sub(r'%(.+?)%', r'', s)
    s = re.sub(' +',' ',s)
    s = re.sub('-','',s)
    return s.strip()

def to_cotovia(text_segments, tra3=TRA3):
    with open(COTOVIA_IN_TXT_PATH, 'w') as f:
        for seg in text_segments:
            if seg:
                f.write(seg + '\n')
            else:
                f.write(',' + '\n')

    if SIMULATE_COTOVIA:
        subprocess.run(["bash", "./utils/preprocessors/gl/fake_cotovia.sh", COTOVIA_IN_TXT_PATH])
    elif tra3:
        subprocess.run(["cotovia", "-i", COTOVIA_IN_TXT_PATH, "-t3", "-n"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        subprocess.run(["cotovia", "-i", COTOVIA_IN_TXT_PATH, "-t1", "-n"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    segs = []
    try:
        with open(COTOVIA_OUT_TRA_PATH, 'r') as f:
            segs = [line.rstrip() for line in f]
            if tra3:
                segs = [remove_tra3_tags(line) for line in segs]
    except:
        print("ERROR: Couldn't read cotovia output")


  
    return segs

#Splits text from punctuation marks, gives list of segments in between and the punctuation marks. Skips punctuation not present in training.
def split_punc(text):
    segments = []
    puncs = []
    curr_seg = ""
    for c in text:
        if c in PUNCLIST:
            segments.append(curr_seg.strip())
            puncs.append(c)
            curr_seg = ""
        else:
            curr_seg += c
    
    segments.append(curr_seg.strip())

    return segments, puncs

def merge_punc(text_segs, puncs):
    merged_str = ""
    for i, seg in enumerate(text_segs):
        merged_str += seg + " "
        
        if i < len(puncs):
            merged_str += puncs[i] + " "
    return merged_str.strip()


def text_preprocess(text):
    #Split from punc
    text_segments, puncs = split_punc(text)

    cotovia_phon_segs = to_cotovia(text_segments)

    cotovia_phon_str = merge_punc(cotovia_phon_segs, puncs)

    phon_str = accent_convert(cotovia_phon_str)

    return phon_str
    