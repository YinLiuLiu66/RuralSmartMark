from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ruralsmartmark.config import settings

app = FastAPI(
    title="RuralSmartMark API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ruralsmartmark"}
