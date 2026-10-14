"""
EcoSentinel AI - Water Data Preprocessing Module
Cleans raw CPCB monitoring data, handles missing values and sentinel strings,
derives statutory CPCB Designated Best Use classification labels and continuous WQI metrics,
executes strict non-leaking train/val/test splits, and exports fitted preprocessing pipelines.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline

# Standardized feature schema
MODEL_FEATURES = [
    'dissolved_oxygen',
    'ph',
    'bod',
    'conductivity',
    'nitrate',
    'total_coliform',
    'temperature',
    'fecal_coliform'
]

# Canonical CPCB target class mapping
CLASS_MAP = {
    0: 'Class A',       # Pristine drinking water source (disinfection only)
    1: 'Class B',       # Outdoor bathing (organised)
    2: 'Class C',       # Drinking water source after conventional treatment
    3: 'Class D/E',     # Wildlife propagation, fisheries & irrigation
    4: 'Critical'       # Polluted / Non-compliant (severe contamination)
}

CLASS_TO_INT = {v: k for k, v in CLASS_MAP.items()}

CLASS_DESCRIPTIONS = {
    'Class A': 'Pristine drinking water source (disinfection only)',
    'Class B': 'Outdoor bathing (organized)',
    'Class C': 'Drinking water source after conventional treatment',
    'Class D/E': 'Wildlife propagation, fisheries & irrigation',
    'Critical': 'Polluted / Non-compliant (severe contamination)'
}

# Environmental risk levels mapped to CPCB classes
RISK_LEVEL_MAP = {
    'Class A': 'Low Risk',
    'Class B': 'Low-Moderate Risk',
    'Class C': 'Moderate Risk',
    'Class D/E': 'High Risk',
    'Critical': 'Severe / Critical Hazard'
}

# Raw column mapping
RAW_COLUMN_MAP = {
    'STATION CODE': 'station_code',
    'LOCATIONS': 'location',
    'STATE': 'state',
    'Temp': 'temperature',
    'D.O. (mg/l)': 'dissolved_oxygen',
    'PH': 'ph',
    'B.O.D. (mg/l)': 'bod',
    'NITRATENAN N+ NITRITENANN (mg/l)': 'nitrate',
    'FECAL COLIFORM (MPN/100ml)': 'fecal_coliform',
    'TOTAL COLIFORM (MPN/100ml)Mean': 'total_coliform',
    'year': 'year'
}


def compute_wqi(row):
    """
    Computes Weighted Arithmetic Water Quality Index (WA-WQI) based on CPCB standards.
    WQI < 25: Excellent, 26-50: Good, 51-75: Poor, 76-100: Very Poor, >100: Severely Polluted.
    """
    # Standards (Si) and ideal values (Vi)
    standards = {
        'dissolved_oxygen': {'s': 5.0, 'v_ideal': 14.6, 'unit_weight': 0.3723},
        'ph': {'s': 8.5, 'v_ideal': 7.0, 'unit_weight': 0.1112},
        'bod': {'s': 5.0, 'v_ideal': 0.0, 'unit_weight': 0.3723},
        'conductivity': {'s': 1000.0, 'v_ideal': 0.0, 'unit_weight': 0.0037},
        'nitrate': {'s': 45.0, 'v_ideal': 0.0, 'unit_weight': 0.0744},
        'total_coliform': {'s': 500.0, 'v_ideal': 0.0, 'unit_weight': 0.0660}
    }
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for param, meta in standards.items():
        val = row.get(param)
        if pd.notna(val) and val >= 0:
            s = meta['s']
            v_ideal = meta['v_ideal']
            w = meta['unit_weight']
            
            # Quality rating qi
            if param == 'ph':
                qi = (abs(val - v_ideal) / (8.5 - 7.0)) * 100.0
            elif param == 'dissolved_oxygen':
                qi = (abs(val - v_ideal) / (14.6 - 5.0)) * 100.0
            else:
                qi = (abs(val - v_ideal) / s) * 100.0
                
            qi = max(0.0, min(500.0, qi))
            weighted_sum += qi * w
            total_weight += w
            
    if total_weight > 0:
        return round(float(weighted_sum / total_weight), 2)
    return np.nan


def assign_cpcb_target_class(row):
    """
    Assigns statutory CPCB Designated Best Use class based on key chemical and microbiological criteria.
    Class A: DO >= 6.0, BOD <= 2.0, pH 6.5-8.5, Coliform <= 50
    Class B: DO >= 5.0, BOD <= 3.0, pH 6.5-8.5, Coliform <= 500
    Class C: DO >= 4.0, BOD <= 3.0, pH 6.0-9.0, Coliform <= 5000
    Class D/E: DO >= 4.0, pH 6.0-8.5, BOD <= 6.0
    Critical: Violates standards (DO < 4.0, BOD > 3.0, Coliform > 5000)
    """
    do = row.get('dissolved_oxygen')
    bod = row.get('bod')
    ph = row.get('ph')
    tc = row.get('total_coliform')
    
    if pd.isna(do) or pd.isna(bod) or pd.isna(ph):
        return np.nan
        
    # Check Class A
    if do >= 6.0 and bod <= 2.0 and (6.5 <= ph <= 8.5) and (pd.isna(tc) or tc <= 50):
        return 'Class A'
    # Check Class B
    elif do >= 5.0 and bod <= 3.0 and (6.5 <= ph <= 8.5) and (pd.isna(tc) or tc <= 500):
        return 'Class B'
    # Check Class C
    elif do >= 4.0 and bod <= 3.0 and (6.0 <= ph <= 9.0) and (pd.isna(tc) or tc <= 5000):
        return 'Class C'
    # Check Class D/E
    elif do >= 4.0 and (6.0 <= ph <= 8.5) and bod <= 6.0:
        return 'Class D/E'
    # Critical / Polluted
    else:
        return 'Critical'


def preprocess_water_dataset(
    raw_csv_path="data/raw/water/cpcb_water_quality.csv",
    output_dir="data/processed/water",
    model_dir="models",
    split_strategy="stratified",  # 'stratified' or 'temporal'
    test_size=0.15,
    val_size=0.15,
    random_state=42
):
    """
    End-to-end preprocessing pipeline for CPCB surface water quality dataset.
    Cleans raw data, engineers CPCB targets & WQI metrics, partitions splits,
    fits learned transformers on train data only, and serializes artifacts.
    """
    raw_path = Path(raw_csv_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw water dataset at {raw_path}")

    output_dir = Path(output_dir)
    model_dir = Path(model_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60, flush=True)
    print("ECOSENTINEL AI - WATER DATA PREPROCESSING PIPELINE", flush=True)
    print("=" * 60, flush=True)

    df_raw = pd.read_csv(raw_path, encoding='latin1')
    
    # 1. Standardize column names
    rename_dict = {}
    for col in df_raw.columns:
        c_strip = col.strip()
        for raw_k, clean_v in RAW_COLUMN_MAP.items():
            if raw_k in c_strip or clean_v in c_strip.lower():
                rename_dict[col] = clean_v
                break
        if col not in rename_dict:
            if 'conduct' in c_strip.lower():
                rename_dict[col] = 'conductivity'
            elif 'nitrat' in c_strip.lower():
                rename_dict[col] = 'nitrate'
            elif 'fecal' in c_strip.lower():
                rename_dict[col] = 'fecal_coliform'
            elif 'total coliform' in c_strip.lower():
                rename_dict[col] = 'total_coliform'
            elif 'd.o' in c_strip.lower():
                rename_dict[col] = 'dissolved_oxygen'
            elif 'b.o.d' in c_strip.lower():
                rename_dict[col] = 'bod'
            elif 'temp' in c_strip.lower():
                rename_dict[col] = 'temperature'

    df = df_raw.rename(columns=rename_dict).copy()

    # 2. Convert all numeric features
    for col in MODEL_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert metadata
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')

    # 3. Handle physical domain constraints
    # pH must be in [0, 14]
    df.loc[(df['ph'] < 0) | (df['ph'] > 14), 'ph'] = np.nan
    # Concentrations cannot be negative
    for col in ['dissolved_oxygen', 'bod', 'conductivity', 'nitrate', 'fecal_coliform', 'total_coliform']:
        if col in df.columns:
            df.loc[df[col] < 0, col] = np.nan

    # 4. Generate CPCB Target Labels & WQI
    df['target_class'] = df.apply(assign_cpcb_target_class, axis=1)
    df['target_label'] = df['target_class'].map(CLASS_TO_INT)
    df['wqi'] = df.apply(compute_wqi, axis=1)

    # Filter out unlabelable records where core parameters (DO, BOD, pH) were missing
    clean_df = df.dropna(subset=['target_class']).copy()
    clean_df['target_label'] = clean_df['target_label'].astype(int)

    print(f"Valid Labeled Observations: {len(clean_df)} / {len(df_raw)} raw rows", flush=True)
    print("CPCB Class Distribution:")
    for cls_name, count in clean_df['target_class'].value_counts().items():
        pct = (count / len(clean_df)) * 100
        print(f"  - {cls_name:12s}: {count:4d} ({pct:5.1f}%)", flush=True)

    # 5. Dataset Splitting
    if split_strategy == "temporal" and 'year' in clean_df.columns and clean_df['year'].notnull().all():
        print("Using Longitudinal Temporal Splitting (Train: <=2011, Val: 2012, Test: >=2013)...", flush=True)
        train_df = clean_df[clean_df['year'] <= 2011].copy()
        val_df = clean_df[clean_df['year'] == 2012].copy()
        test_df = clean_df[clean_df['year'] >= 2013].copy()
    else:
        print(f"Using Stratified Splitting (Train: {int((1-test_size-val_size)*100)}%, Val: {int(val_size*100)}%, Test: {int(test_size*100)}%)...", flush=True)
        train_df, temp_df = train_test_split(
            clean_df,
            test_size=(test_size + val_size),
            random_state=random_state,
            stratify=clean_df['target_label']
        )
        val_rel_ratio = val_size / (test_size + val_size)
        val_df, test_df = train_test_split(
            temp_df,
            test_size=(1.0 - val_rel_ratio),
            random_state=random_state,
            stratify=temp_df['target_label']
        )

    print(f"Split sizes: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}", flush=True)

    # 6. Fit Learned Preprocessing Pipeline (STRICTLY ON TRAIN SPLIT ONLY!)
    preprocessor = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', RobustScaler())  # Robust to skewed coliform and conductivity distributions
    ])

    X_train_raw = train_df[MODEL_FEATURES]
    preprocessor.fit(X_train_raw)
    print("Preprocessing pipeline (Median Imputer + RobustScaler) fitted strictly on training data.", flush=True)

    # 7. Save Processed Datasets
    train_path = output_dir / "water_train.csv"
    val_path = output_dir / "water_val.csv"
    test_path = output_dir / "water_test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    # 8. Save Preprocessor Artifact
    preprocessor_artifact_path = model_dir / "water_preprocessor.joblib"
    joblib.dump(preprocessor, preprocessor_artifact_path)
    print(f"Saved preprocessor artifact to: {preprocessor_artifact_path}", flush=True)

    # 9. Compute and Save Feature Metadata
    train_medians = preprocessor.named_steps['imputer'].statistics_
    feature_metadata = {
        'features': MODEL_FEATURES,
        'feature_count': len(MODEL_FEATURES),
        'class_map': CLASS_MAP,
        'class_descriptions': CLASS_DESCRIPTIONS,
        'risk_level_map': RISK_LEVEL_MAP,
        'feature_medians': {f: float(m) for f, m in zip(MODEL_FEATURES, train_medians)},
        'feature_ranges': {
            f: {
                'min': float(train_df[f].min()) if train_df[f].notnull().any() else 0.0,
                'max': float(train_df[f].max()) if train_df[f].notnull().any() else 100.0,
                'mean': float(train_df[f].mean()) if train_df[f].notnull().any() else 0.0,
                'std': float(train_df[f].std()) if train_df[f].notnull().any() else 1.0,
            }
            for f in MODEL_FEATURES
        },
        'split_summary': {
            'train_size': len(train_df),
            'val_size': len(val_df),
            'test_size': len(test_df),
            'strategy': split_strategy
        }
    }

    metadata_path = output_dir / "water_features_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(feature_metadata, f, indent=4)
    print(f"Saved feature metadata schema to: {metadata_path}", flush=True)
    print("=" * 60, flush=True)

    return {
        'train_df': train_df,
        'val_df': val_df,
        'test_df': test_df,
        'preprocessor': preprocessor,
        'metadata': feature_metadata
    }


if __name__ == "__main__":
    preprocess_water_dataset()
