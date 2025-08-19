# -*- coding: utf-8 -*-
"""
tax_analysis.py — Vergi ayrıştırma ve birim maliyet analizi
"""

from typing import Dict, Any

def analyze_tax_breakdown(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    3. Vergi ayrıştırma ve birim maliyet analizi
    
    Args:
        payload: Fatura verisi
    """
    summary = payload.get("summary", {})
    breakdown = payload.get("breakdown", [])
    
    total_amount = summary.get("total", 0)
    total_tax = summary.get("taxes", 0)
    net_amount = total_amount - total_tax
    
    # Vergi analizi
    tax_analysis = {
        "total_amount": total_amount,
        "net_amount": net_amount,
        "total_tax": total_tax,
        "tax_rate": round((total_tax / net_amount * 100), 1) if net_amount > 0 else 0,
        "tax_breakdown": []
    }
    
    # Kategori bazında vergi analizi
    for category in breakdown:
        category_total = category.get("total", 0)
        category_tax = category_total * 0.18  # KDV oranı
        category_net = category_total - category_tax
        
        tax_analysis["tax_breakdown"].append({
            "category": category.get("category", ""),
            "total": category_total,
            "net": category_net,
            "tax": category_tax,
            "tax_rate": 18.0
        })
    
    # Birim maliyet analizi
    usage = summary.get("usage_summary", {})
    unit_costs = {
        "data_cost_per_gb": round(net_amount / usage.get("gb", 1), 2) if usage.get("gb", 0) > 0 else 0,
        "voice_cost_per_minute": round(net_amount / usage.get("minutes", 1), 2) if usage.get("minutes", 0) > 0 else 0,
        "sms_cost_per_message": round(net_amount / usage.get("sms", 1), 2) if usage.get("sms", 0) > 0 else 0
    }
    
    tax_analysis["unit_costs"] = unit_costs
    
    return tax_analysis

