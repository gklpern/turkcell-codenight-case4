# -*- coding: utf-8 -*-
"""
llm_client.py — OpenAI ile kısa Türkçe fatura özeti (Chat Completions)

Kullanım:
  - Ortam değişkenleri (opsiyonel):
      OPENAI_API_KEY=sk-...
      LLM_MODEL=gpt-4o-mini
      OPENAI_BASE=https://api.openai.com  # (opsiyonel, farklı endpoint için)
  - Python'da:
      from llm_client import render_bill_summary_llm
      text = render_bill_summary_llm(payload)  # payload = explain_engine.build_explain(...) çıktısı
"""

from __future__ import annotations
import os
import json
from typing import Any, Dict, List, Optional

import requests

MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_BASE = os.getenv("OPENAI_BASE", "https://api.openai.com")


def _truncate(s: str, limit: int = 12000) -> str:
    """Basit güvenlik: çok uzun promptları kes."""
    return s if len(s) <= limit else s[:limit]


def call_llm(
    prompt: str,
    max_new_tokens: int = 220,
    temperature: float = 0.2,
    timeout: int = 60,
    api_key: Optional[str] = None,
) -> str:
    """
    OpenAI Chat Completions ile tek atış (prompt -> output).
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY bulunamadı.")

    prompt = _truncate(prompt)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Kısa Türkçe fatura özeti yaz. 2-3 cümle. "
                    "120 kelimeyi geçme. Rakamları değiştirme, TL olarak belirt."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": float(temperature),
        "max_tokens": int(max_new_tokens),
    }

    resp = requests.post(
        f"{OPENAI_BASE}/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return (data["choices"][0]["message"]["content"] or "").strip()


def render_bill_summary_llm(payload: Dict[str, Any]) -> str:
    """
    payload: explain_engine.build_explain(...) çıktısı
      - payload["summary"]: {period,total,taxes,usage_summary,baseline_total_mean,total_delta}
      - payload["breakdown"]: [{category,total,lines:[{text,amount}]}]
      - payload["contributors"]: [{category,current,baseline_mean,delta}, ...]
    """
    summary = payload.get("summary", {})
    usage = summary.get("usage_summary", {})
    breakdown = payload.get("breakdown", [])
    contributors = (payload.get("contributors") or [])[:3]

    prompt = f"""
Görev: Bir GSM faturasını 2-3 cümlede kısa Türkçe özetle.
Kurallar:
- Verilen rakamları asla değiştirme ve yeni hesap yapma.
- Önce toplamı söyle; ardından artış/azalışın ana nedenini belirt.
- Son cümlede tek bir tasarruf ipucu ver (varsa).

Dönem: {summary.get('period')}
Toplam: {summary.get('total')} TL
Önceki 3 ay ortalaması: {summary.get('baseline_total_mean')}
Toplam fark (bu ay - ortalama): {summary.get('total_delta')}

Kullanım: {usage.get('gb')} GB data, {usage.get('minutes')} dk, {usage.get('sms')} SMS, roaming {usage.get('roaming_gb')} GB

Kategori özeti (JSON):
{json.dumps(breakdown, ensure_ascii=False, indent=2)}

Öne çıkan katkılar (delta sırasına göre, JSON):
{json.dumps(contributors, ensure_ascii=False, indent=2)}

Yalnızca 2-3 cümle yaz. Rakamları olduğu gibi kullan.
""".strip()

    try:
        return call_llm(prompt)
    except Exception as e:
        # Basit fallback (LLM çalışmazsa)
        t = summary.get("total")
        d = summary.get("total_delta")
        top_cat = contributors[0]["category"] if contributors else None
        trend = "yüksek" if (isinstance(d, (int, float)) and d and d > 0) else "düşük"
        hint = f"En büyük etki {top_cat} kaleminden geliyor." if top_cat else ""
        return f"Bu ay faturan {t} TL oldu. Önceki ortalamaya göre {trend}. {hint}".strip()
