# -*- coding: utf-8 -*-
"""
LLM'siz fatura analizi:
- Anomali tespiti (toplam, katkı yapan kategoriler, kategori payları, birim maliyet)
- Vergi ayrıştırma (pro-rata allocation)
- Birim maliyet (TL/GB, TL/dk, TL/SMS, TL/GB roaming)

Giriş şeması: (paylaştığın payload)
{
  "summary": {
    "period": "YYYY-MM",
    "total": float,
    "taxes": float,
    "baseline_total_mean": float,   # önceki 3 ay ort.
    "total_delta": float,           # bu ay - ortalama
    "usage_summary": {"gb":float,"minutes":float,"sms":float,"roaming_gb":float}
  },
  "breakdown": [
    {"category":"Data","total":float,"lines":[{"text":str,"amount":float}]},
    ...
  ],
  "contributors": [
    {"category":str,"current":float,"baseline_mean":float,"delta":float}, ...
  ]
}
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

# --- Eşikler (ayarlar) ---
TOTAL_DELTA_HIGH_PCT = 0.15     # toplam, ortalamaya göre %15'ten fazla arttıysa "yüksek"
CONTRIB_DELTA_HIGH_TL = 30.0    # bir kategori delta > 30 TL ise işaretle
CATEGORY_SHARE_LIMITS = {       # kategori payı toplamın üstünde ise (oran)
    "Roaming": 0.05,            # %5+
    "Premium": 0.02,
    "VAS": 0.03,
}
MIN_TOTAL_FOR_SHARE = 100.0     # pay eşiği yorumlamak için minimum fatura toplamı
UNIT_COST_LIMITS = {            # birim maliyetler için "yüksek" sınırlar (örnek)
    "data_tl_per_gb": 25.0,     # TL/GB
    "voice_tl_per_min": 0.8,    # TL/dk
    "sms_tl_per_sms": 1.0,      # TL/SMS
    "roaming_tl_per_gb": 100.0, # TL/GB Roaming
}

def _get(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

# ---------------------------
# Vergi ayrıştırma (pro-rata)
# ---------------------------
def alloc_taxes(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Vergileri 'Vergiler' kategorisini hariç tutup diğer kategorilere oransal dağıtır."""
    summary = payload.get("summary", {}) or {}
    taxes_total = float(summary.get("taxes") or 0.0)
    breakdown = payload.get("breakdown", []) or []

    # Vergi kategorisini (örn. "Vergiler") bazdan düş
    base = [c for c in breakdown if not str(c.get("category","")).lower().startswith("verg")]
    base_total = sum(float(c.get("total") or 0.0) for c in base)

    # dağıtım
    out = []
    for c in base:
        gross = float(c.get("total") or 0.0)
        part = (gross / base_total) if base_total else 0.0
        alloc_tax = taxes_total * part
        net = max(gross - alloc_tax, 0.0)
        eff = (alloc_tax / net) if net else 0.0
        out.append({
            "category": c.get("category"),
            "gross": round(gross, 2),
            "allocated_tax": round(alloc_tax, 2),
            "net": round(net, 2),
            "effective_tax_rate": round(eff, 4),
        })

    return {
        "taxes_total": round(taxes_total, 2),
        "by_category": out,
        "gross_total_ex_taxcat": round(base_total, 2),
    }

# ---------------------------
# Birim maliyet hesapları
# ---------------------------
def unit_costs(vergi_alloc: Dict[str, Any], usage: Dict[str, Any]) -> Dict[str, Optional[float]]:
    cats = {x["category"]: x for x in vergi_alloc.get("by_category", [])}
    def net(cat): return float(cats.get(cat, {}).get("net", 0.0))

    gb   = float(usage.get("gb") or 0.0)
    minutes = float(usage.get("minutes") or 0.0)
    sms  = float(usage.get("sms") or 0.0)
    rgb  = float(usage.get("roaming_gb") or 0.0)

    return {
        "data_tl_per_gb":    round(net("Data")    / gb, 2) if gb else None,
        "voice_tl_per_min":  round(net("Voice")   / minutes, 3) if minutes else None,
        "sms_tl_per_sms":    round(net("SMS")     / sms, 2) if sms else None,
        "roaming_tl_per_gb": round(net("Roaming") / rgb, 2) if rgb else None,
    }

