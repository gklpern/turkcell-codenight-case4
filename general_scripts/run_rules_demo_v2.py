# -*- coding: utf-8 -*-
"""
Robust demo: rules_engine'i gerçek bir user_id ile çalıştırır.
- category_breakdown.csv uygun değilse, data/bill_items.csv + data/bill_headers.csv'den üretir.
Kullanım:
  python general_scripts/run_rules_demo_v2.py --user_id 1003 --period 2025-07
  # period vermezsen, bill_summary'daki son ay alınır.
"""
from __future__ import annotations
import json, argparse, re
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"data"
ART  = ROOT/"artifacts"

def _read_csv(p: Path, **kw) -> pd.DataFrame:
    if not p.exists():
        raise FileNotFoundError(f"CSV yok: {p}")
    return pd.read_csv(p, **kw)

def _ensure_month(s: str) -> str:
    return str(s)[:7]

def month_bounds(period: str):
    y, m = map(int, period.split("-"))
    start = pd.Timestamp(year=y, month=m, day=1)
    end = (start + pd.offsets.MonthBegin(1))
    return start, end

def load_sources():
    bs = _read_csv(ART/"bill_summary.csv")
    cb = pd.read_csv(ART/"category_breakdown.csv") if (ART/"category_breakdown.csv").exists() else None
    usage = pd.read_csv(DATA/"usage_daily.csv", parse_dates=["date"]) if (DATA/"usage_daily.csv").exists() else None
    bills = pd.read_csv(DATA/"bill_headers.csv", parse_dates=["bill_date"])
    items = pd.read_csv(DATA/"bill_items.csv") if (DATA/"bill_items.csv").exists() else None
    return bs, cb, usage, bills, items

def pick_latest_period(bs: pd.DataFrame, user_id: int) -> str:
    df = bs[bs["user_id"]==user_id].copy()
    if df.empty:
        raise ValueError(f"user_id {user_id} için bill_summary kaydı yok.")
    df["period"] = df["period"].astype(str).str[:7]
    return df.sort_values("period")["period"].iloc[-1]

def _norm_col(df: pd.DataFrame, *names, default=None):
    for n in names:
        if n in df.columns: return df[n]
    if default is None:
        raise KeyError(f"Beklenen kolonlar yok: {names}")
    return pd.Series(default, index=df.index)

def _map_category_like(s: str, desc: str="") -> str:
    v = (s or "").upper()
    d = (desc or "").upper()
    if "ROAM" in v or "ROAM" in d: return "Roaming"
    if "PREMIUM" in v or "PREMIUM" in d: return "Premium"
    if "VAS" in v: return "VAS"
    if "VOICE" in v or "KONUŞ" in d: return "Voice"
    if "SMS" in v and "PREMIUM" not in v: return "SMS"
    if "DATA" in v or "INTERNET" in d or "GB" in d: return "Data"
    if "TAX" in v or "VERG" in v or "KDV" in d or "ÖİV" in d: return "Vergiler"
    return "Other"

