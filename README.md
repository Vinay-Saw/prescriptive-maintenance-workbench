# Prescriptive Maintenance Workbench

Reliability console for one plant (~40 assets). The product is a recommended **work order**, not a health score.

## What it demonstrates

- Seeded 90 days of vibration RMS, kurtosis, temperature, current, runtime, load.
- Pump **P-204** develops outer-race bearing wear. The system names the failure mode (not “anomaly”), cites the evidence (kurtosis +87%, RMS rise, sensor OK), drafts a work order with parts, 4-hour window, and production impact that avoids the next changeover.
- Audit trail: accept or override (override requires a reason).
- Separates “sensor bad” (flatline) from “asset bad”.
- Boring rules first + Isolation Forest confirmation.
- Cost language: dollar impact, avoided downtime, confidence.
- Features maintenance people trust: RMS, kurtosis, temperature rise vs load, runtime hours.
- Failure taxonomy style: asset → failure mode → cause → task → parts.

## Stack

- Python FastAPI (REST)
- Pandas + Parquet/CSV historian (signals)
- JSON for assets / failure modes
- scikit-learn Isolation Forest
- Single-file Tailwind + Chart.js UI (no build step)

Raw waveforms stay conceptual (edge box computes features; plant server owns work orders).

## Run

```bash
# From the project root
pip install -r requirements.txt
python backend/seed.py          # generates data/signals.csv if missing
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000 (UI is served at root).

## Key endpoints

- `GET /assets` — tree with status
- `GET /asset/P-204/trends` — time series
- `GET /recommendations` — drafts work orders for active rules
- `POST /work-order/accept` / `/override`
- `GET /case-study` — “12 false alarms killed, 3 real ones caught…” numbers

## Interview line

“I treated the work order as the product. The model only existed to justify a task, a part, and a time window a planner could defend.”
