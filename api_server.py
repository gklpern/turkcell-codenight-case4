# -*- coding: utf-8 -*-
"""
Turkcell Fatura Asistanı API Server
FastAPI tabanlı REST API - Frontend için backend servisi
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import json

# Import our engines
from general_scripts.data_prep import read_csvs, standardize_types
from general_scripts.anomaly_engine import load_artifacts, detect_anomalies_for
from general_scripts.whatif_engine import load_all, scenario_cost, enumerate_top3
from general_scripts.llm_client import render_bill_summary_llm
from general_scripts.rules_engine import analyze_bill, alloc_taxes, unit_costs
from general_scripts.cohort_analysis import analyze_cohort_comparison
from general_scripts.autofix_engine import generate_autofix_recommendation

app = FastAPI(
    title="Turkcell Fatura Asistanı API",
    description="Fatura açıklama, anomali tespiti ve what-if simülasyonu",
    version="1.0.0"
)

# CORS ayarları - frontend'in farklı porttan erişebilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domain'ler belirtin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data cache
DATA_CACHE = {}
ARTIFACTS_CACHE = {}

# Pydantic models
class ExplainRequest(BaseModel):
    bill_id: int

class AnomalyRequest(BaseModel):
    user_id: int
    period: str

class WhatIfRequest(BaseModel):
    user_id: int
    period: str
    scenario: Dict[str, Any]

class CheckoutRequest(BaseModel):
    user_id: int
    actions: List[Dict[str, Any]]

class CohortRequest(BaseModel):
    user_id: int
    period: str
    cohort_data: Dict[str, Any]

class TaxAnalysisRequest(BaseModel):
    user_id: int
    period: str

class AutofixRequest(BaseModel):
    user_id: int
    period: str

# Startup event - data loading
@app.on_event("startup")
async def startup_event():
    """Uygulama başladığında verileri yükle"""
    global DATA_CACHE, ARTIFACTS_CACHE
    
    data_dir = Path("data")
    artifacts_dir = Path("artifacts")
    
    if data_dir.exists():
        print("Loading data...")
        dfs = read_csvs(data_dir)
        dfs = standardize_types(dfs)
        DATA_CACHE = load_all(data_dir)
        print(f"Loaded {len(DATA_CACHE)} dataframes")
    
    if artifacts_dir.exists():
        print("Loading artifacts...")
        try:
            bill_summary, cat_breakdown = load_artifacts(artifacts_dir)
            ARTIFACTS_CACHE = {
                "bill_summary": bill_summary,
                "category_breakdown": cat_breakdown
            }
            print("Artifacts loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load artifacts: {e}")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "data_loaded": len(DATA_CACHE) > 0}

# User endpoints
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Kullanıcı bilgilerini getir"""
    if not DATA_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    users = DATA_CACHE["users"]
    user = users[users["user_id"] == user_id]
    
    if user.empty:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user.iloc[0].to_dict()
    
    # Plan bilgilerini de ekle
    plans = DATA_CACHE["plans"]
    plan = plans[plans["plan_id"] == user_data["current_plan_id"]]
    if not plan.empty:
        user_data["current_plan"] = plan.iloc[0].to_dict()
    
    return user_data

@app.get("/api/users")
async def list_users():
    """Tüm kullanıcıları listele"""
    if not DATA_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    users = DATA_CACHE["users"]
    return users.to_dict("records")

# Bill endpoints
@app.get("/api/bills/{user_id}")
async def get_user_bills(user_id: int, period: Optional[str] = Query(None)):
    """Kullanıcının faturalarını getir"""
    if not DATA_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    bh = DATA_CACHE["bill_headers"]
    bi = DATA_CACHE["bill_items"]
    
    user_bills = bh[bh["user_id"] == user_id].copy()
    
    if period:
        user_bills = user_bills[user_bills["period"] == period]
    
    if user_bills.empty:
        raise HTTPException(status_code=404, detail="No bills found")
    
    # Her fatura için items'ları da ekle
    result = []
    for _, bill in user_bills.iterrows():
        bill_data = bill.to_dict()
        bill_items = bi[bi["bill_id"] == bill["bill_id"]].to_dict("records")
        bill_data["items"] = bill_items
        result.append(bill_data)
    
    return result if len(result) > 1 else result[0]

# Catalog endpoints
@app.get("/api/catalog")
async def get_catalog():
    """Tüm katalog verilerini getir"""
    if not DATA_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    catalog = {}
    
    # Plans
    if "plans" in DATA_CACHE:
        catalog["plans"] = DATA_CACHE["plans"].to_dict("records")
    
    # Add-ons
    if "add_on_packs" in DATA_CACHE:
        catalog["addons"] = DATA_CACHE["add_on_packs"].to_dict("records")
    
    # VAS catalog
    if "vas_catalog" in DATA_CACHE:
        catalog["vas"] = DATA_CACHE["vas_catalog"].to_dict("records")
    
    # Premium SMS catalog
    if "premium_sms_catalog" in DATA_CACHE:
        catalog["premium_sms"] = DATA_CACHE["premium_sms_catalog"].to_dict("records")
    
    return catalog

