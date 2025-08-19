# anomaly_engine.py
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================
# Config
# ==============================
Z_THRESH = 2.0          # z-score >= 2 -> anomali
PCT_THRESH = 0.80       # % artış >= %80 -> anomali
MIN_TL = 5.0            # gürültüyü azaltmak için min tutar eşiği
BASELINE_MONTHS = 3     # geçmiş pencere
EXCLUDE_CATEGORIES = {"tax"}  # genelde vergi değişimleri sinyal değil

# Kategoriye göre aksiyon önerileri
SUGGEST_ACTION = {
    "premium_sms": "Premium SMS engelle/iptal et",
    "vas": "VAS aboneliklerini gözden geçir/iptal et",
    "roaming": "Roaming paketi al veya veri dolaşımını kapat",
    "data": "Daha yüksek kotalı plana geç veya ek data paketi ekle",
    "voice": "Daha yüksek dakika içeren planı değerlendir",
    "sms": "SMS paketi ekle veya mesajlaşma uygulamalarını kullan",
    "one_off": "Tek seferlik ücret için destekle iletişime geç",
    "discount": "İndirim koşullarını kontrol et (kampanya bitti mi?)",
}

def _to_period(s):
    return pd.to_datetime(s).dt.to_period("M").astype(str)

def _safe_div(a, b):
    return float(a) / float(b) if float(b) != 0 else np.inf

# ==============================
# Load artifacts (+ optional raw)
# ==============================
def load_artifacts(artifacts_dir: Path):
    bill_summary = pd.read_csv(artifacts_dir / "bill_summary.csv")
    cat_breakdown = pd.read_csv(artifacts_dir / "category_breakdown.csv")
    # types
    for c in ["items_total", "total_amount"]:
        if c in bill_summary.columns:
            bill_summary[c] = bill_summary[c].astype(float)
    return bill_summary, cat_breakdown

def load_raw_if_available(data_dir: Path):
    """Optional: raw bill_items to detect subtype-level 'first_seen'."""
    bi = None
    try:
        p = data_dir / "bill_items.csv"
        if p.exists():
            bi = pd.read_csv(p)
            bi["category"] = bi["category"].str.lower().str.strip()
            bi["subtype"] = bi["subtype"].fillna("unknown").str.lower().str.strip()
            # month
            # Join with bill_headers to get period if needed
            # but artifacts bill_summary already maps bill_id->period; we’ll pass mapping
    except Exception:
        bi = None
    return bi