# ---------------------------
# Anomali kuralları (LLM yok)
# ---------------------------
def detect_anomalies(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = payload.get("summary", {}) or {}
    contributors = payload.get("contributors", []) or []
    breakdown = payload.get("breakdown", []) or []

    total = float(summary.get("total") or 0.0)
    baseline = float(summary.get("baseline_total_mean") or 0.0)
    delta = float(summary.get("total_delta") or (total - baseline))

    flags: List[Dict[str, Any]] = []

    # 1) Toplam spike (baseline'a göre)
    pct = (delta / baseline) if baseline else None
    if pct is not None and abs(pct) >= TOTAL_DELTA_HIGH_PCT:
        flags.append({
            "type": "total_spike",
            "severity": "high" if abs(pct) >= (TOTAL_DELTA_HIGH_PCT * 1.5) else "medium",
            "message": f"Toplam faturada {'artış' if delta>0 else 'azalış'}: {delta:+.0f} TL (%{pct*100:.1f}).",
            "metrics": {"total": total, "baseline_mean": baseline, "delta": delta, "pct": round(pct*100,1)},
        })

    # 2) Katkı yapan kategoriler (delta eşiği)
    for c in sorted(contributors, key=lambda x: float(x.get("delta") or 0.0), reverse=True):
        dlt = float(c.get("delta") or 0.0)
        if abs(dlt) >= CONTRIB_DELTA_HIGH_TL:
            flags.append({
                "type": "category_delta",
                "severity": "high" if abs(dlt) >= CONTRIB_DELTA_HIGH_TL*1.5 else "medium",
                "category": c.get("category"),
                "message": f"{c.get('category')} kaleminde {dlt:+.0f} TL değişim.",
                "metrics": {"current": c.get("current"), "baseline_mean": c.get("baseline_mean"), "delta": dlt},
            })

    # 3) Kategori payları (toplam içindeki oran)
    if total >= MIN_TOTAL_FOR_SHARE:
        cat_map = {c["category"]: float(c.get("total") or 0.0) for c in breakdown}
        for cat, limit in CATEGORY_SHARE_LIMITS.items():
            if cat in cat_map:
                share = cat_map[cat] / total
                if share >= limit:
                    flags.append({
                        "type": "category_share",
                        "severity": "medium" if share < limit*1.5 else "high",
                        "category": cat,
                        "message": f"{cat} payı %{share*100:.1f} (eşik %{limit*100:.0f}).",
                        "metrics": {"share_pct": round(share*100,1), "limit_pct": limit*100, "amount": cat_map[cat]},
                    })

    # 4) Birim maliyet anomali (vergiler netleştirildikten sonra karşılaştırılır)
    vergi = alloc_taxes(payload)
    usage = summary.get("usage_summary", {}) or {}
    uc = unit_costs(vergi, usage)
    for key, val in uc.items():
        if val is None: 
            continue
        lim = UNIT_COST_LIMITS.get(key)
        if lim and val >= lim:
            flags.append({
                "type": "unit_cost",
                "severity": "medium" if val < lim*1.5 else "high",
                "metric": key,
                "message": f"{key} beklenenin üzerinde: {val} (eşik {lim}).",
                "metrics": {"value": val, "limit": lim},
            })

    return {
        "flags": flags,
        "vergi_alloc": vergi,
        "unit_costs": uc,
    }

# ---------------------------
# Dışa açık tek API
# ---------------------------
def analyze_bill(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Toplam rapor: anomali bayrakları + vergi ayrıştırma + birim maliyet."""
    out = detect_anomalies(payload)
    # İstersen burada 'autofix' veya 'what-if' senaryolarını deterministik ekleyebilirsin.
    return out
