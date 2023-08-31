from langdetect import detect
from helper_files.convert_language import resolve


def detect_title(title:str):
    str = title
    strc = " ".join([token.capitalize() for token in str.split()])
    lang = resolve(detect(strc))
    return lang
