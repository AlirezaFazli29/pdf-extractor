import fitz
from .utils import normalize_digits_and_fix_order
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
        file_path, pg_num, eng_numbering = args
        with fitz.open(file_path) as doc:
            pg_txt = doc.get_page_text(pg_num)
            pg_txt = normalize_digits_and_fix_order(
                text=pg_txt,
                eng_numbering=eng_numbering
            )
        return {
            "page_number": pg_num + 1,
            "text": pg_txt
        }

    def extract_text(
            self,
            max_workers: int = 64,
            eng_numbering: bool = True,
    ) -> list[dict]:
        results = []

        for i in range(0, self.page_count, max_workers):
            chunk_args = [
                (self.file_path, j, eng_numbering)
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