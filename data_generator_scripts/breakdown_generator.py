# === make_category_breakdown (pure Python, no shell) ===
import pandas as pd
from pathlib import Path

# KÖK klasörünü kendi yoluna göre ayarla (gerekirse değiştir)
BASE = Path(r"D:\GIT\turkcell_codenight")
DATA = BASE / "data"
OUT  = BASE / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)

# 1) bill_items.csv oku (sağlam okuma)
bi = pd.read_csv(DATA / "bill_items.csv")

# a) kategorileri normalize et
bi["category"] = bi["category"].astype(str).str.lower().str.strip()
if "subtype" in bi.columns:
    bi["subtype"] = bi["subtype"].astype(str).str.lower().str.strip()

# b) sayısal alanları zorla sayıya çevir (virgül/nokta olursa düzelt)
def to_num(s):
    # "12,50" gibi değerler için
    return pd.to_numeric(
        pd.Series(s, dtype="string")
          .str.replace(".", "", regex=False)   # "1.234,56" -> "1234,56"
          .str.replace(",", ".", regex=False), # "1234,56" -> "1234.56"
        errors="coerce"
    )

for c in ["amount","unit_price","quantity","tax_rate"]:
    if c in bi.columns:
        bi[c] = to_num(bi[c]) if bi[c].dtype == "object" else pd.to_numeric(bi[c], errors="coerce")

for c in ["bill_id","item_id"]:
    if c in bi.columns:
        bi[c] = pd.to_numeric(bi[c], errors="coerce")

# NaN amount -> 0
bi["amount"] = bi["amount"].fillna(0.0)

# 2) breakdown üret
cat = (
    bi.groupby(["bill_id","category"], dropna=False)
      .agg(
          category_total=("amount","sum"),
          n_items=("item_id","count"),
          unit_price_avg=("unit_price","mean"),
          tax_rate_avg=("tax_rate","mean"),
      ).reset_index()
)

# 3) yaz ve raporla
cat.to_csv(OUT / "category_breakdown.csv", index=False, encoding="utf-8")
print(f"✓ category_breakdown.csv yazıldı → {OUT}")
print("satır sayısı:", len(cat))
print("örnek kategoriler:", cat['category'].unique()[:10])
