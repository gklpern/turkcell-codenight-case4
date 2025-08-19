import pandas as pd

artifacts = "D:/GIT/turkcell_codenight/artifacts"
cat = pd.read_csv(f"{artifacts}/category_breakdown.csv")
summary = pd.read_csv(f"{artifacts}/bill_summary.csv")

# yüksek roaming/premium_sms/vas olan ilk 5 fatura
sus = cat[cat["category"].isin(["roaming","premium_sms","vas"])] \
        .sort_values("category_total", ascending=False) \
        .head(5)

print(sus[["bill_id","category","category_total"]])

# bunları summary ile joinleyelim
merged = sus.merge(summary[["bill_id","user_id","period"]], on="bill_id", how="left")
print(merged[["user_id","period","category","category_total"]])
