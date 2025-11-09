import re



def normalize_digits_and_fix_order(
        text: str,
        eng_numbering: bool = False,
) -> str:
    normalizeed_text = re.sub(
        r'[\u0660-\u0669\u06F0-\u06F9/]+',
        lambda m: m.group(0)[::-1],
        text,
    )

    if eng_numbering:
        normalizeed_text = digits_to_latin(normalizeed_text)

    return normalizeed_text

def digits_to_latin(text: str):
    # Maps for Arabic-Indic and Eastern Arabic-Indic (Persian) digits -> Western digits
    ARABIC_INDIC_MAP = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
    PERSIAN_MAP = {ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}

    # Combined translation table
    TRANSLATE_TABLE = {**ARABIC_INDIC_MAP, **PERSIAN_MAP}

    return text.translate(TRANSLATE_TABLE)
