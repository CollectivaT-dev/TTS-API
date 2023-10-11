from .cat_number_letter import num_let
from collections import Counter
import re
from urllib.parse import urlparse
import csv
import logging
import os

logger = logging.getLogger(__name__)

# Get the current directory of the script
current_dir = os.path.dirname(__file__)

LETTERS = {line.split(',')[0]: line.split(',')[1].strip() for line in open(os.path.join(current_dir, 'letters.csv'))}
MONTHS = {int(line.split(',')[0]): line.split(',')[1].strip() for line in open(os.path.join(current_dir, 'months.csv'))}
SYMBOLS = {line.split(',')[0]: line.split(',')[1].strip() for line in open(os.path.join(current_dir, 'symbols.csv'))}
ACRONYMS = {line.split(',')[0]: line.split(',')[1].strip() for line in open(os.path.join(current_dir, 'acronyms.csv'))}
UNITS = {line.split(',')[0]: line.split(',')[1].strip() for line in open(os.path.join(current_dir, 'units.csv'))}

PUNCLIST = [';', '?', '¿', ',', ':', '.', '!', '¡']
URL_PATTERN = re.compile(r'^(https?://|www\.)\S+', re.IGNORECASE)
ALLOWED_IN_NUMERICAL = [',', '.']

#Splits text from punctuation marks, gives list of segments in between and the punctuation marks. Skips punctuation not present in training.
def split_punc(text):
    text = fix_date(text)
    segments = []
    puncs = []
    curr_seg = ""
    for i, c in enumerate(text):
        #check next char
        next_is_space_or_end = False
        if i < len(text) - 1:
            next_is_space_or_end = text[i+1].isspace()
        else:
            next_is_space_or_end = True
        if c in PUNCLIST and next_is_space_or_end:
            segments.append(curr_seg.strip())
            puncs.append(c)
            curr_seg = ""
        else:
            curr_seg += c
    
    segments.append(curr_seg.strip())

    return segments, puncs

date_pattern = r'\b(\d{2})\.(\d{2})\.(\d{4})\b'

def fix_date(text):
    # Use re.sub() to replace dots with slashes in matched dates
    converted_text = re.sub(date_pattern, r'\1/\2/\3', text)
    return converted_text

def merge_punc(text_segs, puncs):
    merged_str = ""
    for i, seg in enumerate(text_segs):
        merged_str += seg
        
        if i < len(puncs):
            merged_str += puncs[i] + " "
    return merged_str.strip()

def extract_time(text):
    # Regular expression pattern for HH.MM format
    pattern = r'\b(0[0-9]|1[0-9]|2[0-3])\.([0-5][0-9])\b'
    
    # Find the first match
    match = re.search(pattern, text)
    
    if match:
        # Extract hour and minute as integers
        hour = int(match.group(1))
        minute = int(match.group(2))
        return hour, minute
    else:
        return None, None

def read_hours(hour_part, minute_part):
    # hour_processed = num_let(int(remove_nonnumber(hour_part)))
    # minute_processed = num_let(int(remove_nonnumber(minute_part)))
    text = num_let(hour_part) + " i " + num_let(minute_part)
    return text

def read_dates(text):
    if "/" in text:
        day, month, year = text.split('/')
    elif "-" in text:
        day, month, year = text.split('-')
    day_processed = num_let(int(remove_nonnumber(day)))
    year_processed = num_let(int(remove_nonnumber(year)))
            
    month_processed = MONTHS.get(int(month), '')
    text = day_processed + " de " + month_processed + " de " + year_processed
    return text

def separate_numbers_from_text(expression):
    prev_was_digit = False
    prev_was_alpha = False
    separated_expression = ''
    for i, c in enumerate(expression):
        curr_alpha = c.isalpha()
        curr_digit = c.isdigit()
        if curr_alpha and prev_was_digit:
            separated_expression += ' ' + c
            prev_was_alpha = curr_alpha
            prev_was_digit = curr_digit
        elif curr_digit and prev_was_alpha:
            separated_expression += ' ' + c
            prev_was_alpha = curr_alpha
            prev_was_digit = curr_digit
        elif curr_alpha or curr_digit:
            separated_expression += c
            prev_was_alpha = curr_alpha
            prev_was_digit = curr_digit
        elif c in ALLOWED_IN_NUMERICAL:
            separated_expression += c
        else:
            separated_expression += ' ' + c
            
    return separated_expression

def pronounce_letter(letter):
    return LETTERS.get(letter.lower(), letter)

def pronounce_symbol(letter):
    return SYMBOLS.get(letter, letter)

def pronounce_unit(unit):
    return UNITS.get(unit, unit)

def pronounce_acronym(text):
    return ACRONYMS.get(text, text)

def convert_numbered(exp, next_token=""):
    exp = separate_numbers_from_text(exp)
    tokens = exp.split()
    
    converted = ''
    
    for tok in tokens:
        if has_numbers(tok):
            h,m = extract_time(tok)
            if h and m:
                converted += read_hours(h, m)
            elif tok.count('/') == 2 or tok.count('-') == 2:
                #condition that follows DD/MM/YYYY
                converted += read_dates(tok)
            else:    
                tok = tok.replace(".", "")
                tok = tok.replace(",", ".")
                converted += num_let(float(tok))
        else:
            converted_tok = pronounce_unit(tok)
            converted_tok = pronounce_symbol(converted_tok)
            if len(converted_tok) == 1:    
                converted_tok = pronounce_letter(converted_tok)
            converted += converted_tok
        converted += " "

    return converted.strip()

def is_url(expression):
    return bool(URL_PATTERN.match(expression))

def convert_url(text):
    if is_url(text):
        text = text.replace('http://', '')
        text = text.replace('https://', '')
        text = text.replace('www', 've doble ve doble ve doble ')
        text = text.replace('.', ' punt ')
        text = re.sub(' +', ' ', text)
    return text

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def remove_nonnumber(text):
    return re.sub('[^0-9]','', text)

def fix_special_symbols(text):
    text = re.sub('[Ö|ö]', 'o', text)
    text = re.sub('[ş|Ş]', 'x', text)
    text = re.sub('[İ|ı]', 'i', text)
    text = text.replace("(", ", ")
    text = text.replace(")", "")
    return text

def text_preprocess(text):
    text = fix_special_symbols(text)
    segs, puncs = split_punc(text)

    new_segs = []
    number_behind = False

    for seg in segs:
        new_seg_tokens = []
        seg_tokens = seg.split()

        for tok in seg_tokens:
            try:
                
                
                if has_numbers(tok):
                    tok = convert_numbered(tok)
                    number_behind = True
                elif number_behind:
                    tok = pronounce_unit(tok)
                    number_behind = False

                tok = pronounce_acronym(tok)
                tok = convert_url(tok)
                tok = pronounce_letter(tok)
                tok = pronounce_symbol(tok)
            except Exception as e:
                logger.error(f"Normalization fail + {e}")
                
            new_seg_tokens.append(tok)

        new_segs.append(' '.join(new_seg_tokens))


    return merge_punc(new_segs,puncs)

