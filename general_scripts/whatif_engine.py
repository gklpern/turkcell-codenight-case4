# -*- coding: utf-8 -*-
"""
What-If Engine — Turkcell Fatura Asistanı (MVP)
Klasör yapısı:
  data/
    users.csv, plans.csv, bill_headers.csv, bill_items.csv, usage_daily.csv, add_on_packs.csv
Kullanım (CLI):
  python general_scripts/whatif_engine.py --data data --user_id 1055 --period 2025-08 --plan_id 3 --addons 101 --disable_vas --block_premium_sms
  python general_scripts/whatif_engine.py --data data --user_id 1055 --period 2025-08 --top3
"""
from __future__ import annotations
import argparse
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from pathlib import Path
import json

VAT_RATE = 0.18  # basit KDV

# ----------------- IO -----------------
def load_all(data_dir: Path):
    users = pd.read_csv(data_dir / "users.csv")
    plans = pd.read_csv(data_dir / "plans.csv")
    bill_headers = pd.read_csv(data_dir / "bill_headers.csv")
    bill_items = pd.read_csv(data_dir / "bill_items.csv")
    usage_daily = pd.read_csv(data_dir / "usage_daily.csv")
    add_on_packs = pd.read_csv(data_dir / "add_on_packs.csv")

    # tipler
    bill_headers["period_start"] = pd.to_datetime(bill_headers["period_start"])
    bill_headers["period_end"]   = pd.to_datetime(bill_headers["period_end"])
    bill_headers["issue_date"]   = pd.to_datetime(bill_headers["issue_date"])
    bill_headers["period"]       = pd.to_datetime(bill_headers["period_start"]).dt.to_period("M").astype(str)
    usage_daily["date"]          = pd.to_datetime(usage_daily["date"])

    # kategorileri normalize
    bill_items["category"] = bill_items["category"].astype(str).str.lower().str.strip()

    return {
        "users": users,
        "plans": plans,
        "bill_headers": bill_headers,
        "bill_items": bill_items,
        "usage_daily": usage_daily,
        "add_on_packs": add_on_packs,
    }

# ----------------- çekirdek hesaplar -----------------
def usage_for_period(user_id: int, period: str, db) -> Dict[str, float]:
    bh = db["bill_headers"]; ud = db["usage_daily"]
    rows = bh[(bh["user_id"] == user_id) & (bh["period"] == period)]
    if rows.empty:
        raise ValueError("Fatura bulunamadı (user_id/period).")
    r = rows.iloc[0]
    mask = (ud["user_id"] == user_id) & (ud["date"] >= r["period_start"]) & (ud["date"] <= r["period_end"])
    use = ud[mask]
    return {
        "gb": float(use["mb_used"].sum())/1024.0,
        "min": float(use["minutes_used"].sum()),
        "sms": int(use["sms_used"].sum()),
        "roam_mb": float(use["roaming_mb"].sum()),
        "bill_id": int(r["bill_id"]),
        "current_total": float(r["total_amount"]),
    }

def calc_overages(usage_gb, usage_min, usage_sms, quota_gb, quota_min, quota_sms, over_gb, over_min, over_sms):
    over_data_gb = max(0.0, usage_gb - float(quota_gb))
    over_voice   = max(0.0, usage_min - float(quota_min))
    over_sms     = max(0, int(usage_sms - int(quota_sms)))  
    cost_data = over_data_gb * float(over_gb)
    cost_voice= over_voice   * float(over_min)
    cost_sms  = over_sms     * float(over_sms)
    return over_data_gb, over_voice, over_sms, cost_data, cost_voice, cost_sms