# Explain endpoint
@app.post("/api/explain")
async def explain_bill(request: ExplainRequest):
    """Faturayı açıkla"""
    if not DATA_CACHE or not ARTIFACTS_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    bill_id = request.bill_id
    
    # Bill header'ı bul
    bh = DATA_CACHE["bill_headers"]
    bill = bh[bh["bill_id"] == bill_id]
    if bill.empty:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    bill_data = bill.iloc[0]
    user_id = bill_data["user_id"]
    period = bill_data["period"]
    
    # Bill items'ları kategorilere göre grupla
    bi = DATA_CACHE["bill_items"]
    items = bi[bi["bill_id"] == bill_id]
    
    # Kategori bazında toplamlar
    breakdown = []
    for category in items["category"].unique():
        cat_items = items[items["category"] == category]
        total = cat_items["amount"].sum()
        
        # Her kalem için açıklama
        lines = []
        for _, item in cat_items.iterrows():
            line = {
                "text": f"{item['description']} - {item['quantity']}x{item['unit_price']} TL",
                "amount": float(item["amount"])
            }
            lines.append(line)
        
        breakdown.append({
            "category": category,
            "total": float(total),
            "lines": lines
        })
    
    # Kullanım özeti
    usage = DATA_CACHE["usage_daily"]
    bill_start = bill_data["period_start"]
    bill_end = bill_data["period_end"]
    
    period_usage = usage[
        (usage["user_id"] == user_id) & 
        (usage["date"] >= bill_start) & 
        (usage["date"] <= bill_end)
    ]
    
    usage_summary = {
        "gb": float(period_usage["mb_used"].sum()) / 1024.0,
        "minutes": float(period_usage["minutes_used"].sum()),
        "sms": int(period_usage["sms_used"].sum()),
        "roaming_gb": float(period_usage["roaming_mb"].sum()) / 1024.0
    }
    
    # Özet
    summary = {
        "period": period,
        "total": float(bill_data["total_amount"]),
        "taxes": float(items[items["category"] == "tax"]["amount"].sum()),
        "usage_summary": usage_summary,
        "baseline_total_mean": 0.0,  # TODO: geçmiş ortalaması hesapla
        "total_delta": 0.0
    }
    
    # LLM özeti
    payload = {
        "summary": summary,
        "breakdown": breakdown,
        "contributors": []  # TODO: katkıda bulunanları hesapla
    }
    
    try:
        llm_summary = render_bill_summary_llm(payload)
    except Exception as e:
        llm_summary = f"Fatura özeti: {summary['total']} TL toplam tutar."
    
    return {
        "summary": summary,
        "breakdown": breakdown,
        "llm_summary": llm_summary
    }

