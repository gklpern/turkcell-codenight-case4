# -*- coding: utf-8 -*-
"""
Data Prep — Bill Summary & Segment Stats

Amaç:
1) Tüm CSV'leri (data klasöründen) okuyup veri tiplerini standardize etmek
2) Fatura-odaklı özet tablo üretmek: bill_summary_df (kategori bazında toplamlar + header + user)
3) Segment bazlı istatistikler üretmek: segment_stats_df (youth/retail/corporate/tourist)
4) CSV olarak çıktı vermek (./artifacts klasörüne):
   - bill_summary.csv
   - segment_stats.csv

Çalıştırma:
    python data_prep.py --data data --out artifacts
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


CATS = [
    "data","voice","sms","roaming","premium_sms","vas","one_off","discount","tax","one_off","discount"
]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data", help="Girdi klasörü (CSV'ler)")
    ap.add_argument("--out", default="artifacts", help="Çıktı klasörü")
    return ap.parse_args()


def read_csvs(root: Path) -> Dict[str, pd.DataFrame]:
    def rd(name):
        p = root / f"{name}.csv"
        if not p.exists():
            raise FileNotFoundError(f"Eksik: {p}")
        return pd.read_csv(p)
    dfs = {
        "users": rd("users"),
        "plans": rd("plans"),
        "bill_headers": rd("bill_headers"),
        "bill_items": rd("bill_items"),
        "usage_daily": rd("usage_daily"),
    }
    # opsiyonel kataloglar (varsa oku)
    for opt in ["vas_catalog","premium_sms_catalog","add_on_packs"]:
        p = root / f"{opt}.csv"
        if p.exists():
            dfs[opt] = pd.read_csv(p)
    return dfs


def standardize_types(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    # Tarih kolonlarını to_datetime
    date_cols = {
        "bill_headers": ["period_start","period_end","issue_date"],
        "bill_items": ["created_at"],
        "usage_daily": ["date"],
    }
    for k, cols in date_cols.items():
        if k in dfs:
            for c in cols:
                if c in dfs[k].columns:
                    dfs[k][c] = pd.to_datetime(dfs[k][c], errors="coerce")
    # Sayısallar
    if "bill_items" in dfs:
        for c in ["amount","unit_price","quantity","tax_rate"]:
            if c in dfs["bill_items"].columns:
                dfs["bill_items"][c] = pd.to_numeric(dfs["bill_items"][c], errors="coerce")
        if "category" in dfs["bill_items"].columns:
            dfs["bill_items"]["category"] = dfs["bill_items"]["category"].str.lower().fillna("unknown")
    if "usage_daily" in dfs:
        for c in ["mb_used","minutes_used","sms_used","roaming_mb"]:
            if c in dfs["usage_daily"].columns:
                dfs["usage_daily"][c] = pd.to_numeric(dfs["usage_daily"][c], errors="coerce").fillna(0)
    return dfs


def build_bill_summary(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    bh = dfs["bill_headers"].copy()
    bi = dfs["bill_items"].copy()
    users = dfs["users"].copy()

    # Kategori pivotu (bill_id x category)
    pivot = (
        bi.groupby(["bill_id","category"], dropna=False)["amount"].sum()
          .unstack(fill_value=0)
    )
    # Varsayılan kategorileri eksikse ekle
    for c in CATS:
        if c not in pivot.columns:
            pivot[c] = 0.0
    pivot = pivot.reset_index()

    # Header + User join
    df = pivot.merge(bh, on="bill_id", how="left")
    df = df.merge(users[["user_id","name","type","current_plan_id"]], on="user_id", how="left")

    # Türetilmiş sütunlar
    df["period"] = df["period_start"].dt.strftime("%Y-%m")
    df["total_without_tax"] = df[[c for c in pivot.columns if c not in ("bill_id",)]].sum(axis=1) - df.get("tax", 0.0)

    # Tutarlılık kontrolü (opsiyonel)
    if "total_amount" in df.columns:
        df["diff_total_vs_items"] = (df["total_amount"] - df[[c for c in pivot.columns if c not in ("bill_id",)]].sum(axis=1)).round(2)

    # Sıralama
    sort_cols = ["period_start","user_id","bill_id"]
    df = df.sort_values(sort_cols).reset_index(drop=True)
    return df


def build_segment_stats(dfs: Dict[str, pd.DataFrame], bill_summary: pd.DataFrame) -> pd.DataFrame:
    # Kullanım bazlı özet (aylık; user x month)
    ud = dfs["usage_daily"].copy()
    ud["period"] = ud["date"].dt.strftime("%Y-%m")
    use_m = (
        ud.groupby(["user_id","period"]).agg(
            used_gb=("mb_used", lambda s: float(s.sum())/1024.0),
            used_min=("minutes_used", "sum"),
            used_sms=("sms_used", "sum"),
            roaming_gb=("roaming_mb", lambda s: float(s.sum())/1024.0),
        ).reset_index()
    )

    # User tiplerini bağla
    users = dfs["users"][ ["user_id","type"] ].copy()
    use_m = use_m.merge(users, on="user_id", how="left")

    # Segment istatistikleri (aylık ortalamalar)
    seg = (
        use_m.groupby("type").agg(
            mean_gb=("used_gb","mean"), std_gb=("used_gb","std"),
            mean_min=("used_min","mean"), std_min=("used_min","std"),
            mean_sms=("used_sms","mean"), std_sms=("used_sms","std"),
            mean_roam_gb=("roaming_gb","mean"), std_roam_gb=("roaming_gb","std"),
            n_users=("user_id","nunique"), n_user_months=("period","count")
        ).reset_index()
    )

    # Harcama tarafı: kategori toplamları segment bazında
    spend_cols = [c for c in bill_summary.columns if c in CATS]
    spend = (
        bill_summary.groupby("type")[spend_cols + ["total_amount"]]
            .mean(numeric_only=True)
            .reset_index()
            .rename(columns={"total_amount":"avg_bill_total"})
    )

    seg_stats = seg.merge(spend, on="type", how="left")
    return seg_stats


def main():
    args = parse_args()
    root = Path(args.data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    dfs = read_csvs(root)
    dfs = standardize_types(dfs)

    bill_summary = build_bill_summary(dfs)
    seg_stats = build_segment_stats(dfs, bill_summary)

    bill_summary.to_csv(out/"bill_summary.csv", index=False)
    seg_stats.to_csv(out/"segment_stats.csv", index=False)

    print("✓ Hazır: bill_summary.csv ve segment_stats.csv →", out.resolve())


if __name__ == "__main__":
    main()