def scenario_cost(user_id: int, period: str, db, plan_id: Optional[int]=None,
                  addons: Optional[List[int]]=None, disable_vas: bool=False, block_premium_sms: bool=False) -> Dict[str, Any]:
    """
    Verilen senaryo için yeni toplamı hesapla.
    """
    addons = addons or []
    users = db["users"]; plans = db["plans"]; bi = db["bill_items"]; bh = db["bill_headers"]; aop = db["add_on_packs"]

    use = usage_for_period(user_id, period, db)
    bill_id = use["bill_id"]
    current_total = use["current_total"]

    cur_user = users[users["user_id"] == user_id].iloc[0]
    cur_plan_id = int(cur_user["current_plan_id"])
    plan_id = plan_id if plan_id is not None else cur_plan_id

    new_plan = plans[plans["plan_id"] == plan_id].iloc[0].to_dict()

    # add-on etkisi
    extra_gb = 0.0; extra_min = 0; extra_sms = 0; addon_cost = 0.0
    if addons:
        sel = aop[aop["addon_id"].isin(addons)]
        if not sel.empty:
            extra_gb = float(sel["extra_gb"].sum())
            extra_min = int(sel["extra_min"].sum())
            extra_sms = int(sel["extra_sms"].sum())
            addon_cost = float(sel["price"].sum())

    # efektif kotalar
    eff_quota_gb  = float(new_plan["quota_gb"]) + extra_gb
    eff_quota_min = float(new_plan["quota_min"]) + extra_min
    eff_quota_sms = float(new_plan["quota_sms"]) + extra_sms

    # aşım
    over_data_gb, over_voice, over_sms, c_data, c_voice, c_sms = calc_overages(
        use["gb"], use["min"], use["sms"],
        eff_quota_gb, eff_quota_min, eff_quota_sms,
        new_plan["overage_gb"], new_plan["overage_min"], new_plan["overage_sms"]
    )

    # mevcut faturadaki kalemlerden alınacak/kapatılacaklar
    items = bi[bi["bill_id"] == bill_id].copy()
    amt_vas    = float(items[items["category"] == "vas"]["amount"].sum())
    amt_prem   = float(items[items["category"] == "premium_sms"]["amount"].sum())
    amt_roam   = float(items[items["category"] == "roaming"]["amount"].sum())
    amt_oneoff = float(items[items["category"] == "one_off"]["amount"].sum())

    keep_vas  = 0.0 if disable_vas else amt_vas
    keep_prem = 0.0 if block_premium_sms else amt_prem

    fixed_fee = float(new_plan["monthly_price"])
    subtotal = fixed_fee + addon_cost + c_data + c_voice + c_sms + keep_vas + keep_prem + amt_roam + amt_oneoff
    tax = subtotal * VAT_RATE
    new_total = subtotal + tax

    details = {
        "fixed_fee": round(fixed_fee,2),
        "addons_cost": round(addon_cost,2),
        "overage_data_gb": round(over_data_gb,2),
        "overage_voice_min": round(over_voice,0),
        "overage_sms": int(over_sms),
        "cost_overage_data": round(c_data,2),
        "cost_overage_voice": round(c_voice,2),
        "cost_overage_sms": round(c_sms,2),
        "kept_vas": round(keep_vas,2),
        "kept_premium_sms": round(keep_prem,2),
        "kept_roaming": round(amt_roam,2),
        "kept_one_off": round(amt_oneoff,2),
        "tax": round(tax,2),
    }

    return {
        "new_total": round(float(new_total), 2),
        "saving": round(float(current_total - new_total), 2),
        "details": details,
        "plan_id": int(plan_id),
        "addons": addons,
        "disable_vas": bool(disable_vas),
        "block_premium_sms": bool(block_premium_sms),
    }

def enumerate_top3(user_id: int, period: str, db) -> List[Dict[str, Any]]:
    """Basit arama uzayı: tüm planlar x {[], ucuz 2 add-on} x {vas on/off} x {premium on/off}"""
    plans = db["plans"]; addons = db["add_on_packs"]
    plan_ids = [int(x) for x in plans["plan_id"].tolist()]
    addon_none = []
    addon_small = addons.sort_values("price").head(2)["addon_id"].tolist()

    results = []
    for pid in plan_ids:
        for ad in [addon_none, addon_small]:
            for disable_vas in [False, True]:
                for block_premium in [False, True]:
                    try:
                        r = scenario_cost(user_id, period, db, plan_id=pid, addons=ad,
                                          disable_vas=disable_vas, block_premium_sms=block_premium)
                        results.append(r)
                    except Exception:
                        pass
    results = sorted(results, key=lambda x: x["new_total"])[:3]
    # saving’leri normalize
    current_total = usage_for_period(user_id, period, db)["current_total"]
    for r in results:
        r["saving"] = round(float(current_total - r["new_total"]), 2)
    return results

# ----------------- CLI -----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--user_id", type=int, required=True)
    ap.add_argument("--period", type=str, required=True)
    ap.add_argument("--plan_id", type=int, default=None)
    ap.add_argument("--addons", type=int, nargs="*", default=[])
    ap.add_argument("--disable_vas", action="store_true")
    ap.add_argument("--block_premium_sms", action="store_true")
    ap.add_argument("--top3", action="store_true")
    args = ap.parse_args()

    db = load_all(Path(args.data))

    if args.top3:
        out = enumerate_top3(args.user_id, args.period, db)
        print(json.dumps({"top3": out}, ensure_ascii=False, indent=2))
    else:
        out = scenario_cost(
            args.user_id, args.period, db,
            plan_id=args.plan_id, addons=args.addons,
            disable_vas=args.disable_vas, block_premium_sms=args.block_premium_sms
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