# Anomaly endpoint
@app.post("/api/anomalies")
async def detect_anomalies(request: AnomalyRequest):
    """Anomalileri tespit et"""
    if not ARTIFACTS_CACHE:
        raise HTTPException(status_code=503, detail="Artifacts not loaded")
    
    user_id = request.user_id
    period = request.period
    
    try:
        result = detect_anomalies_for(
            ARTIFACTS_CACHE["bill_summary"],
            ARTIFACTS_CACHE["category_breakdown"],
            user_id,
            period
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# What-if endpoint
@app.post("/api/whatif")
async def what_if_simulation(request: WhatIfRequest):
    """What-if simülasyonu"""
    if not DATA_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    user_id = request.user_id
    period = request.period
    scenario = request.scenario
    
    try:
        # Tek senaryo hesapla
        plan_id = scenario.get("plan_id")
        addons = scenario.get("addons", [])
        disable_vas = scenario.get("disable_vas", False)
        block_premium_sms = scenario.get("block_premium_sms", False)
        
        result = scenario_cost(
            user_id, period, DATA_CACHE,
            plan_id=plan_id,
            addons=addons,
            disable_vas=disable_vas,
            block_premium_sms=block_premium_sms
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Top 3 scenarios endpoint
@app.get("/api/whatif/top3/{user_id}")
async def get_top3_scenarios(user_id: int, period: str):
    """En iyi 3 senaryoyu getir"""
    if not DATA_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        scenarios = enumerate_top3(user_id, period, DATA_CACHE)
        return {"scenarios": scenarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Checkout endpoint (mock)
@app.post("/api/checkout")
async def checkout(request: CheckoutRequest):
    """Mock checkout - gerçek uygulamada entegrasyon yapılacak"""
    user_id = request.user_id
    actions = request.actions
    
    # Mock order ID
    import uuid
    order_id = f"MOCK-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "status": "ok",
        "order_id": order_id,
        "user_id": user_id,
        "actions": actions,
        "message": "Mock işlem başarılı - gerçek entegrasyon için hazır"
    }

# Cohort comparison endpoint
@app.post("/api/cohort")
async def cohort_comparison(request: CohortRequest):
    """Kohort kıyası: benzer kullanıcıların ortalamasına göre fark"""
    if not ARTIFACTS_CACHE:
        raise HTTPException(status_code=503, detail="Artifacts not loaded")
    
    user_id = request.user_id
    period = request.period
    cohort_data = request.cohort_data
    
    try:
        # Kullanıcının fatura verilerini al
        bill_summary = ARTIFACTS_CACHE["bill_summary"]
        user_bills = bill_summary[bill_summary["user_id"] == user_id]
        
        if user_bills.empty:
            raise HTTPException(status_code=404, detail="User bill not found")
        
        # Fatura verilerini hazırla
        bill_data = user_bills[user_bills["period"] == period]
        if bill_data.empty:
            raise HTTPException(status_code=404, detail="Bill for period not found")
        
        # Payload formatına çevir
        payload = {
            "summary": {
                "total": float(bill_data["total_amount"].iloc[0]),
                "usage_summary": {
                    "gb": float(bill_data["data"].iloc[0]),
                    "minutes": float(bill_data["voice"].iloc[0]),
                    "sms": float(bill_data["sms"].iloc[0])
                }
            }
        }
        
        # Kohort analizi yap
        result = analyze_cohort_comparison(payload, cohort_data)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Tax analysis endpoint
@app.post("/api/tax-analysis")
async def tax_analysis(request: TaxAnalysisRequest):
    """Vergi ayrıştırma ve birim maliyet analizi"""
    if not ARTIFACTS_CACHE:
        raise HTTPException(status_code=503, detail="Artifacts not loaded")
    
    user_id = request.user_id
    period = request.period
    
    try:
        # Kullanıcının fatura verilerini al
        bill_summary = ARTIFACTS_CACHE["bill_summary"]
        cat_breakdown = ARTIFACTS_CACHE["category_breakdown"]
        
        user_bills = bill_summary[bill_summary["user_id"] == user_id]
        if user_bills.empty:
            raise HTTPException(status_code=404, detail="User bill not found")
        
        bill_data = user_bills[user_bills["period"] == period]
        if bill_data.empty:
            raise HTTPException(status_code=404, detail="Bill for period not found")
        
        # Kategori breakdown'ını al
        bill_id = bill_data["bill_id"].iloc[0]
        categories = cat_breakdown[cat_breakdown["bill_id"] == bill_id]
        
        # Payload formatına çevir
        payload = {
            "summary": {
                "total": float(bill_data["total_amount"].iloc[0]),
                "taxes": float(bill_data["tax"].iloc[0]),
                "usage_summary": {
                    "gb": float(bill_data["data"].iloc[0]),
                    "minutes": float(bill_data["voice"].iloc[0]),
                    "sms": float(bill_data["sms"].iloc[0])
                }
            },
            "breakdown": []
        }
        
        # Kategori breakdown'ını ekle
        for _, cat in categories.iterrows():
            payload["breakdown"].append({
                "category": cat["category"],
                "total": float(cat["total_amount"])
            })
        
        # Rules engine ile analiz yap
        result = analyze_bill(payload)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Autofix recommendation endpoint
@app.post("/api/autofix")
async def autofix_recommendation(request: AutofixRequest):
    """Otomatik "autofix" önerisi: tek tıkla en iyi senaryo + gerekçe"""
    if not DATA_CACHE or not ARTIFACTS_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    user_id = request.user_id
    period = request.period
    
    try:
        # Önce what-if senaryolarını al
        scenarios = enumerate_top3(user_id, period, DATA_CACHE)
        
        if not scenarios:
            raise HTTPException(status_code=404, detail="No scenarios found")
        
        # Kullanıcının mevcut fatura verilerini al
        bill_summary = ARTIFACTS_CACHE["bill_summary"]
        user_bills = bill_summary[bill_summary["user_id"] == user_id]
        
        if user_bills.empty:
            raise HTTPException(status_code=404, detail="User bill not found")
        
        bill_data = user_bills[user_bills["period"] == period]
        if bill_data.empty:
            raise HTTPException(status_code=404, detail="Bill for period not found")
        
        # Payload formatına çevir
        payload = {
            "summary": {
                "total": float(bill_data["total_amount"].iloc[0])
            }
        }
        
        # Autofix önerisi oluştur
        result = generate_autofix_recommendation(payload, scenarios)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 