def ensure_category_breakdown(user_id: int, period: str, bs: pd.DataFrame, cb: Optional[pd.DataFrame],
                              bills: pd.DataFrame, items: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Döndürdüğü df kolonları: user_id, period, category, total"""
    # 1) artifacts/category_breakdown.csv uygunsa onu kullan
    if cb is not None:
        cols = set(c.lower() for c in cb.columns)
        need = {"user_id","period","category","total"}
        if need.issubset(cols):
            tmp = cb.copy()
            tmp.columns = [c.lower() for c in tmp.columns]
            tmp["period"] = tmp["period"].astype(str).str[:7]
            ok = tmp[(tmp["user_id"]==user_id) & (tmp["period"]==period)]
            if not ok.empty:
                return ok[["user_id","period","category","total"]]

    # 2) Fallback: bill_items + bill_headers'tan üret
    if items is None:
        raise ValueError("category_breakdown yok ve data/bill_items.csv bulunamadı (fallback yapılamıyor).")

    bills2 = bills.copy()
    bills2["period"] = bills2["bill_date"].dt.strftime("%Y-%m")
    cur_bills = bills2[(bills2["user_id"]==user_id) & (bills2["period"]==period)][["bill_id","user_id","period","bill_date"]]
    if cur_bills.empty:
        raise ValueError("Bu user+period için bill_headers kaydı yok.")

    df = items.merge(cur_bills, on="bill_id", how="inner")
    # kolon varyantlarını normalize et
    cat_raw = _norm_col(df, "category", "item_type", "type", default="OTHER").astype(str)
    desc = _norm_col(df, "description", "text", default="").astype(str)
    amt  = _norm_col(df, "total", "amount", "price").astype(float)

    df["category"] = [ _map_category_like(c, d) for c,d in zip(cat_raw, desc) ]
    df["total"] = amt

    out = (df.groupby(["user_id","period","category"], as_index=False)["total"].sum())
    return out

def build_payload_for(user_id: int, period: Optional[str]) -> Dict[str, Any]:
    bs, cb, usage, bills, items = load_sources()
    period = _ensure_month(period or pick_latest_period(bs, user_id))

    # --- SUMMARY ---
    srow = bs.copy()
    srow["period"] = srow["period"].astype(str).str[:7]
    srow = srow[(srow["user_id"]==user_id) & (srow["period"]==period)]
    if srow.empty:
        raise ValueError(f"bill_summary: user_id={user_id}, period={period} yok.")
    total = float(srow["total"].iloc[0]) if "total" in srow.columns else float(srow["total_amount"].iloc[0])
    taxes = float(srow["taxes"].iloc[0]) if "taxes" in srow.columns else 0.0

    # usage_summary: varsa bs’den al; yoksa usage_daily’den topla
    if {"gb","minutes","sms","roaming_gb"}.issubset(srow.columns):
        usage_summary = {
            "gb": float(srow["gb"].iloc[0]),
            "minutes": float(srow["minutes"].iloc[0]),
            "sms": float(srow["sms"].iloc[0]),
            "roaming_gb": float(srow["roaming_gb"].iloc[0]),
        }
    else:
        if usage is None:
            usage_summary = {"gb": None, "minutes": None, "sms": None, "roaming_gb": None}
        else:
            start, end = month_bounds(period)
            u = usage[(usage["user_id"]==user_id) & (usage["date"]>=start) & (usage["date"]<end)]
            usage_summary = {
                "gb": float(u.get("data_mb", pd.Series([0])).sum() / 1024.0) if "data_mb" in u else None,
                "minutes": float(u.get("voice_min", pd.Series([0])).sum()) if "voice_min" in u else None,
                "sms": float(u.get("sms_count", pd.Series([0])).sum()) if "sms_count" in u else None,
                "roaming_gb": float(u.get("roaming_mb", pd.Series([0])).sum() / 1024.0) if "roaming_mb" in u else None,
            }

    # baseline (önceki 3 ay ort.)
    btmp = bs.copy()
    btmp["period"] = btmp["period"].astype(str).str[:7]
    cur_start, _ = month_bounds(period)
    prev3 = btmp[(btmp["user_id"]==user_id) & (pd.to_datetime(btmp["period"]+"-01") < cur_start)] \
            .sort_values("period").tail(3)
    baseline_total_mean = float(prev3["total"].mean()) if "total" in prev3.columns else float(prev3["total_amount"].mean())
    total_delta = float(total - baseline_total_mean) if baseline_total_mean else float("nan")

    # --- BREAKDOWN (robust) ---
    cdf = ensure_category_breakdown(user_id, period, bs, cb, bills, items)
    breakdown = (
        cdf.groupby("category", as_index=False)["total"]
        .sum()
        .assign(lines=lambda d: d.apply(lambda r: [{"text": r["category"], "amount": float(r["total"])}], axis=1))
        .to_dict(orient="records")
    )

    # --- CONTRIBUTORS (kategori delta: bu ay - önceki 3 ay ort.)
    ctmp = cdf.copy()
    ctmp["dt"] = pd.to_datetime(ctmp["period"]+"-01")
    contributors = []
    for cat, cur_amt in cdf.set_index("category")["total"].items():
        prev_cat = ctmp[(ctmp["category"]==cat) & (ctmp["user_id"]==user_id) & (ctmp["dt"]<cur_start)] \
                      .sort_values("period").tail(3)
        baseline_mean = float(prev_cat["total"].mean()) if not prev_cat.empty else 0.0
        contributors.append({
            "category": cat,
            "current": float(cur_amt),
            "baseline_mean": baseline_mean,
            "delta": float(cur_amt - baseline_mean),
        })

    payload = {
        "summary": {
            "period": period,
            "total": total,
            "taxes": taxes,
            "baseline_total_mean": baseline_total_mean,
            "total_delta": total_delta,
            "usage_summary": usage_summary,
        },
        "breakdown": breakdown,
        "contributors": contributors,
    }
    return payload

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user_id", type=int, required=True)
    ap.add_argument("--period", type=str, help="YYYY-MM (opsiyonel)")
    args = ap.parse_args()

    payload = build_payload_for(args.user_id, args.period)

    from rules_engine import analyze_bill
    result = analyze_bill(payload)

    print("=== PAYLOAD (özet) ===")
    preview = {
        "summary": payload["summary"],
        "breakdown": payload["breakdown"],
        "contributors_top": sorted(payload["contributors"], key=lambda x: x["delta"], reverse=True)[:5]
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))

    print("\n=== RULES ENGINE RESULT ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
