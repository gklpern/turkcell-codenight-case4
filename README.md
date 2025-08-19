# Turkcell Bill Assistant (Codenight Case) — MVP

A lightweight backend that (1) **explains** monthly bills, (2) **detects anomalies** (z-score / %Δ, first-seen, roaming & Premium/VAS spikes), and (3) runs **what-if simulations** to find the **3 cheapest** scenarios.

## Status
This repository starts empty by design. Use the bootstrap steps below to get a running FastAPI skeleton in minutes.

## API contract (planned)
- `POST /api/explain` — Itemize bill + short NL summary
- `POST /api/anomalies` — Z-score & %Δ spikes, first-seen, roaming/premium/VAS checks
- `POST /api/whatif` — Try plan change / add-on / disable VAS/Premium; return top-3 cheapest
- `POST /api/checkout` — Mock endpoint to “apply” a chosen scenario

## Minimal data model (CSV-friendly)
- **users**(user_id, msisdn, plan_id, segment)
- **plans**(plan_id, name, monthly_fee, voice_min, data_mb, sms_count, …)
- **bill_headers**(bill_id, user_id, bill_date, total_amount)
- **bill_items**(bill_id, category, sub_category, amount, unit, qty, notes)
- **usage_daily**(user_id, date, voice_min, data_mb, sms_count, roaming_data_mb, …)
- **vas_catalog**(vas_id, name, monthly_fee, description)
- **premium_sms_catalog**(shortcode, service_name, price_per_sms)
- **add_on_packs**(pack_id, name, price, data_mb, voice_min, sms_count, validity_days)

## Bootstrap (quick start)
> If you already have code, skip this section. If not, use this to create a runnable skeleton.

```bash
# Create folders
mkdir -p app/api app/services app/core data general_scripts

# Create a tiny FastAPI entrypoint
cat > app/main.py << 'PY'
from fastapi import FastAPI
app = FastAPI(title="Turkcell Bill Assistant")

@app.get("/")
def health():
    return {"ok": True}

# Stubs (fill later)
@app.post("/api/explain")
def explain(payload: dict): return {"todo": "explain"}

@app.post("/api/anomalies")
def anomalies(payload: dict): return {"todo": "anomalies"}

@app.post("/api/whatif")
def whatif(payload: dict): return {"todo": "whatif"}

@app.post("/api/checkout")
def checkout(payload: dict): return {"todo": "checkout"}
PY

# Requirements
cat > requirements.txt << 'REQ'
fastapi
uvicorn[standard]
pydantic
pandas
numpy
REQ

Run locally:

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs

Git basics (first push)

git init
git remote add origin https://github.com/gklpern/turkcell-codenight-case4
echo "# Turkcell Bill Assistant (MVP)" > README.md
# ensure .gitignore exists (see below), then:
git add .
git commit -m "Bootstrap: README, .gitignore, FastAPI skeleton"
git branch -M main
git push -u origin main

Roadmap

    Implement real explain/anomaly/what-if engines

    Plug in CSV loaders under data/

    Optional local LLM (Ollama) for short summaries

    Tests & CI
