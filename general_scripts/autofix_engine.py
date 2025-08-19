# -*- coding: utf-8 -*-
"""
autofix_engine.py — Otomatik "autofix" önerisi motoru
"""

from typing import Dict, Any, List

def generate_autofix_recommendation(payload: Dict[str, Any], whatif_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    4. Otomatik "autofix" önerisi: tek tıkla en iyi senaryo + gerekçe
    
    Args:
        payload: Fatura verisi
        whatif_scenarios: What-if simülasyon sonuçları
    """
    if not whatif_scenarios:
        return {"error": "What-if senaryoları bulunamadı"}
    
    # En iyi senaryoyu bul (en yüksek tasarruf)
    best_scenario = max(whatif_scenarios, key=lambda x: x.get("saving", 0))
    
    # Gerekçe oluştur
    current_total = payload.get("summary", {}).get("total", 0)
    new_total = best_scenario.get("new_total", 0)
    saving = best_scenario.get("saving", 0)
    
    # Basit gerekçe (LLM kullanmadan)
    rationale = f"Bu değişiklikler ile {saving} TL tasarruf sağlayabilirsiniz."
    
    autofix = {
        "current_total": current_total,
        "recommended_total": new_total,
        "potential_saving": saving,
        "saving_percent": round((saving / current_total * 100), 1) if current_total > 0 else 0,
        "recommendation": {
            "plan_id": best_scenario.get("plan_id"),
            "addons": best_scenario.get("addons", []),
            "disable_vas": best_scenario.get("disable_vas", False),
            "block_premium_sms": best_scenario.get("block_premium_sms", False),
            "details": best_scenario.get("details", {})
        },
        "rationale": rationale,
        "one_click_action": {
            "type": "apply_recommendation",
            "payload": {
                "plan_id": best_scenario.get("plan_id"),
                "addons": best_scenario.get("addons", []),
                "disable_vas": best_scenario.get("disable_vas", False),
                "block_premium_sms": best_scenario.get("block_premium_sms", False)
            }
        }
    }
    
    return autofix

