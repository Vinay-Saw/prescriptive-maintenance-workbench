# Seed data for Prescriptive Maintenance Workbench
# Assets + failure modes as JSON, signals as CSV (historian)

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from pathlib import Path

DATA_DIR = Path("../data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def seed_assets():
    assets = [
        {"id": "P-101", "name": "Cooling Water Pump", "asset_type": "pump", "location": "Utility Area", "criticality": "medium", "manufacturer": "Flowserve", "model": "3196", "install_date": "2018-03-15", "rated_power_kw": 45, "expected_mtbf_hours": 18000},
        {"id": "P-102", "name": "Process Feed Pump", "asset_type": "pump", "location": "Process Unit A", "criticality": "high", "manufacturer": "Sulzer", "model": "OHH", "install_date": "2019-06-20", "rated_power_kw": 75, "expected_mtbf_hours": 12000},
        {"id": "P-204", "name": "Main Process Pump", "asset_type": "pump", "location": "Process Unit B", "criticality": "critical", "manufacturer": "Flowserve", "model": "3196", "install_date": "2017-11-10", "rated_power_kw": 110, "expected_mtbf_hours": 10000},
        {"id": "P-205", "name": "Recycle Pump", "asset_type": "pump", "location": "Process Unit B", "criticality": "high", "manufacturer": "KSB", "model": "Etanorm", "install_date": "2020-02-28", "rated_power_kw": 55, "expected_mtbf_hours": 15000},
        {"id": "P-301", "name": "Boiler Feed Pump", "asset_type": "pump", "location": "Utility", "criticality": "critical", "manufacturer": "Sulzer", "model": "HPcp", "install_date": "2016-08-05", "rated_power_kw": 200, "expected_mtbf_hours": 8000},
        {"id": "GB-12", "name": "Conveyor Gearbox A", "asset_type": "gearbox", "location": "Material Handling", "criticality": "medium", "manufacturer": "SEW", "model": "R97", "install_date": "2019-01-12", "rated_power_kw": 15, "expected_mtbf_hours": 20000},
        {"id": "GB-13", "name": "Conveyor Gearbox B", "asset_type": "gearbox", "location": "Material Handling", "criticality": "medium", "manufacturer": "SEW", "model": "R97", "install_date": "2019-01-12", "rated_power_kw": 15, "expected_mtbf_hours": 20000},
        {"id": "GB-25", "name": "Mixer Gearbox", "asset_type": "gearbox", "location": "Process Unit A", "criticality": "high", "manufacturer": "Nord", "model": "SK", "install_date": "2018-09-30", "rated_power_kw": 22, "expected_mtbf_hours": 16000},
        {"id": "C-01", "name": "Air Compressor 1", "asset_type": "compressor", "location": "Utility", "criticality": "high", "manufacturer": "Atlas Copco", "model": "GA90", "install_date": "2015-04-18", "rated_power_kw": 90, "expected_mtbf_hours": 14000},
        {"id": "C-02", "name": "Air Compressor 2", "asset_type": "compressor", "location": "Utility", "criticality": "high", "manufacturer": "Atlas Copco", "model": "GA90", "install_date": "2015-04-18", "rated_power_kw": 90, "expected_mtbf_hours": 14000},
        {"id": "C-10", "name": "Process Gas Compressor", "asset_type": "compressor", "location": "Process Unit B", "criticality": "critical", "manufacturer": "Elliott", "model": "PAP", "install_date": "2017-07-22", "rated_power_kw": 500, "expected_mtbf_hours": 6000},
        {"id": "CV-01", "name": "Infeed Conveyor", "asset_type": "conveyor", "location": "Material Handling", "criticality": "medium", "manufacturer": "Dematic", "model": "Standard", "install_date": "2021-03-01", "rated_power_kw": 7.5, "expected_mtbf_hours": 25000},
        {"id": "CV-02", "name": "Outfeed Conveyor", "asset_type": "conveyor", "location": "Material Handling", "criticality": "medium", "manufacturer": "Dematic", "model": "Standard", "install_date": "2021-03-01", "rated_power_kw": 7.5, "expected_mtbf_hours": 25000},
        {"id": "CV-15", "name": "Overhead Conveyor", "asset_type": "conveyor", "location": "Assembly", "criticality": "low", "manufacturer": "FlexLink", "model": "X85", "install_date": "2022-01-15", "rated_power_kw": 3, "expected_mtbf_hours": 30000},
    ]
    for i in range(16, 41):
        typ = ["pump", "gearbox", "compressor", "conveyor"][i % 4]
        assets.append({
            "id": f"A-{i:03d}",
            "name": f"{typ.title()} {i}",
            "asset_type": typ,
            "location": ["Process Unit A", "Process Unit B", "Utility", "Material Handling"][i % 4],
            "criticality": ["medium", "high", "critical", "low"][i % 4],
            "manufacturer": "Generic",
            "model": "Model-X",
            "install_date": "2020-01-01",
            "rated_power_kw": 50,
            "expected_mtbf_hours": 15000
        })
    with open(DATA_DIR / "assets.json", "w") as f:
        json.dump(assets, f, indent=2)
    return [a["id"] for a in assets]

def seed_failure_modes():
    modes = [
        {"asset_type": "pump", "failure_mode": "Outer race bearing wear", "cause": "Fatigue / contamination", "typical_task": "Replace bearing set, check lubrication and seals", "typical_parts": "Bearing kit (SKF 6310 or equiv), seal kit, oil", "urgency_base": "high", "avg_repair_hours": 4.0, "downtime_cost_per_hour": 2500},
        {"asset_type": "pump", "failure_mode": "Inner race bearing wear", "cause": "Fatigue", "typical_task": "Replace bearing set", "typical_parts": "Bearing kit, seals", "urgency_base": "high", "avg_repair_hours": 4.0, "downtime_cost_per_hour": 2500},
        {"asset_type": "pump", "failure_mode": "Impeller imbalance", "cause": "Erosion / buildup", "typical_task": "Clean or replace impeller, rebalance", "typical_parts": "Impeller, gaskets, fasteners", "urgency_base": "medium", "avg_repair_hours": 6.0, "downtime_cost_per_hour": 2500},
        {"asset_type": "pump", "failure_mode": "Misalignment", "cause": "Installation / thermal growth", "typical_task": "Realign coupling, check soft foot", "typical_parts": "Shims, coupling elements", "urgency_base": "medium", "avg_repair_hours": 3.0, "downtime_cost_per_hour": 2500},
        {"asset_type": "pump", "failure_mode": "Cavitation", "cause": "NPSH insufficient", "typical_task": "Inspect suction conditions, adjust operating point", "typical_parts": "None immediate", "urgency_base": "medium", "avg_repair_hours": 2.0, "downtime_cost_per_hour": 2500},
        {"asset_type": "gearbox", "failure_mode": "Tooth wear", "cause": "Lubrication failure / overload", "typical_task": "Inspect gears, change oil, replace if pitting severe", "typical_parts": "Oil, filter, possible gear set", "urgency_base": "high", "avg_repair_hours": 8.0, "downtime_cost_per_hour": 1800},
        {"asset_type": "gearbox", "failure_mode": "Bearing failure", "cause": "Contamination", "typical_task": "Replace bearings, flush and refill oil", "typical_parts": "Bearing kit, oil, seals", "urgency_base": "high", "avg_repair_hours": 6.0, "downtime_cost_per_hour": 1800},
        {"asset_type": "compressor", "failure_mode": "Valve leakage", "cause": "Wear / carbon buildup", "typical_task": "Replace valves, inspect cylinder", "typical_parts": "Valve kit", "urgency_base": "high", "avg_repair_hours": 5.0, "downtime_cost_per_hour": 3000},
        {"asset_type": "compressor", "failure_mode": "Bearing wear", "cause": "Fatigue", "typical_task": "Replace main bearings", "typical_parts": "Bearing kit, oil", "urgency_base": "critical", "avg_repair_hours": 10.0, "downtime_cost_per_hour": 3000},
        {"asset_type": "conveyor", "failure_mode": "Belt tracking issue", "cause": "Misalignment / wear", "typical_task": "Adjust tracking, inspect and replace rollers as needed", "typical_parts": "Belt sections, rollers", "urgency_base": "medium", "avg_repair_hours": 4.0, "downtime_cost_per_hour": 800},
        {"asset_type": "conveyor", "failure_mode": "Motor overload", "cause": "Mechanical bind / jam", "typical_task": "Clear jam, inspect drive train", "typical_parts": "None", "urgency_base": "medium", "avg_repair_hours": 2.0, "downtime_cost_per_hour": 800},
    ]
    with open(DATA_DIR / "failure_modes.json", "w") as f:
        json.dump(modes, f, indent=2)

def generate_signals(asset_ids, days=90):
    start = datetime.now() - timedelta(days=days)
    timestamps = pd.date_range(start, periods=days*24, freq="h")
    
    dfs = []
    for asset_id in asset_ids:
        base_vib = 2.5 if asset_id.startswith("P-") or asset_id.startswith("A-") else 1.8
        base_temp = 45.0
        base_current = 25.0
        
        vib_rms = base_vib + np.random.normal(0, 0.15, len(timestamps))
        kurt = 3.0 + np.random.normal(0, 0.3, len(timestamps))
        temp = base_temp + np.random.normal(0, 2, len(timestamps))
        current = base_current + np.random.normal(0, 1.5, len(timestamps))
        load = 60 + np.random.normal(0, 10, len(timestamps))
        runtime = np.arange(len(timestamps)) * 1.0
        sensor = np.array(["ok"] * len(timestamps))
        
        # P-204 outer-race wear drift after day 60
        if asset_id == "P-204":
            days_in = np.arange(len(timestamps)) / 24.0
            drift_mask = days_in > 60
            drift = np.maximum(0, (days_in - 60) * 0.08)
            vib_rms[drift_mask] += drift[drift_mask]
            kurt[drift_mask] += drift[drift_mask] * 1.5
            temp[drift_mask] += drift[drift_mask] * 0.8
        
        # Occasional flatline sensors on other assets
        flat_idx = np.random.choice(len(timestamps), size=int(0.001 * len(timestamps)), replace=False)
        if asset_id != "P-204":
            vib_rms[flat_idx] = 0.1
            kurt[flat_idx] = 0.5
            sensor[flat_idx] = "flatline"
        
        df = pd.DataFrame({
            "asset_id": asset_id,
            "timestamp": timestamps,
            "vibration_rms": np.round(vib_rms, 3),
            "vibration_kurtosis": np.round(kurt, 2),
            "temperature_c": np.round(temp, 1),
            "current_a": np.round(current, 1),
            "runtime_hours": runtime,
            "load_pct": np.round(load, 1),
            "sensor_status": sensor
        })
        dfs.append(df)
    
    all_signals = pd.concat(dfs, ignore_index=True)
    all_signals.to_csv(DATA_DIR / "signals.csv", index=False)
    print(f"Seeded {len(all_signals)} signal rows to signals.csv")

if __name__ == "__main__":
    asset_ids = seed_assets()
    seed_failure_modes()
    generate_signals(asset_ids)
    print("Seeding complete. Files in", DATA_DIR)
