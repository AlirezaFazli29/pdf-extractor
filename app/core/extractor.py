import fitz
import base64
import pytesseract
from .utils import (
    digits_to_latin,
    normalize_digits_and_fix_order,
)
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from concurrent.futures import ProcessPoolExecutor


class MuExtractor:

    def __init__(
            self,
            file_path: str,
    ):
        self.file_path = file_path
        with fitz.open(file_path) as doc:
            self.page_count = len(doc)

    @staticmethod
    def _extract_text(
            args,
    ) -> dict:
        file_path, pg_num, try_ocr, lang, eng_numbering = args
        with fitz.open(file_path) as doc:
            pg_txt = doc.get_page_text(pg_num)
            pg_txt = normalize_digits_and_fix_order(
                text=pg_txt,
                eng_numbering=eng_numbering
            )
            if try_ocr and not pg_txt:
                page = convert_from_path(
                    file_path,
                    first_page=pg_num+1,
                    last_page=pg_num+1,
                )
                pg_txt = pytesseract.image_to_string(page[0], lang=lang)
                pg_txt = digits_to_latin(
                    pg_txt
                ) if eng_numbering else pg_txt
        return {
            "page_number": pg_num + 1,
            "text": pg_txt
        }
    
    @staticmethod
    def _extract_image(
        args,
    ) -> dict:
        file_path, pg_num = args
        with fitz.open(file_path) as doc:
            pg_imgs = doc.get_page_images(pg_num)
            imgs_list = []
            for tup_img in pg_imgs:
                try: 
                    xref = tup_img[0]
                    temp_dict = doc.extract_image(xref)
                    image_bytes = temp_dict.get("image")
                    base64_str = base64.b64encode(image_bytes).decode("utf-8")
                    res = {
                        "image_name": tup_img[7],
                        "width_px": temp_dict.get("width"),
                        "height_px": temp_dict.get("height"),
                        "file_extension": temp_dict.get("ext"),
                        "image_size_bytes": temp_dict.get("size"),
                        "Bits_per_color_component": temp_dict.get("bpc"),
                        "compression_method": tup_img[-1],
                        "color_space": temp_dict.get("cs-name"),
                        "bounding_box": {
                            "x0": doc[pg_num].get_image_rects(xref)[0][0],
                            "y0": doc[pg_num].get_image_rects(xref)[0][1],
                            "x1": doc[pg_num].get_image_rects(xref)[0][2],
                            "y1": doc[pg_num].get_image_rects(xref)[0][3],
                        },
                        "image_base64": base64_str,
                    }
                    imgs_list.append(res)
                except:
                    continue
            return {
                "page_number": pg_num + 1,
                "images": imgs_list
            }

    def extract_text(
            self,
            max_workers: int = 64,
            eng_numbering: bool = True,
            try_ocr: bool = False,
            ocr_language: str = "fas"
    ) -> list[dict]:
        results = []

        for i in range(0, self.page_count, max_workers):
            chunk_args = [
                (self.file_path, j, try_ocr, ocr_language, eng_numbering)
                for j in range(i, min(i + max_workers, self.page_count))
            ]

            with ProcessPoolExecutor(
                max_workers=min(max_workers, len(chunk_args))
            ) as executor:
                chunk_results = list(
                    executor.map(
                        self._extract_text,
                        chunk_args,
                    )
                )

            results.extend(chunk_results)
        
        results.sort(key=lambda x: x["page_number"])

        return results
    
    def extract_image(
            self,
            max_workers: int = 64,
    ) -> list[dict]:
        results = []

        for i in range(0, self.page_count, max_workers):
            chunk_args = [
                (self.file_path, j)
                for j in range(i, min(i + max_workers, self.page_count))
            ]

            with ProcessPoolExecutor(
                max_workers=min(max_workers, len(chunk_args))
            ) as executor:
                chunk_results = list(
                    executor.map(
                        self._extract_image,
                        chunk_args,
                    )
                )

            results.extend(chunk_results)
        
        results.sort(key=lambda x: x["page_number"])

        return results

    def get_metadata(
            self,
    ) -> dict:
        with fitz.open(self.file_path) as doc:
            metadata = doc.metadata
        return metadata


class PyPDFExtractor:
    def __init__(
            self,
            file_path: str,
    ):
        self.file_path = file_path
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            self.page_count = len(reader.pages)
            del reader

    @staticmethod
    def _extract_text(
            args,
    ) -> dict:
        file_path, pg_num, try_ocr, lang, eng_numbering = args
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            page = reader.pages[pg_num]
            pg_txt = page.extract_text()
            pg_txt = normalize_digits_and_fix_order(
                text=pg_txt,
                eng_numbering=eng_numbering,
            )
            if try_ocr and not pg_txt:
                page = convert_from_path(
                    file_path,
                    first_page=pg_num+1,
                    last_page=pg_num+1,
                )
                pg_txt = pytesseract.image_to_string(page[0], lang=lang)
                pg_txt = digits_to_latin(
                    pg_txt
                ) if eng_numbering else pg_txt
        return {
            "page_number": pg_num + 1,
            "text": pg_txt
        }
    
    def extract_text(
            self,
            max_workers: int = 64,
            eng_numbering: bool = True,
            try_ocr: bool = False,
            ocr_language: str = "fas"
    ) -> list[dict]:
        results = []

        for i in range(0, self.page_count, max_workers):
            chunk_args = [
                (self.file_path, j, try_ocr, ocr_language, eng_numbering)
                for j in range(i, min(i + max_workers, self.page_count))
            ]

            with ProcessPoolExecutor(
                max_workers=min(max_workers, len(chunk_args))
            ) as executor:
                chunk_results = list(
                    executor.map(
                        self._extract_text,
                        chunk_args,
                    )
                )

            results.extend(chunk_results)
        
        results.sort(key=lambda x: x["page_number"])

        return results

    def get_metadata(
            self,
    ) -> dict:
        with open(self.file_path, "rb") as file:
            reader = PdfReader(file)
            metadata = reader.metadata            
        return metadata


class OCRExtractor:
    def __init__(
            self,
            file_path: str,
    ):
        self.file_path = file_path
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            self.page_count = len(reader.pages)
            del reader

    @staticmethod
    def _extract_text(
            args,
    ) -> dict:
        file_path, pg_num, lang , eng_numbering = args
        page = convert_from_path(
            file_path,
            first_page=pg_num+1,
            last_page=pg_num+1,
        )
        pg_txt = pytesseract.image_to_string(page[0], lang=lang)
        pg_txt = digits_to_latin(
            pg_txt
        ) if eng_numbering else pg_txt
        return {
            "page_number": pg_num + 1,
            "text": pg_txt,
        }
    
    def extract_text(
            self,
            max_workers: int = 64,
            lang: str = "fas",
            eng_numbering: bool = True,
    ) -> list[dict]:
        results = []

        for i in range(0, self.page_count, max_workers):
            chunk_args = [
                (self.file_path, j, lang, eng_numbering)
                for j in range(i, min(i + max_workers, self.page_count))
            ]

            with ProcessPoolExecutor(
                max_workers=min(max_workers, len(chunk_args))
            ) as executor:
                chunk_results = list(
                    executor.map(
                        self._extract_text,
                        chunk_args,
                    )
                )

            results.extend(chunk_results)
        
        results.sort(key=lambda x: x["page_number"])

        return results
