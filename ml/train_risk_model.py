"""
Project ASTRA - AI-Powered Multi-Agent Women's Travel Safety Assistant
Phase-1 Review 1 (50% Implementation Milestone)
CHRIST (Deemed to be University), Department of CSE
Team: Kasine RS (Backend/ML Lead) & Darshan R (Android/Client Lead)

Agent 1: Predictive Risk Scoring Engine
Training Pipeline for Multi-Class Telemetry Classification (Safe, Moderate, Critical)
"""

import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


def generate_synthetic_telemetry(n_samples: int = 6000, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic urban safety dataset for travel telemetry risk scoring.

    Features:
      - route_deviation_meters (float): Distance off the expected route polyline.
      - stop_duration_seconds (float): Unscheduled dwell/stop duration.
      - speed_kmh (float): Current vehicle speed.
      - hour_of_day (int): 0-23 clock hour.

    Target:
      - 0: Safe
      - 1: Moderate
      - 2: Critical
    """
    np.random.seed(random_state)

    # 1. Safe Scenario Samples (~50% of dataset)
    # Daytime moving traffic, slight GPS drift (< 30m), normal traffic signal pauses (< 120s)
    n_safe = int(n_samples * 0.50)
    safe_deviation = np.random.exponential(scale=8.0, size=n_safe).clip(0, 35)
    safe_speed = np.random.uniform(15, 65, size=n_safe)
    safe_stops = np.zeros(n_safe)

    # Some safe samples represent normal signal stops (speed=0, stop < 120s)
    signal_stop_indices = np.random.choice(n_safe, size=int(n_safe * 0.35), replace=False)
    safe_speed[signal_stop_indices] = np.random.uniform(0, 5, size=len(signal_stop_indices))
    safe_stops[signal_stop_indices] = np.random.uniform(10, 110, size=len(signal_stop_indices))
    safe_hours = np.random.choice(range(6, 22), size=n_safe)  # Daytime/early evening

    df_safe = pd.DataFrame({
        "route_deviation_meters": safe_deviation,
        "stop_duration_seconds": safe_stops,
        "speed_kmh": safe_speed,
        "hour_of_day": safe_hours,
        "risk_code": 0
    })

    # 2. Moderate Scenario Samples (~25% of dataset)
    # Detours (40-150m), moderate delays/dwelling (120-300s), late evening hours or unusual slow crawls
    n_mod = int(n_samples * 0.25)
    mod_deviation = np.random.uniform(30, 160, size=n_mod)
    mod_speed = np.random.uniform(0, 25, size=n_mod)
    mod_stops = np.random.uniform(90, 300, size=n_mod)
    # Moderate hours: late evening (20-23), early morning (4-6), or daytime with noticeable detour
    mod_hours = np.random.choice(
        [4, 5, 12, 13, 14, 20, 21, 22, 23],
        size=n_mod,
        p=[0.05, 0.05, 0.1, 0.1, 0.1, 0.2, 0.2, 0.1, 0.1]
    )

    df_mod = pd.DataFrame({
        "route_deviation_meters": mod_deviation,
        "stop_duration_seconds": mod_stops,
        "speed_kmh": mod_speed,
        "hour_of_day": mod_hours,
        "risk_code": 1
    })

    # 3. Critical Scenario Samples (~25% of dataset)
    # Severe off-route deviation (> 200m), prolonged stoppage (> 300s), late night / midnight hours (22:00 - 05:00)
    n_crit = int(n_samples * 0.25)
    crit_deviation = np.random.uniform(180, 1200, size=n_crit)
    crit_stops = np.random.uniform(250, 1800, size=n_crit)
    crit_speed = np.random.uniform(0, 15, size=n_crit)
    # 70% of critical incidents occur late night/midnight
    night_crit_indices = np.random.choice(n_crit, size=int(n_crit * 0.75), replace=False)
    crit_hours = np.random.choice(range(6, 22), size=n_crit)
    crit_hours[night_crit_indices] = np.random.choice([22, 23, 0, 1, 2, 3, 4, 5], size=len(night_crit_indices))

    # In critical night halts, vehicle is typically completely stationary
    crit_speed[night_crit_indices] = np.random.uniform(0, 3, size=len(night_crit_indices))

    df_crit = pd.DataFrame({
        "route_deviation_meters": crit_deviation,
        "stop_duration_seconds": crit_stops,
        "speed_kmh": crit_speed,
        "hour_of_day": crit_hours,
        "risk_code": 2
    })

    # Combine and shuffle
    df = pd.concat([df_safe, df_mod, df_crit], ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df


def train_and_export_model(
    output_path: str = "ml/risk_model.pkl",
    random_state: int = 42
) -> RandomForestClassifier:
    """
    Trains the multi-class RandomForest risk model, evaluates performance,
    and serializes the artifact for FastAPI inference.
    """
    print("=" * 60)
    print("Project ASTRA - Training Agent 1 (Predictive Risk Scoring)")
    print("=" * 60)

    # 1. Generate Dataset
    print("[1/4] Generating synthetic urban travel safety telemetry dataset...")
    df = generate_synthetic_telemetry(n_samples=6000, random_state=random_state)
    print(f"      Generated {len(df)} telemetry samples.")
    print("      Class Distribution:")
    for code, label in {0: "Safe", 1: "Moderate", 2: "Critical"}.items():
        count = (df['risk_code'] == code).sum()
        print(f"        - {label} ({code}): {count} ({count/len(df)*100:.1f}%)")

    # 2. Split Features and Target
    feature_cols = [
        "route_deviation_meters",
        "stop_duration_seconds",
        "speed_kmh",
        "hour_of_day"
    ]
    X = df[feature_cols]
    y = df["risk_code"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    # 3. Model Training
    print("\n[2/4] Training RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # 4. Evaluation
    print("\n[3/4] Evaluating Model Performance on Held-Out Test Set...")
    y_pred = model.predict(X_test)
    target_names = ["Safe (0)", "Moderate (1)", "Critical (2)"]
    report = classification_report(y_test, y_pred, target_names=target_names)
    print("\nClassification Report:")
    print(report)

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(cm)

    # Feature Importances
    print("\nFeature Importances:")
    for feat, imp in zip(feature_cols, model.feature_importances_):
        print(f"  - {feat:25s}: {imp:.4f} ({imp*100:.1f}%)")

    # Verify Baseline Scenarios
    print("\n[4/4] Validating Project ASTRA Test Scenarios:")
    test_cases = [
        {"name": "Scenario 1 (Daytime Commute)", "data": [10.0, 0.0, 45.0, 14], "expected": 0},
        {"name": "Scenario 2 (Traffic Signal Pause)", "data": [20.0, 90.0, 0.0, 18], "expected": 0},
        {"name": "Scenario 3 (Midnight Off-Route Halt)", "data": [550.0, 400.0, 0.0, 23], "expected": 2},
    ]

    labels_map = {0: "Safe", 1: "Moderate", 2: "Critical"}
    for tc in test_cases:
        sample = np.array([tc["data"]])
        pred = int(model.predict(sample)[0])
        probs = model.predict_proba(sample)[0]
        conf = probs[pred]
        status_sym = "PASS" if pred == tc["expected"] else "FAIL"
        print(f"  [{status_sym}] {tc['name']}")
        print(f"         Input: {tc['data']}")
        print(f"         Output: {labels_map[pred]} (code {pred}), Confidence: {conf:.2f}")

    # Export Model Artifact
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    artifact_payload = {
        "model": model,
        "feature_names": feature_cols,
        "classes": [0, 1, 2],
        "class_labels": {0: "Safe", 1: "Moderate", 2: "Critical"},
        "version": "1.0.0-phase1"
    }
    joblib.dump(artifact_payload, out_file)
    print(f"\nModel artifact successfully exported to: {out_file.resolve()}")
    print("=" * 60)
    return model


if __name__ == "__main__":
    # Resolve project root relative to this script
    script_dir = Path(__file__).resolve().parent
    model_output = script_dir / "risk_model.pkl"
    train_and_export_model(output_path=str(model_output))
