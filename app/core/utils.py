import re

# Maps for Arabic-Indic and Eastern Arabic-Indic (Persian) digits -> Western digits
ARABIC_INDIC_MAP = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}   # U+0660..U+0669
PERSIAN_MAP = {ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}        # U+06F0..U+06F9

# Combined translation table
TRANSLATE_TABLE = {**ARABIC_INDIC_MAP, **PERSIAN_MAP}

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
        normalizeed_text = normalizeed_text.translate(TRANSLATE_TABLE)

    return normalizeed_text
