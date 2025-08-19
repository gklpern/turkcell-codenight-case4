# -*- coding: utf-8 -*-
"""
Turkcell Fatura — Mock Veri Üretici (CSV)

Bu betik, hackathon MVP'si için ihtiyaç duyulan tüm CSV/JSON dosyalarını
tek komutla üretir ve birbirini tutan (referansları doğru) veriler oluşturur.

Üretilen dosyalar (./data klasörüne):
- users.csv
- plans.csv
- bill_headers.csv
- bill_items.csv
- usage_daily.csv
- vas_catalog.csv
- premium_sms_catalog.csv
- add_on_packs.csv

Parametrelerle kullanıcı sayısı, ay sayısı ve anomali oranı değiştirilebilir.

Nasıl çalıştırılır:
$ python mock_data_generator.py

Ya da parametreli:
$ python mock_data_generator.py --n_users 50 --n_months 4 --seed 42 --anom_rate 0.2
"""
from __future__ import annotations
import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

# ============================
# Konfigürasyon
# ============================

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data", help="Çıktı klasörü")
    ap.add_argument("--seed", type=int, default=123, help="Rastgelelik tohumu")
    ap.add_argument("--n_users", type=int, default=75, help="Kullanıcı sayısı")
    ap.add_argument("--n_months", type=int, default=4, help="Kaç ay üretilecek (son ay anomali/what-if testleri için)")
    ap.add_argument("--anom_rate", type=float, default=0.25, help="Son ayda kaç kullanıcının anomalisı olacak (0-1)")
    return ap.parse_args()

# Yardımcılar
rng = np.random.default_rng(123)

def choice(a):
    return a[rng.integers(0, len(a))]

# ============================
# Kataloglar
# ============================

def build_catalogs(seed: int):
    random.seed(seed)
    np.random.seed(seed)

    plans = pd.DataFrame([
        # plan_id, plan_name, type, quota_gb, quota_min, quota_sms, monthly_price, overage_gb, overage_min, overage_sms
        [1, "GB10 + 500dk + 100SMS", "retail", 10, 500, 100, 329.0, 40.0, 0.75, 0.75],
        [2, "GB20 + 750dk + 250SMS", "retail", 20, 750, 250, 429.0, 35.0, 0.65, 0.65],
        [3, "GB30 + 1000dk + 500SMS", "retail", 30, 1000, 500, 529.0, 30.0, 0.55, 0.55],
        [4, "GB50 + 1500dk + 1000SMS", "retail", 50, 1500, 1000, 699.0, 25.0, 0.45, 0.45],
        [5, "Sınırsız Sosyal + GB15 + 750dk", "youth", 15, 750, 200, 479.0, 32.0, 0.60, 0.60],
    ], columns=["plan_id","plan_name","type","quota_gb","quota_min","quota_sms","monthly_price","overage_gb","overage_min","overage_sms"])

    add_on_packs = pd.DataFrame([
        [101, "Sosyal 5GB", "data", 5, 0, 0, 79.0],
        [102, "Video 10GB", "data", 10, 0, 0, 129.0],
        [103, "Konuşma 250dk", "voice", 0, 250, 0, 49.0],
        [104, "SMS 500", "sms", 0, 0, 500, 39.0],
    ], columns=["addon_id","name","type","extra_gb","extra_min","extra_sms","price"])

    vas_catalog = pd.DataFrame([
        [201, "Müzik+", 29.9, "Turkcell"],
        [202, "Dijital Dergi", 24.9, "3rdPartyMedia"],
        [203, "Oyun Kulübü", 19.9, "Turkcell"],
    ], columns=["vas_id","name","monthly_fee","provider"])

    premium_sms_catalog = pd.DataFrame([
        ["7979", "CharityOrg", 15.0],
        ["8888", "Oyunİçi", 12.0],
        ["4545", "ServisSağlayıcıX", 10.0],
    ], columns=["shortcode","provider","unit_price"])

    return plans, add_on_packs, vas_catalog, premium_sms_catalog

# ============================
# Kullanıcılar
# ============================

