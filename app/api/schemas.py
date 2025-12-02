from enum import Enum
from pydantic import BaseModel


class LanguageOCR(Enum):
    English = "eng"
    Spanish = "spa"
    Arabic = "ara"
    French = "fra"
    German = "deu"
    Farsi = "fas"


class OCROption(Enum):
    NoOcr = "no_ocr"
    TryOcr = "try_ocr"
    ForceOcr = "force_ocr"


class JsonRequestTextUrl(BaseModel):
    url: str
    max_workers: int = 32
    eng_numbering: bool = False
    ocr_mode: str = "no_ocr"
    ocr_language: str = "fas"


class JsonRequestImageUrl(BaseModel):
    url: str
    max_workers: int = 32


class JsonRequestTikaUrl(BaseModel):
    url: str
    eng_numbering: bool = False


class JsonRequestOcrUrl(BaseModel):
    url: str
    language: str = "fas"
    max_workers: int = 32
    eng_numbering: bool = False


class JsonRequestTextBase64(BaseModel):
    base64_pdf: str
    max_workers: int = 32
    eng_numbering: bool = False
    ocr_mode: str = "no_ocr"
    ocr_language: str = "fas"


class JsonRequestImageBase64(BaseModel):
    base64_pdf: str
    max_workers: int = 32


class JsonRequestTikaBase64(BaseModel):
    base64_pdf: str
    eng_numbering: bool = False


class JsonRequestOcrBase64(BaseModel):
    base64_pdf: str
    language: str = "fas"
    max_workers: int = 32
    eng_numbering: bool = False
