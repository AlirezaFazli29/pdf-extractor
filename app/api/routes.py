import os
import fitz
import httpx
import PyPDF2
import base64
import tempfile
from tika import parser
from ..core.extractor import (
    MuExtractor,
    OCRExtractor,
    PyPDFExtractor,
)
from fastapi import File, Form
from .schemas import LanguageOCR
from ..core.utils import digits_to_latin
from fastapi.responses import JSONResponse
from pytesseract import get_tesseract_version
from fastapi import FastAPI, UploadFile, HTTPException


TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998")
app = FastAPI(title="Document Extractor")


@app.get(
    path = "/",
    tags = [
        "Health",
    ],
)
async def root():
    return JSONResponse(
        {
            "message": "Service is up and running",
            "supported models":
            [
                "PyMuPDF",
                "PyPDF2",
                "Apache Tika",
                "Tesseract OCR",
            ]
        }
    )


@app.post(
    path = "/file_to_base64/",
    tags = [
        "Health",
    ],
)
async def file_to_base64(
        file: UploadFile = File(...),
):
    try:
        file_data = await file.read()
        base64_string = base64.b64encode(file_data).decode("utf-8")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not process the uploaded file."
        )

    return JSONResponse(
        {
            "filename": file.filename,
            "base64_string": base64_string
        }
    )


@app.get(
    path="/mu_health/",
    tags=[
        "Health",
        "PyMuPDF",
    ]
)
async def mu_health_check():
    try:
        doc = fitz.__doc__.replace("\n", " ").strip()
        return JSONResponse(
            status_code=200,
            content={
                "status": doc,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e),
            }
        )
    

@app.get(
    path="/pypdf_health/",
    tags=[
        "Health",
        "PyPDF2",
    ]
)
async def pypdf_health_check():
    try:
        doc = PyPDF2.__doc__.replace("\n", " ").strip()
        return JSONResponse(
            status_code=200,
            content={
                "status": doc,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e),
            }
        )


@app.get(
    path="/tika_health/",
    tags=[
        "Health",
        "Apache Tika",
    ]
)
async def tika_health_check():
    try:
        state = httpx.get(os.path.join(TIKA_URL, "tika"))
        return JSONResponse(
            status_code=200,
            content={
                "status": state.text.replace(" Please PUT\n", "").strip(),
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e),
            }
        )


@app.get(
    path="/tesseract_health/",
    tags=[
        "Health",
        "Tesseract OCR",
    ]
)
async def tesseract_health():
    try:
        version = get_tesseract_version().__str__()
        return JSONResponse(
            status_code=200,
            content={
                "status": f"Using pytesseract version {version} as the ocr core",
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e),
            }
        )


@app.post(
    path="/extract_text_mu/",
    tags=[
        "PyMuPDF",
    ]
)
async def extract_text_mu(
    file: UploadFile = File(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF file allowed."
        )

    
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        content = await file.read()

        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file",
            )
        
        tmp.write(content)
        tmp.flush()

        extractor = MuExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "uploaded file",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_image_mu/",
    tags=[
        "PyMuPDF",
    ]
)
async def extract_image_mu(
    file: UploadFile = File(...),
    max_workers: int = Form(32),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF file allowed."
        )
    
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        content = await file.read()

        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file",
            )
        
        tmp.write(content)
        tmp.flush()

        extractor = MuExtractor(file_path=tmp.name)
        results = extractor.extract_image(max_workers=max_workers)

        response = {
            "source": "uploaded file",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_text_url_mu/",
    tags=[
        "PyMuPDF",
    ]
)
async def extract_text_url_mu(
    url: str = Form(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
):
    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Could not fetch file from URL: {response.reason_phrase}",
                )
            content = response.content
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Request error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )
    
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )
    
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = MuExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "url",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(response)


@app.post(
    path="/extract_image_url_mu/",
    tags=[
        "PyMuPDF",
    ]
)
async def extract_image_url_mu(
    url: str = Form(...),
    max_workers: int = Form(32),
):
    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Could not fetch file from URL: {response.reason_phrase}",
                )
            content = response.content
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Request error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )
    
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )
    
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = MuExtractor(file_path=tmp.name)
        results = extractor.extract_image(max_workers=max_workers)

        response = {
            "source": "url",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(response)


@app.post(
    path="/extract_text_base64_mu/",
    tags=[
        "PyMuPDF",
    ]
)
async def extract_text_base64_mu(
    base64_pdf: str = Form(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
):
    try:
        content = base64.b64decode(base64_pdf)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = MuExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "base64 input",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_image_base64_mu/",
    tags=[
        "PyMuPDF",
    ]
)
async def extract_image_base64_mu(
    base64_pdf: str = Form(...),
    max_workers: int = Form(32),
):
    try:
        content = base64.b64decode(base64_pdf)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = MuExtractor(file_path=tmp.name)
        results = extractor.extract_image(max_workers=max_workers)

        response = {
            "source": "base64 input",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_text_pypdf/",
    tags=[
        "PyPDF2",
    ]
)
async def extract_text_pypdf(
    file: UploadFile = File(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF file allowed."
        )

    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        content = await file.read()

        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file",
            )
        
        tmp.write(content)
        tmp.flush()

        extractor = PyPDFExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "uploaded file",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_text_url_pypdf/",
    tags=[
        "PyPDF2",
    ]
)
async def extract_text_url_pypdf(
    url: str = Form(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
):
    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Could not fetch file from URL: {response.reason_phrase}",
                )
            content = response.content
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Request error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )
    
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )
    
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = PyPDFExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "url",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(response)