def build_users(n_users: int, plans: pd.DataFrame) -> pd.DataFrame:
    users = []
    for i in range(n_users):
        uid = 1000 + i
        plan = plans.sample(1, random_state=uid).iloc[0]
        msisdn = f"5{rng.integers(0,9)}{rng.integers(100000000, 999999999)}"[:10]
        users.append([uid, f"Kullanıcı {i+1}", int(plan.plan_id), "retail", msisdn])
    return pd.DataFrame(users, columns=["user_id","name","current_plan_id","type","msisdn"])

# ============================
# Kullanım ve Fatura simülasyonu
# ============================

def month_range(n_months: int) -> List[pd.Timestamp]:
    # Son ay: şimdiye en yakın; önceki aylar geriye
    base = pd.Timestamp.today().normalize().replace(day=1)
    return [base - pd.DateOffset(months=i) for i in range(n_months)][::-1]


def simulate_usage(users: pd.DataFrame, months: List[pd.Timestamp]) -> pd.DataFrame:
    """Gerçekçiliği artırılmış kullanım simülasyonu.
    - Data: log-normal (GB), hafta sonu hafif artış, ay içi sezonluk dalgalanma
    - Dakika: gamma (pozitif skew), hafta içi daha yüksek
    - SMS: sıfır-şişkin Poisson (çoğu gün 0 SMS)
    - Roaming: nadir seyahatler → geometrik uzunlukta kümeler + log-normal günlük MB
    """
    rows = []
    for _, u in users.iterrows():
        # Kişiye özgü tabanlar
        base_gb = rng.lognormal(mean=2.4, sigma=0.5)   # median ~11 GB civarı
        base_min = rng.gamma(shape=3.0, scale=200.0)   # mean ~600 dk
        base_sms_m = max(10.0, rng.lognormal(mean=2.2, sigma=0.7))  # aylık SMS ortalaması

        for m in months:
            days = pd.period_range(m, m + pd.offsets.MonthEnd(0), freq="D").to_timestamp()
            n = len(days)

            # Ay içi yumuşak sezonluk dalga (sinüs) [0.85, 1.15]
            phase = rng.uniform(0, 2*np.pi)
            seasonal = 1.0 + 0.15*np.sin(np.linspace(0, 2*np.pi, n, endpoint=False) + phase)

            # Hafta içi/sonu çarpanları
            weekday_mult = np.array([1.10 if d.weekday() < 5 else 0.95 for d in days])  # dk için
            weekend_data_boost = np.array([1.05 if d.weekday() >= 5 else 0.98 for d in days])

            # Günlük ortalamalar
            mean_gb_day = (base_gb / n) * seasonal * weekend_data_boost
            mean_min_day = (base_min / n) * seasonal * weekday_mult
            mean_sms_day = (base_sms_m / n) * seasonal

            # Gerçekleşen değerler
            day_gb = rng.lognormal(mean=np.log(np.clip(mean_gb_day, 1e-3, None)), sigma=0.35)
            day_min = rng.gamma(shape=3.0, scale=np.clip(mean_min_day/3.0, 1e-3, None))

            # Zero-inflated Poisson (çoğu gün 0 SMS)
            p_zero = 0.4
            lam_sms = np.clip(mean_sms_day, 0.01, None)
            sms_draw = rng.poisson(lam=lam_sms)
            zeros = rng.random(n) < p_zero
            sms_draw[zeros] = 0

            # Roaming: bu ay seyahat var mı? küçük olasılık
            roaming_mb = np.zeros(n)
            if rng.random() < 0.18:  # %18 ayda bir seyahat
                # Geometrik uzunlukta burst (3–7 gün)
                burst_len = int(np.clip(rng.geometric(p=0.35), 3, 7))
                start_idx = int(rng.integers(0, max(1, n - burst_len)))
                # Günlük roaming MB log-normal (ortalama ~180MB)
                roam_slice = rng.lognormal(mean=np.log(180.0), sigma=0.7, size=burst_len)
                roaming_mb[start_idx:start_idx+burst_len] = roam_slice

            for i, d in enumerate(days):
                rows.append([
                    u.user_id,
                    d,
                    float(day_gb[i]*1024.0),
                    float(day_min[i]),
                    int(sms_draw[i]),
                    float(roaming_mb[i]),
                ])
    return pd.DataFrame(rows, columns=["user_id","date","mb_used","minutes_used","sms_used","roaming_mb"])


