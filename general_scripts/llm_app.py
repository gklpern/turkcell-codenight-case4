# app.py (örnek minimal)
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict
from general_scripts.llm_client import render_bill_summary_llm

app = FastAPI()

class ExplainPayload(BaseModel):
    # explain_engine.build_explain(...) çıktısının aynısı/altkümeleri
    summary: Dict[str, Any]
    breakdown: list
    contributors: list | None = None

@app.post("/api/llm/summary")
def llm_summary(payload: ExplainPayload):
    # Pydantic objesini dict'e çevir
    data = payload.model_dump()
    text = render_bill_summary_llm(data)   # <<< Qwen2.5 ile özet üretir
    return {"text": text}
