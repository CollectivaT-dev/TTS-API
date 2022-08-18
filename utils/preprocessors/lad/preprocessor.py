from .ladino_number_letter import num_let

def canBeNumber(n):
    try:
        int(n)
        return True
    except ValueError:
        # Not a number
        return False


def text_preprocess(text):
    text = text.strip()
    text = text.replace('&', 'i')
    return ' '.join([num_let(int(t)) if canBeNumber(t) else t for t in text.split()])