def build_billing(
    users: pd.DataFrame,
    plans: pd.DataFrame,
    usage_daily: pd.DataFrame,
    months: List[pd.Timestamp],
    vas_catalog: pd.DataFrame,
    premium_sms_catalog: pd.DataFrame,
    anom_rate: float = 0.25,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Gerçekçi faturalandırma:
    - VAS aboneliği kullanıcı-bazında kalıcı; her ay %5 churn/iptal olasılığı
    - Premium SMS: sıfır-şişkin Poisson; anomali aylarında λ yükseltilir
    - Roaming kalemi: usage_daily'den alınır
    """
    bill_headers = []
    bill_items = []

    bill_id_seq = 700000
    plan_map = plans.set_index("plan_id").to_dict(orient="index")

    last_month = months[-1]
    anom_users = set(rng.choice(users.user_id.values, size=max(1, int(len(users)*anom_rate)), replace=False))

    # VAS abonelik durumu (kullanıcı -> vas_id or None)
    vas_state: dict[int, Optional[int]] = {}
    for _, u in users.iterrows():
        # Başlangıçta %35 ihtimalle bir VAS
        if rng.random() < 0.35:
            vas_state[int(u.user_id)] = int(vas_catalog.sample(1).iloc[0].vas_id)
        else:
            vas_state[int(u.user_id)] = None

    for _, u in users.iterrows():
        for m in months:
            bill_id_seq += 1
            period_start = pd.Timestamp(m).normalize()
            period_end = (period_start + pd.offsets.MonthEnd(0))
            issue_date = period_end + pd.Timedelta(days=3)

            plan = plan_map[int(u.current_plan_id)]

            # Kullanım agregasyonu
            ud = usage_daily[(usage_daily.user_id == u.user_id) & (usage_daily.date >= period_start) & (usage_daily.date <= period_end)]
            used_gb = ud.mb_used.sum()/1024.0
            used_min = ud.minutes_used.sum()
            used_sms = ud.sms_used.sum()
            roam_mb = ud.roaming_mb.sum()

            over_gb = max(0.0, used_gb - float(plan.get("quota_gb", 0.0)))
            over_min = max(0.0, used_min - float(plan.get("quota_min", 0.0)))
            over_sms = max(0, int(used_sms - int(plan.get("quota_sms", 0))))

            data_over_cost = over_gb * float(plan.get("overage_gb", 0.0))
            voice_over_cost = over_min * float(plan.get("overage_min", 0.0))
            sms_over_cost = over_sms * float(plan.get("overage_sms", 0.0))

            items = []
            # Sabit ücret
            items.append([bill_id_seq, 1, "one_off", "base_fee", f"Aylık sabit ücret ({plan['plan_name']})", float(plan["monthly_price"]), float(plan["monthly_price"]), 1, 0.18, period_start])

            # Aşımlar
            if data_over_cost > 0:
                items.append([bill_id_seq, 2, "data", "data_overage", f"Data aşımı {over_gb:.2f}GB", float(data_over_cost), float(plan["overage_gb"]), round(over_gb,2), 0.18, period_end])
            if voice_over_cost > 0:
                items.append([bill_id_seq, 3, "voice", "voice_overage", f"Konuşma aşımı {over_min:.0f} dk", float(voice_over_cost), float(plan["overage_min"]), round(over_min,0), 0.18, period_end])
            if sms_over_cost > 0:
                items.append([bill_id_seq, 4, "sms", "sms_overage", f"SMS aşımı {over_sms} adet", float(sms_over_cost), float(plan["overage_sms"]), int(over_sms), 0.18, period_end])

            # VAS aboneliği (persist + churn %5)
            cur_vas = vas_state[int(u.user_id)]
            if cur_vas is not None:
                vas = vas_catalog[vas_catalog.vas_id == cur_vas].iloc[0]
                items.append([bill_id_seq, 5, "vas", "vas_monthly", f"{vas['name']} aylık ücret", float(vas['monthly_fee']), float(vas['monthly_fee']), 1, 0.18, period_end])
                # churn
                if rng.random() < 0.05:
                    vas_state[int(u.user_id)] = None
            else:
                # nadiren kullanıcı yeni VAS açar
                if rng.random() < 0.05:
                    new_vas = vas_catalog.sample(1).iloc[0]
                    vas_state[int(u.user_id)] = int(new_vas.vas_id)
                    items.append([bill_id_seq, 5, "vas", "vas_monthly", f"{new_vas['name']} aylık ücret (yeni)", float(new_vas['monthly_fee']), float(new_vas['monthly_fee']), 1, 0.18, period_end])

            # Premium SMS: ZIP (zero-inflated Poisson)
            lam = 0.9
            if (m == last_month) and (u.user_id in anom_users):
                lam = 8.0  # anomali patlaması
            # Zero-inflation
            if rng.random() > 0.75:  # %25 olasılıkla premium davranışı
                prem_n = int(rng.poisson(lam))
                if prem_n > 0:
                    prem = premium_sms_catalog.sample(1).iloc[0]
                    amount = float(prem_n * prem['unit_price'])
                    items.append([bill_id_seq, 6, "premium_sms", "premium_3rdparty", f"{prem['shortcode']} numarasına {prem_n} SMS", amount, float(prem['unit_price']), int(prem_n), 0.18, period_end])

            # Roaming kalemi (kullanıma bağlı)
            if roam_mb > 0:
                roam_amount = 0.05 * float(roam_mb)  # 0.05 TL/MB ~ 50 TL/GB (basit katsayı)
                items.append([bill_id_seq, 7, "roaming", "roaming_data", f"Roaming data {float(roam_mb)/1024.0:.2f}GB", float(roam_amount), 0.05, int(roam_mb), 0.18, period_end])

            # Vergi
            subtotal = float(sum(x[5] for x in items))
            tax = subtotal * 0.18
            items.append([bill_id_seq, 99, "tax", "vat", "KDV", float(tax), float(tax), 1, 0.0, period_end])

            total_amount = subtotal + tax
            bill_headers.append([bill_id_seq, int(u.user_id), period_start, period_end, issue_date, round(total_amount,2), "TRY"])
            bill_items.extend(items)

    bill_headers_df = pd.DataFrame(bill_headers, columns=["bill_id","user_id","period_start","period_end","issue_date","total_amount","currency"])
    bill_items_df = pd.DataFrame(bill_items, columns=["bill_id","item_id","category","subtype","description","amount","unit_price","quantity","tax_rate","created_at"])
    return bill_headers_df, bill_items_df

# ============================
# Main
# ============================

def main():
    args = parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    plans, add_on_packs, vas_catalog, premium_sms_catalog = build_catalogs(args.seed)
    users = build_users(args.n_users, plans)

    months = month_range(args.n_months)
    usage_daily = simulate_usage(users, months)

    bill_headers, bill_items = build_billing(
        users, plans, usage_daily, months, vas_catalog, premium_sms_catalog, anom_rate=args.anom_rate
    )

    # Kaydet
    users.to_csv(out/"users.csv", index=False)
    plans.to_csv(out/"plans.csv", index=False)
    bill_headers.to_csv(out/"bill_headers.csv", index=False)
    bill_items.to_csv(out/"bill_items.csv", index=False)
    usage_daily.to_csv(out/"usage_daily.csv", index=False)
    vas_catalog.to_csv(out/"vas_catalog.csv", index=False)
    premium_sms_catalog.to_csv(out/"premium_sms_catalog.csv", index=False)
    add_on_packs.to_csv(out/"add_on_packs.csv", index=False)

    print(f"✓ Veri üretildi → {out.resolve()}")
    print("Dosyalar:")
    for f in ["users.csv","plans.csv","bill_headers.csv","bill_items.csv","usage_daily.csv","vas_catalog.csv","premium_sms_catalog.csv","add_on_packs.csv"]:
        print(" -", f)

if __name__ == "__main__":
    main()
