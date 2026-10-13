# Prescriptive Maintenance Workbench API
# Rules + Isolation Forest. Work order is the product.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import json
from pathlib import Path
from datetime import datetime, timedelta
import uuid

app = FastAPI(title="Prescriptive Maintenance Workbench", version="0.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DATA_DIR = Path("../data")
WO_STORE = DATA_DIR / "work_orders.json"

# Load static data
assets = json.loads((DATA_DIR / "assets.json").read_text())
failure_modes = json.loads((DATA_DIR / "failure_modes.json").read_text())
signals = pd.read_csv(DATA_DIR / "signals.csv")
signals["timestamp"] = pd.to_datetime(signals["timestamp"])

# In-memory work orders + audit
if WO_STORE.exists():
    work_orders = json.loads(WO_STORE.read_text())
else:
    work_orders = []

def save_work_orders():
    WO_STORE.write_text(json.dumps(work_orders, indent=2, default=str))

# Simple production calendar mock: next changeover in 18 hours for Process Unit B
NEXT_CHANGEOVER = datetime.now() + timedelta(hours=18)

class AcceptRequest(BaseModel):
    work_order_id: str
    actor: str
    reason: Optional[str] = None

class OverrideRequest(BaseModel):
    work_order_id: str
    actor: str
    reason: str

def compute_features(asset_id: str, recent_hours: int = 24, baseline_days: int = 30) -> Dict:
    """Features maintenance people trust: RMS, kurtosis, temp rise vs load, runtime."""
    df = signals[signals["asset_id"] == asset_id].sort_values("timestamp")
    if df.empty:
        return {}
    recent = df.tail(recent_hours)
    cutoff = df["timestamp"].max() - pd.Timedelta(days=14)
    baseline = df[df["timestamp"] < cutoff].tail(baseline_days * 24)
    if baseline.empty:
        baseline = df.head(min(len(df)//2, baseline_days*24))
    
    features = {
        "asset_id": asset_id,
        "latest_timestamp": df["timestamp"].max().isoformat(),
        "vibration_rms_recent": float(recent["vibration_rms"].mean()),
        "vibration_rms_baseline": float(baseline["vibration_rms"].mean()) if len(baseline) else float(recent["vibration_rms"].mean()),
        "vibration_kurtosis_recent": float(recent["vibration_kurtosis"].mean()),
        "vibration_kurtosis_baseline": float(baseline["vibration_kurtosis"].mean()) if len(baseline) else 3.0,
        "temperature_recent": float(recent["temperature_c"].mean()),
        "temp_rise_vs_load": float((recent["temperature_c"] - 40 - recent["load_pct"] * 0.05).mean()),
        "runtime_hours": float(df["runtime_hours"].max()),
        "sensor_flatline_pct": float((df["sensor_status"] == "flatline").mean()),
        "latest_sensor_status": df["sensor_status"].iloc[-1],
        "rms_trend_slope": float(np.polyfit(range(len(recent)), recent["vibration_rms"], 1)[0]) if len(recent) > 5 else 0.0,
        "kurtosis_trend_slope": float(np.polyfit(range(len(recent)), recent["vibration_kurtosis"], 1)[0]) if len(recent) > 5 else 0.0,
    }
    return features

def detect_sensor_bad(features: Dict) -> bool:
    return features.get("latest_sensor_status") == "flatline" or features.get("sensor_flatline_pct", 0) > 0.05

def rules_engine(asset: Dict, features: Dict) -> Optional[Dict]:
    """Boring rule first. Outer-race wear on pumps: rising kurtosis + RMS, sensor ok."""
    if detect_sensor_bad(features):
        return {
            "type": "sensor_issue",
            "failure_mode": "Sensor fault / flatline",
            "urgency": "low",
            "confidence": 0.95,
            "evidence": f"Sensor status {features['latest_sensor_status']}, flatline % {features['sensor_flatline_pct']:.1%}. Not an asset failure.",
            "procedure": "Inspect and replace probe / wiring. Do not schedule mechanical repair.",
            "parts": "Vibration sensor, cabling",
            "hours": 1.0
        }
    
    if asset["asset_type"] == "pump":
        rms_ratio = features["vibration_rms_recent"] / max(features["vibration_rms_baseline"], 0.1)
        kurt_ratio = features["vibration_kurtosis_recent"] / max(features["vibration_kurtosis_baseline"], 1.0)
        if kurt_ratio > 1.4 and rms_ratio > 1.3 and features["kurtosis_trend_slope"] > 0.01:
            mode = next((m for m in failure_modes if m["asset_type"] == "pump" and "Outer race" in m["failure_mode"]), None)
            if mode:
                return {
                    "type": "asset_failure",
                    "failure_mode": mode["failure_mode"],
                    "cause": mode["cause"],
                    "urgency": "high" if rms_ratio > 1.6 else "medium",
                    "confidence": min(0.92, 0.6 + (kurt_ratio - 1.4) * 0.4),
                    "evidence": f"Kurtosis {features['vibration_kurtosis_recent']:.1f} (baseline {features['vibration_kurtosis_baseline']:.1f}, +{((kurt_ratio-1)*100):.0f}%), RMS {features['vibration_rms_recent']:.2f} (baseline {features['vibration_rms_baseline']:.2f}). Rising trend. Consistent with outer-race defect (ISO 14224 / FMECA). Sensor OK.",
                    "procedure": mode["typical_task"],
                    "parts": mode["typical_parts"],
                    "hours": mode["avg_repair_hours"],
                    "downtime_cost_per_hour": mode["downtime_cost_per_hour"]
                }
    return None

def isolation_forest_score(asset_id: str) -> float:
    asset = next(a for a in assets if a["id"] == asset_id)
    peers = [a["id"] for a in assets if a["asset_type"] == asset["asset_type"]]
    rows = []
    for pid in peers:
        f = compute_features(pid)
        if f:
            rows.append([
                f["vibration_rms_recent"],
                f["vibration_kurtosis_recent"],
                f["temperature_recent"],
                f["temp_rise_vs_load"],
                f["rms_trend_slope"]
            ])
    if len(rows) < 5:
        return 0.0
    X = np.array(rows)
    clf = IsolationForest(contamination=0.1, random_state=42)
    clf.fit(X)
    target_idx = peers.index(asset_id)
    score = -clf.score_samples(X[target_idx:target_idx+1])[0]
    return float(score)

def draft_work_order(asset_id: str) -> Optional[Dict]:
    asset = next((a for a in assets if a["id"] == asset_id), None)
    if not asset:
        return None
    features = compute_features(asset_id)
    if not features:
        return None
    
    rule_hit = rules_engine(asset, features)
    if not rule_hit:
        return None
    
    if_score = isolation_forest_score(asset_id)
    model_conf = min(0.95, max(0.4, if_score * 0.3))
    confidence = round((rule_hit["confidence"] * 0.7 + model_conf * 0.3), 2)
    
    window_start = datetime.now() + timedelta(hours=6)
    window_end = window_start + timedelta(hours=rule_hit["hours"])
    if window_end > NEXT_CHANGEOVER - timedelta(hours=2):
        window_start = NEXT_CHANGEOVER - timedelta(hours=rule_hit["hours"] + 4)
        window_end = window_start + timedelta(hours=rule_hit["hours"])
    
    dollar_impact = rule_hit.get("downtime_cost_per_hour", 2000) * rule_hit["hours"] * (1 if asset["criticality"] == "critical" else 0.6)
    
    wo = {
        "id": f"WO-{uuid.uuid4().hex[:8].upper()}",
        "asset_id": asset_id,
        "asset_name": asset["name"],
        "failure_mode": rule_hit["failure_mode"],
        "urgency": rule_hit["urgency"],
        "procedure": rule_hit["procedure"],
        "spare_parts": rule_hit["parts"],
        "estimated_hours": rule_hit["hours"],
        "scheduled_window": f"{window_start.strftime('%Y-%m-%d %H:%M')} – {window_end.strftime('%Y-%m-%d %H:%M')}",
        "production_impact": f"Scheduled to complete before next changeover ({NEXT_CHANGEOVER.strftime('%Y-%m-%d %H:%M')}). Avoids unplanned disruption to Process Unit B order.",
        "confidence": confidence,
        "dollar_impact": round(dollar_impact),
        "status": "recommended",
        "recommended_at": datetime.now().isoformat(),
        "decided_at": None,
        "decided_by": None,
        "override_reason": None,
        "evidence": rule_hit["evidence"],
        "features": {k: round(v, 3) if isinstance(v, float) else v for k, v in features.items() if k != "asset_id"},
        "model_score": round(if_score, 3),
        "type": rule_hit["type"]
    }
    return wo

@app.get("/assets")
def list_assets():
    result = []
    for a in assets:
        f = compute_features(a["id"])
        status = "healthy"
        if f:
            if detect_sensor_bad(f):
                status = "sensor_issue"
            elif f.get("vibration_kurtosis_recent", 3) > 4.5 or f.get("vibration_rms_recent", 2) > 4:
                status = "attention"
        result.append({**a, "status": status, "latest_rms": f.get("vibration_rms_recent"), "latest_kurtosis": f.get("vibration_kurtosis_recent")})
    return result

@app.get("/asset/{asset_id}/trends")
def get_trends(asset_id: str, hours: int = 720):
    df = signals[signals["asset_id"] == asset_id].sort_values("timestamp").tail(hours)
    if df.empty:
        raise HTTPException(404, "No data")
    return {
        "asset_id": asset_id,
        "timestamps": df["timestamp"].dt.strftime("%Y-%m-%d %H:%M").tolist(),
        "vibration_rms": df["vibration_rms"].tolist(),
        "vibration_kurtosis": df["vibration_kurtosis"].tolist(),
        "temperature_c": df["temperature_c"].tolist(),
        "current_a": df["current_a"].tolist(),
        "load_pct": df["load_pct"].tolist(),
        "sensor_status": df["sensor_status"].tolist()
    }

@app.get("/recommendations")
def get_recommendations():
    recs = []
    for a in assets:
        wo = draft_work_order(a["id"])
        if wo and wo["status"] == "recommended":
            recs.append(wo)
    existing_ids = {w["id"] for w in work_orders}
    for r in recs:
        if r["id"] not in existing_ids:
            work_orders.append(r)
    save_work_orders()
    return recs

@app.get("/work-orders")
def list_work_orders():
    return work_orders

@app.post("/work-order/accept")
def accept_wo(req: AcceptRequest):
    wo = next((w for w in work_orders if w["id"] == req.work_order_id), None)
    if not wo:
        raise HTTPException(404, "Work order not found")
    wo["status"] = "accepted"
    wo["decided_at"] = datetime.now().isoformat()
    wo["decided_by"] = req.actor
    save_work_orders()
    return {"ok": True, "work_order": wo}

@app.post("/work-order/override")
def override_wo(req: OverrideRequest):
    if not req.reason or len(req.reason.strip()) < 5:
        raise HTTPException(400, "Override requires a reason")
    wo = next((w for w in work_orders if w["id"] == req.work_order_id), None)
    if not wo:
        raise HTTPException(404, "Work order not found")
    wo["status"] = "overridden"
    wo["decided_at"] = datetime.now().isoformat()
    wo["decided_by"] = req.actor
    wo["override_reason"] = req.reason
    save_work_orders()
    return {"ok": True, "work_order": wo}

@app.get("/case-study")
def case_study():
    total_recs = len(work_orders)
    accepted = sum(1 for w in work_orders if w["status"] == "accepted")
    overridden = sum(1 for w in work_orders if w["status"] == "overridden")
    sensor_kills = sum(1 for w in work_orders if w.get("type") == "sensor_issue")
    real_caught = sum(1 for w in work_orders if w.get("failure_mode") == "Outer race bearing wear")
    return {
        "false_alarms_killed": sensor_kills + overridden,
        "real_ones_caught": real_caught,
        "saved_changeover": 1 if any("P-204" in w["asset_id"] and w["status"] == "accepted" for w in work_orders) else 0,
        "total_recommendations": total_recs,
        "accepted": accepted,
        "overridden": overridden,
        "quote": "I treated the work order as the product. The model only existed to justify a task, a part, and a time window a planner could defend."
    }

app.mount("/ui", StaticFiles(directory="../frontend", html=True), name="ui")

@app.get("/")
def root():
    return FileResponse("../frontend/index.html")
