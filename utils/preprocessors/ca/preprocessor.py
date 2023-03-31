from .cat_number_letter import num_let
import re

def canBeNumber(n):
    try:
        int(n)
        return True
    except ValueError:
        # Not a number
        return False

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

# STUB: Function to write out letter (b->be, w->ve doble)
# def pronounce_letter(letter):
#     #Source: https://www.cursdecatala.com/es/pronunciar-el-alfabeto-catalan/

def remove_nonnumber(text):
    return re.sub('[^0-9]','', text)

def text_preprocess(text):
    text = text.strip()
    text = text.replace('&', 'i')
    text = re.sub('[Ö|ö]', 'o', text)
    text = re.sub('[ş|Ş]', 's', text)
    text = re.sub('[ü|Ü]', 'u', text)
    text = re.sub('[ç|Ç]', 'c', text)
    text = re.sub('[İ|ı]', 'i', text)


    return ' '.join([num_let(int(remove_nonnumber(t))) if has_numbers(t) else t for t in text.split()])