# ==============================
# Core anomaly detection
# ==============================
def detect_anomalies_for(bill_summary, cat_breakdown, user_id: int, period: str, bill_items=None):
    period = str(period)
    # 1) Hedef faturayı bul
    user_bills = bill_summary[bill_summary["user_id"] == user_id].copy()
    if user_bills.empty:
        return {"anomalies": [], "warnings": [f"user_id={user_id} için fatura bulunamadı"]}

    # en yakın exact eşleşme
    target = user_bills[user_bills["period"] == period]
    if target.empty:
        return {"anomalies": [], "warnings": [f"user_id={user_id}, period={period} için fatura yok"]}

    target_row = target.iloc[0]
    bill_id = int(target_row["bill_id"])

    # 2) Geçmiş (baseline) penceresi
    # Kullanıcının tüm dönemleri
    periods = sorted(user_bills["period"].unique())
    if period not in periods:
        return {"anomalies": [], "warnings": [f"period={period} listede yok"]}
    idx = periods.index(period)
    prev_periods = periods[max(0, idx-BASELINE_MONTHS):idx]
    # Eğer yeterli yoksa yine mevcut olanla devam
    history_bills = user_bills[user_bills["period"].isin(prev_periods)].copy()

    # 3) Kategori toplamları (current & baseline)
    cb = cat_breakdown.copy()
    cb["category"] = cb["category"].str.lower().str.strip()

    current_cat = cb[cb["bill_id"] == bill_id].groupby("category", as_index=False)["category_total"].sum()
    hist_cat = (
        cb[cb["bill_id"].isin(history_bills["bill_id"].tolist())]
        .groupby(["category","bill_id"], as_index=False)["category_total"].sum()
    )

    # 4) Baseline istatistikleri
    baseline_stats = (
        hist_cat.groupby("category")["category_total"]
        .agg(mean="mean", std="std", count="count")
        .reset_index()
    )

    # kategori birleşimi
    all_cats = sorted(set(current_cat["category"]).union(set(baseline_stats["category"])))
    anomalies = []
    contribs = []

    # harcama değişimi katkılarını görmek için baseline toplam vs current toplam
    cur_total = float(target_row.get("items_total", np.nan))
    base_total = float(history_bills["items_total"].mean()) if not history_bills.empty else np.nan
    total_delta = cur_total - base_total if not np.isnan(cur_total) and not np.isnan(base_total) else np.nan

    for cat in all_cats:
        if cat in EXCLUDE_CATEGORIES:
            continue

        cur_amt = float(current_cat[current_cat["category"] == cat]["category_total"].sum()) if cat in set(current_cat["category"]) else 0.0

        row = baseline_stats[baseline_stats["category"] == cat]
        mean = float(row["mean"].iloc[0]) if not row.empty else 0.0
        std = float(row["std"].iloc[0]) if (not row.empty and not np.isnan(row["std"].iloc[0])) else 0.0
        count = int(row["count"].iloc[0]) if not row.empty else 0

        # First-seen?
        first_seen = (count == 0 and cur_amt >= MIN_TL)

        # z-score ve %Δ
        z = (cur_amt - mean) / std if std > 0 else None
        pct_delta = _safe_div(cur_amt - mean, mean) if mean >= MIN_TL else (np.inf if (cur_amt >= MIN_TL and mean == 0) else 0.0)

        is_spike = False
        reasons = []

        if first_seen:
            is_spike = True
            reasons.append("İlk kez görüldü")

        if cur_amt >= MIN_TL and not first_seen:
            if (z is not None and z >= Z_THRESH):
                is_spike = True
                reasons.append(f"z-skoru {z:.2f} (≥ {Z_THRESH})")
            if pct_delta >= PCT_THRESH:
                is_spike = True
                reasons.append(f"% değişim {pct_delta*100:.0f}% (≥ {int(PCT_THRESH*100)}%)")

        # Kategoriye özel heuristik (roaming/premium/vas hassas)
        if cat in {"roaming", "premium_sms", "vas"} and (cur_amt >= MIN_TL):
            # önceki ay toplam 0 ve şimdi > 0 ise 'yeni artış'
            prev_sum = float(hist_cat[hist_cat["category"] == cat]["category_total"].sum()) if count > 0 else 0.0
            if prev_sum < MIN_TL and cur_amt >= MIN_TL:
                is_spike = True
                reasons.append("Önceki aylarda yoktu/çok düşüktü, bu ay var")

        if is_spike:
            anomalies.append({
                "category": cat,
                "amount": round(cur_amt, 2),
                "baseline_mean": round(mean, 2),
                "baseline_std": round(std, 2) if std else None,
                "z": round(z, 2) if z is not None else None,
                "pct_delta": round(pct_delta, 3) if np.isfinite(pct_delta) else None,
                "reason": "; ".join(reasons),
                "suggested_action": SUGGEST_ACTION.get(cat, "Gözden geçir"),
            })

        # katkı (opsiyonel görsel/özet için)
        contribs.append({
            "category": cat,
            "current": round(cur_amt, 2),
            "baseline_mean": round(mean, 2),
            "delta": round(cur_amt - mean, 2),
        })

    # 5) subtype-level first-seen (opsiyonel)
    subtype_alerts = []
    if bill_items is not None and not bill_items.empty:
        # bill_id -> period map
        # Bunu bill_summary'den alıyoruz
        bill_map = bill_summary[["bill_id","period","user_id"]]
        bi = bill_items.merge(bill_map, on="bill_id", how="left")
        bi["category"] = bi["category"].str.lower().str.strip()
        bi["subtype"] = bi["subtype"].fillna("unknown").str.lower().str.strip()

        # aynı kullanıcının baseline subtypelarına bakalım
        base_sub = (
            bi[(bi["user_id"] == user_id) & (bi["period"].isin(prev_periods))]
            .groupby(["category", "subtype"], as_index=False)["amount"].sum()
        )
        cur_sub = (
            bi[(bi["bill_id"] == bill_id)]
            .groupby(["category", "subtype"], as_index=False)["amount"].sum()
        )

        known = set(zip(base_sub["category"], base_sub["subtype"]))
        for _, r in cur_sub.iterrows():
            key = (r["category"], r["subtype"])
            if r["amount"] >= MIN_TL and key not in known and r["category"] not in EXCLUDE_CATEGORIES:
                subtype_alerts.append({
                    "category": r["category"],
                    "subtype": r["subtype"],
                    "amount": round(float(r["amount"]), 2),
                    "reason": "Bu alt-kalem ilk kez görüldü",
                    "suggested_action": SUGGEST_ACTION.get(r["category"], "Gözden geçir"),
                })

    # 6) discount özel durumu: önce indirim vardı, bu ay yok/azaldı
    # (zaten cat=discount spike olarak işaretlenmiş olabilir; ayrıca metinle belirtelim)
    # Not: discount negatif tutar olduğundan baseline_mean negatif olabilir; basit bir kontrol yapalım.
    for a in anomalies:
        if a["category"] == "discount":
            # eğer bu ay indirim kaybı varsa (daha az negatif)
            if a["baseline_mean"] < -MIN_TL and a["amount"] > a["baseline_mean"]:
                a["reason"] += "; İndirim azalmış/bitmiş olabilir"

    # Çıktı
    result = {
        "user_id": int(user_id),
        "period": period,
        "bill_id": bill_id,
        "overall": {
            "current_total": round(cur_total, 2) if not np.isnan(cur_total) else None,
            "baseline_total_mean": round(base_total, 2) if not np.isnan(base_total) else None,
            "total_delta": round(total_delta, 2) if not np.isnan(total_delta) else None,
        },
        "anomalies": sorted(anomalies, key=lambda x: (x.get("z") or 0, x.get("pct_delta") or 0, x["amount"]), reverse=True),
        "contributors": sorted(contribs, key=lambda x: x["delta"], reverse=True),
        "subtype_first_seen": subtype_alerts,
        "warnings": [] if history_bills.shape[0] > 0 else ["Yetersiz geçmiş veri (baseline zayıf)"],
    }
    return result

# ==============================
# CLI
# ==============================
def main():
    global Z_THRESH, PCT_THRESH   # <<< en üste al
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", type=str, default="artifacts", help="data_prep çıktıları (bill_summary.csv, category_breakdown.csv)")
    ap.add_argument("--data", type=str, default=None, help="(Opsiyonel) raw csv klasörü (bill_items.csv için)")
    ap.add_argument("--user_id", type=int, required=True)
    ap.add_argument("--period", type=str, required=True, help="YYYY-MM")
    ap.add_argument("--z", type=float, default=Z_THRESH)
    ap.add_argument("--pct", type=float, default=PCT_THRESH)
    args = ap.parse_args()

    Z_THRESH = args.z
    PCT_THRESH = args.pct


    artifacts_dir = Path(args.artifacts)
    bill_summary, cat_breakdown = load_artifacts(artifacts_dir)

    bill_items = None
    if args.data:
        bill_items = load_raw_if_available(Path(args.data))

    out = detect_anomalies_for(bill_summary, cat_breakdown, args.user_id, args.period, bill_items=bill_items)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
