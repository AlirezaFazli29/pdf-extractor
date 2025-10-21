import gc
import fitz
from fastapi import FastAPI
from fastapi.responses import JSONResponse


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


@app.get(
    path="/mu_health/",
    tags=[
        "Health",
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

