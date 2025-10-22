import fitz
import httpx
import base64
import tempfile
from fastapi import File, Form
from fastapi.responses import JSONResponse
from fastapi import FastAPI, UploadFile, HTTPException
from ..core.extractor import (
    MuExtractor
)


app = FastAPI(title="PDF Extractor")


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
                "PyMuPDF"
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
    path="/extract_text_base64_mu/",
    tags=["PyMuPDF"]
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

