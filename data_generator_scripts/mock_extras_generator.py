# -*- coding: utf-8 -*-
"""
Mock Extras Generator — Discount, One-Off, Segments

Bu betik, mevcut mock CSV'leri (users, plans, bill_headers, bill_items, usage_daily, ...) okur ve
"discount", "one_off" gibi kalemleri ile kullanıcı segmentlerini (youth/retail/corporate/tourist)
GERİYE UYUMLU şekilde ekler.

Kullanım:
  python mock_extras_generator.py --data data --seed 42 \
      --discount_rate 0.10 --discount_min 5 --discount_max 20 \
      --oneoff_rate 0.15 --oneoff_med 100 --oneoff_sigma 0.5 \
      --tourist_rate 0.05

Çıktı: Aynı klasördeki CSV'ler güncellenir (overwrite). İsterseniz --out ile farklı klasöre yazabilirsiniz.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data", help="Girdi veri klasörü (mock generator çıktısı)")
    ap.add_argument("--out", default=None, help="İsteğe bağlı: güncellenmiş CSV'ler için farklı klasör")
    ap.add_argument("--seed", type=int, default=42)
    # Discount
    ap.add_argument("--discount_rate", type=float, default=0.10, help="Kullanıcı oranı")
    ap.add_argument("--discount_min", type=float, default=5.0, help="% minimum")
    ap.add_argument("--discount_max", type=float, default=20.0, help="% maksimum")
    # One-off
    ap.add_argument("--oneoff_rate", type=float, default=0.15, help="Kullanıcı oranı")
    ap.add_argument("--oneoff_med", type=float, default=100.0, help="TL medyan")
    ap.add_argument("--oneoff_sigma", type=float, default=0.5, help="lognormal sigma")
    # Segments
    ap.add_argument("--youth_rate", type=float, default=0.30)
    ap.add_argument("--corporate_rate", type=float, default=0.20)
    ap.add_argument("--tourist_rate", type=float, default=0.05)
    return ap.parse_args()


def _read_df(root: Path, name: str) -> pd.DataFrame:
    p = root / f"{name}.csv"
    if not p.exists():
        raise FileNotFoundError(f"Bulunamadı: {p}")
    return pd.read_csv(p)


def _write_df(root: Path, name: str, df: pd.DataFrame):
    (root / f"{name}.csv").parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(root / f"{name}.csv", index=False)


def assign_segments(users: pd.DataFrame, youth_rate: float, corporate_rate: float, tourist_rate: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(users)
    k = np.arange(n)
    rng.shuffle(k)
    n_youth = int(n * youth_rate)
    n_corp = int(n * corporate_rate)
    n_tour = int(n * tourist_rate)
    seg = pd.Series(["retail"] * n)
    seg.iloc[k[:n_youth]] = "youth"
    seg.iloc[k[n_youth:n_youth+n_corp]] = "corporate"
    seg.iloc[k[n_youth+n_corp:n_youth+n_corp+n_tour]] = "tourist"
    users = users.copy()
    users["type"] = seg.values
    return users


def add_discounts(bill_headers: pd.DataFrame, bill_items: pd.DataFrame, users: pd.DataFrame, rate: float, pmin: float, pmax: float, seed: int) -> pd.DataFrame:
    """Her kullanıcı için SON AY faturasında belirli oranda indirim (negatif kalem) ekle.
    İndirim oranı: uniform[pmin, pmax]%
    """
    rng = np.random.default_rng(seed + 10)
    # Son ayı bul (global)
    last_period = pd.to_datetime(bill_headers["period_start"]).max()
    # Bu dönemin faturaları
    bh_last = bill_headers[pd.to_datetime(bill_headers["period_start"]) == last_period]
    chosen = bh_last.sample(frac=rate, random_state=seed).copy()
    if chosen.empty:
        return bill_items

    # Her seçili fatura için indirim kalemi ekle
    extra_rows = []
    for _, h in chosen.iterrows():
        bill_id = int(h["bill_id"])
        # O faturanın ara toplamını tahmin etmek için mevcut kalemleri topla (vergiler dahil)
        cur_items = bill_items[bill_items["bill_id"] == bill_id]
        gross = float(cur_items["amount"].sum())
        disc_pct = rng.uniform(pmin, pmax) / 100.0
        disc_amt = round(gross * disc_pct * -1.0, 2)
        extra_rows.append([
            bill_id, 90, "discount", "loyalty", f"Sadakat indirimi (-{disc_pct*100:.1f}%)", disc_amt, disc_amt, 1, 0.0, h["period_end"],
        ])
    if extra_rows:
        add_df = pd.DataFrame(extra_rows, columns=bill_items.columns)
        bill_items = pd.concat([bill_items, add_df], ignore_index=True)
    return bill_items


def add_oneoffs(bill_headers: pd.DataFrame, bill_items: pd.DataFrame, users: pd.DataFrame, rate: float, med: float, sigma: float, seed: int) -> pd.DataFrame:
    """Rastgele seçilen kullanıcıların SON AY faturalarına one-off (cihaz/aktivasyon) ekle.
    Tutar: lognormal(median=med, sigma)
    """
    rng = np.random.default_rng(seed + 20)
    last_period = pd.to_datetime(bill_headers["period_start"]).max()
    bh_last = bill_headers[pd.to_datetime(bill_headers["period_start"]) == last_period]
    chosen = bh_last.sample(frac=rate, random_state=seed+1).copy()
    if chosen.empty:
        return bill_items

    mu = np.log(max(1e-6, med))  # yaklaşık median ≈ exp(mu)
    extra_rows = []
    for _, h in chosen.iterrows():
        bill_id = int(h["bill_id"])
        amt = float(np.random.lognormal(mean=mu, sigma=sigma))
        amt = round(amt, 2)
        extra_rows.append([
            bill_id, 85, "one_off", "device_or_activation", "Tek seferlik ücret", amt, amt, 1, 0.18, h["period_end"],
        ])
    if extra_rows:
        add_df = pd.DataFrame(extra_rows, columns=bill_items.columns)
        bill_items = pd.concat([bill_items, add_df], ignore_index=True)
    return bill_items


def adjust_usage_for_segments(usage_daily: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """Segment bazlı çarpanlar uygulayarak kullanım desenini hafifçe yeniden ölçeklendir.
    - youth: data x1.25, minutes x0.9, sms x0.9
    - corporate: data x0.9, minutes x1.2, sms x1.1
    - tourist: data x1.3 (roaming varsa x1.5), minutes x0.8, sms x0.8
    - retail: no-op
    """
    users_idx = users.set_index("user_id")["type"].to_dict()
    ud = usage_daily.copy()

    def mults(kind: str, roam_mb: float):
        if kind == "youth":
            return 1.25, 0.9, 0.9
        if kind == "corporate":
            return 0.9, 1.2, 1.1
        if kind == "tourist":
            return (1.5 if roam_mb > 0 else 1.3), 0.8, 0.8
        return 1.0, 1.0, 1.0

    # Uygula
    data = []
    for idx, row in ud.iterrows():
        kind = users_idx.get(row.user_id, "retail")
        m_gb, m_min, m_sms = mults(kind, row.roaming_mb)
        data.append([
            row.user_id,
            row.date,
            float(row.mb_used * m_gb),
            float(row.minutes_used * m_min),
            int(round(row.sms_used * m_sms)),
            float(row.roaming_mb),
        ])
    new_ud = pd.DataFrame(data, columns=ud.columns)
    return new_ud


def main():
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    in_root = Path(args.data)
    out_root = Path(args.out) if args.out else in_root
    out_root.mkdir(parents=True, exist_ok=True)

    users = _read_df(in_root, "users")
    plans = _read_df(in_root, "plans")
    bill_headers = _read_df(in_root, "bill_headers")
    bill_items = _read_df(in_root, "bill_items")
    usage_daily = _read_df(in_root, "usage_daily")

    # 1) Segment ataması
    users2 = assign_segments(users, args.youth_rate, args.corporate_rate, args.tourist_rate, args.seed)

    # 2) Segment etkilerini usage üzerine uygula
    usage2 = adjust_usage_for_segments(usage_daily, users2)

    # 3) Discount ve One-off kalemleri ekle (son aya)
    bill_items2 = add_discounts(bill_headers, bill_items, users2, args.discount_rate, args.discount_min, args.discount_max, args.seed)
    bill_items2 = add_oneoffs(bill_headers, bill_items2, users2, args.oneoff_rate, args.oneoff_med, args.oneoff_sigma, args.seed)

    # 4) Çıktıyı yaz
    _write_df(out_root, "users", users2)
    _write_df(out_root, "plans", plans)
    _write_df(out_root, "bill_headers", bill_headers)
    _write_df(out_root, "bill_items", bill_items2)
    _write_df(out_root, "usage_daily", usage2)

    print("✓ Güncelleme tamamlandı →", out_root.resolve())
    print("Güncellenen dosyalar: users.csv, bill_items.csv, usage_daily.csv")


if __name__ == "__main__":
    main()
