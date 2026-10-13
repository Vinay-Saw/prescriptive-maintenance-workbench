# Case Study: Outer-Race Wear on Pump P-204

**Plant Alpha Reliability Console**  
90-day seeded historian · Rules + Isolation Forest · Work order as product

## What happened

Pump P-204 (critical, Process Unit B) showed progressive rise in vibration kurtosis (+87% vs. baseline) and RMS after day 60. Temperature rose modestly with load. Sensor status remained “ok” — not a flatlined probe.

## What the system did

- Named the failure mode: **Outer race bearing wear** (ISO 14224 / FMECA style), not “anomaly”.
- Cited evidence: kurtosis 6.6 (baseline 3.5), RMS 4.85 (baseline 2.83), rising trend, sensor healthy.
- Drafted work order:
  - Procedure: Replace bearing set, check lubrication and seals
  - Parts: Bearing kit (SKF 6310 or equiv), seal kit, oil
  - Window: 4-hour slot scheduled to finish before next changeover
  - Dollar impact: $10,000 avoided unplanned downtime
  - Confidence: 0.67 (rule primary, Isolation Forest confirmation)
- Logged accept/override with reason required for override. Audit trail is the senior signal.

## Numbers (demo run)

- Real ones caught: 1 (P-204 outer-race)
- False alarms killed: sensor-flatline cases separated from asset faults; overrides require reason
- Saved changeover: 1 (window avoids production order disruption)
- Features used: RMS, kurtosis, temperature rise vs. load, runtime hours — not a black-box score alone

## Interview line

“I treated the work order as the product. The model only existed to justify a task, a part, and a time window a planner could defend.”

---
Edge box computes health features; plant server owns work orders and CMMS loop. Raw waveforms do not leave the cell.
