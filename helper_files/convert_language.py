iso_639_1={'af': 'afr', 'sq': 'alb', 'ar': 'ara', 'bn': 'ben', 'bg': 'bul', 'ca': 'cat', 'zh': 'chi', 'cs': 'cze', 'da': 'dan', 'nl': 'dut', 'en': 'eng', 'et': 'est', 'fi': 'fin', 'fr': 'fre', 'de': 'ger', 'el': 'gre', 'gu': 'guj', 'he': 'heb', 'hi': 'hin', 'hr': 'hrv', 'hu': 'hun', 'id': 'ind', 'it': 'ita', 'ja': 'jpn', 'kn': 'kan', 'ko': 'kor', 'lv': 'lav', 'lt': 'lit', 'mk': 'mac', 'ml': 'mal', 'mr': 'mar', 'ne': 'nep', 'no': 'nor', 'pa': 'pan', 'fa': 'per', 'pl': 'pol', 'pt': 'por', 'ro': 'rum', 'ru': 'rus', 'sk': 'slo', 'sl': 'slv', 'so': 'som', 'es': 'spa', 'sw': 'swa', 'sv': 'swe', 'ta': 'tam', 'te': 'tel', 'tl': 'tgl', 'th': 'tha', 'tr': 'tur', 'uk': 'ukr', 'ur': 'urd', 'vi': 'vie', 'cy': 'wel'}
iso_639_2={'afr': 'af', 'alb': 'sq', 'ara': 'ar', 'ben': 'bn', 'bul': 'bg', 'cat': 'ca', 'chi': 'zh', 'cze': 'cs', 'dan': 'da', 'dut': 'nl', 'eng': 'en', 'est': 'et', 'fin': 'fi', 'fre': 'fr', 'ger': 'de', 'gre': 'el', 'guj': 'gu', 'heb': 'he', 'hin': 'hi', 'hrv': 'hr', 'hun': 'hu', 'ind': 'id', 'ita': 'it', 'jpn': 'ja', 'kan': 'kn', 'kor': 'ko', 'lav': 'lv', 'lit': 'lt', 'mac': 'mk', 'mal': 'ml', 'mar': 'mr', 'nep': 'ne', 'nor': 'no', 'pan': 'pa', 'per': 'fa', 'pol': 'pl', 'por': 'pt', 'rum': 'ro', 'rus': 'ru', 'slo': 'sk', 'slv': 'sl', 'som': 'so', 'spa': 'es', 'swa': 'sw', 'swe': 'sv', 'tam': 'ta', 'tel': 'te', 'tgl': 'tl', 'tha': 'th', 'tur': 'tr', 'ukr': 'uk', 'urd': 'ur', 'vie': 'vi', 'wel': 'cy'}


def resolve(code):
    try:
        code=iso_639_1[code]
        return code
    except:
        return iso_639_2[code]