"""HTTP API of HATARI.

Run locally from the repository root:

    uvicorn hatari.api.app:app --port 8000

The message is analysed in memory and returned. It is not stored, and it is
not written to the logs, since only the method and path of requests are logged.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from hatari.service.analyzer import Analyzer, ModelNotFound
from hatari.text.preprocessing import MAX_CHARACTERS, InvalidMessage

app = FastAPI(
    title="HATARI",
    description="Analyse d'un message suspect. Think before you trust.",
    version="0.1.0",
)


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_CHARACTERS,
                         description="Texte du message à analyser. Il n'est pas conservé.")


@lru_cache(maxsize=1)
def get_analyzer() -> Analyzer:
    return Analyzer()


def analyzer_dependency() -> Analyzer:
    try:
        return get_analyzer()
    except ModelNotFound as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/health")
def health() -> dict:
    try:
        get_analyzer()
    except ModelNotFound:
        return {"status": "degraded", "model_loaded": False}
    return {"status": "ok", "model_loaded": True}


@app.post("/analyze")
def analyze(request: MessageRequest, analyzer: Analyzer = Depends(analyzer_dependency)) -> dict:
    try:
        return analyzer.analyze(request.message).to_dict()
    except InvalidMessage as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
