# -*- coding: utf-8 -*-
"""
cohort_analysis.py — Kohort kıyası analizi
"""

from typing import Dict, Any

def analyze_cohort_comparison(payload: Dict[str, Any], cohort_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    2. Kohort kıyası: benzer kullanıcıların ortalamasına göre fark
    
    Args:
        payload: Fatura verisi
        cohort_data: Benzer kullanıcıların verisi
            {
                "cohort_type": "retail|youth|corporate",
                "avg_total": 180.25,
                "avg_data_gb": 12.5,
                "avg_minutes": 450,
                "avg_sms": 25,
                "percentile_25": 150.0,
                "percentile_75": 220.0
            }
    """
    summary = payload.get("summary", {})
    usage = summary.get("usage_summary", {})
    
    user_total = summary.get("total", 0)
    cohort_avg = cohort_data.get("avg_total", 0)
    cohort_diff = user_total - cohort_avg
    cohort_percentile = cohort_data.get("percentile_75", 0)
    
    # Kohort analizi
    analysis = {
        "cohort_type": cohort_data.get("cohort_type", "genel"),
        "user_total": user_total,
        "cohort_average": cohort_avg,
        "difference": cohort_diff,
        "difference_percent": round((cohort_diff / cohort_avg * 100), 1) if cohort_avg > 0 else 0,
        "percentile": "yüksek" if user_total > cohort_percentile else "normal" if user_total > cohort_data.get("percentile_25", 0) else "düşük",
        "usage_comparison": {
            "data_gb": {
                "user": usage.get("gb", 0),
                "cohort_avg": cohort_data.get("avg_data_gb", 0),
                "difference": usage.get("gb", 0) - cohort_data.get("avg_data_gb", 0)
            },
            "minutes": {
                "user": usage.get("minutes", 0),
                "cohort_avg": cohort_data.get("avg_minutes", 0),
                "difference": usage.get("minutes", 0) - cohort_data.get("avg_minutes", 0)
            },
            "sms": {
                "user": usage.get("sms", 0),
                "cohort_avg": cohort_data.get("avg_sms", 0),
                "difference": usage.get("sms", 0) - cohort_data.get("avg_sms", 0)
            }
        }
    }
    
    return analysis