@app.post(
    path="/extract_text_base64_pypdf/",
    tags=[
        "PyPDF2",
    ]
)
async def extract_text_base64_pypdf(
    base64_pdf: str = Form(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
):
    try:
        content = base64.b64decode(base64_pdf)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = PyPDFExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "base64 input",
            "metadata": extractor.get_metadata(),
            "pages": results,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_text_tika/",
    tags=[
        "Apache Tika",
    ]
)
async def extract_text_tika(
    file: UploadFile = File(...),
    eng_numbering: bool = Form(False),
):
    _, ext = os.path.splitext(file.filename)
    if not ext:
        ext = ""
    
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp.flush()

        parsed_doc = parser.from_file(
            tmp.name,
            serverEndpoint=TIKA_URL,
        )

        content = digits_to_latin(
            parsed_doc.get("content")
        ) if eng_numbering else parsed_doc.get("content")

        response = {
            "source": "uploaded file",
            "metadata": parsed_doc.get("metadata"),
            "content": content,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_text_url_tika/",
    tags=[
        "Apache Tika",
    ]
)
async def extract_text_url_tika(
    url: str = Form(...),
    eng_numbering: bool = Form(False),
):
    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Could not fetch file from URL: {response.reason_phrase}",
                )
            content = response.content
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Request error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )
    
    parsed_doc = parser.from_buffer(
        content,
        serverEndpoint=TIKA_URL,
    )

    content = digits_to_latin(
        parsed_doc.get("content")
    ) if eng_numbering else parsed_doc.get("content")

    response = {
        "source": "uploaded file",
        "metadata": parsed_doc.get("metadata"),
        "content": content,
    }

    return JSONResponse(response)


@app.post(
    path="/extract_text_base64_tika/",
    tags=[
        "Apache Tika",
    ]
)
async def extract_text_base64_tika(
    base64_pdf: str = Form(...),
    eng_numbering: bool = Form(False),
):
    try:
        content = base64.b64decode(base64_pdf)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    parsed_doc = parser.from_buffer(
        content,
        serverEndpoint=TIKA_URL,
    )

    content = digits_to_latin(
        parsed_doc.get("content")
    ) if eng_numbering else parsed_doc.get("content")

    response = {
        "source": "uploaded file",
        "metadata": parsed_doc.get("metadata"),
        "content": content,
    }

    return JSONResponse(content=response)


@app.post(
    path="/extract_text_tesseract/",
    tags=[
        "Tesseract OCR",
    ]
)
async def extract_text_tesseract(
    file: UploadFile = File(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
    language: LanguageOCR = Form(LanguageOCR.Farsi.value),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF file allowed."
        )

    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        content = await file.read()

        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file",
            )
        
        tmp.write(content)
        tmp.flush()

        extractor = OCRExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            lang=language.value,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "uploaded file",
            "pages": results,
        }

    return JSONResponse(content=response)


@app.post(
    path="/extract_text_url_tesseract/",
    tags=[
        "Tesseract OCR",
    ]
)
async def extract_text_url_tesseract(
    url: str = Form(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
    language: LanguageOCR = Form(LanguageOCR.Farsi.value),
):
    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Could not fetch file from URL: {response.reason_phrase}",
                )
            content = response.content
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Request error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )
    
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )
    
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = OCRExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            lang=language.value,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "url",
            "pages": results,
        }

    return JSONResponse(response)


@app.post(
    path="/extract_text_base64_tesseract/",
    tags=[
        "Tesseract OCR",
    ]
)
async def extract_text_base64_tesseract(
    base64_pdf: str = Form(...),
    max_workers: int = Form(32),
    eng_numbering: bool = Form(False),
    language: LanguageOCR = Form(LanguageOCR.Farsi.value),
):
    try:
        content = base64.b64decode(base64_pdf)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".pdf",
    ) as tmp:
        tmp.write(content)
        tmp.flush()

        extractor = OCRExtractor(file_path=tmp.name)
        results = extractor.extract_text(
            max_workers=max_workers,
            lang=language.value,
            eng_numbering=eng_numbering,
        )

        response = {
            "source": "base64 input",
            "pages": results,
        }

    return JSONResponse(content=response)
