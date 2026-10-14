"""
EcoSentinel AI - Water Model Inference Module
Loads trained CPCB water classification model and preprocessor artifacts,
validates user-supplied physicochemical measurements, generates class predictions,
confidence distributions, WQI scores, environmental risk levels, and explainable limiting factors.
Never trains during prediction; handles missing artifacts gracefully.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

# Global caches to avoid reloading artifacts on repeated calls
_MODEL_CACHE = {}
_PREPROCESSOR_CACHE = {}
_METADATA_CACHE = {}

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

CLASS_MAP = {
    0: 'Class A',
    1: 'Class B',
    2: 'Class C',
    3: 'Class D/E',
    4: 'Critical'
}

CLASS_DESCRIPTIONS = {
    'Class A': 'Pristine Drinking Water Source (Safe after disinfection only)',
    'Class B': 'Outdoor Bathing & Recreational Water Body',
    'Class C': 'Drinking Water Source after Conventional Treatment & Disinfection',
    'Class D/E': 'Propagation of Wildlife, Fisheries & Agricultural Irrigation',
    'Critical': 'Polluted / Non-Compliant (Severe Ecological & Public Health Hazard)'
}

RISK_LEVEL_MAP = {
    'Class A': 'Low Risk',
    'Class B': 'Low-Moderate Risk',
    'Class C': 'Moderate Risk',
    'Class D/E': 'High Risk',
    'Critical': 'Severe / Critical Hazard'
}

# Statutory CPCB Permissible Thresholds for Explainability
CPCB_THRESHOLDS = {
    'dissolved_oxygen': {'min_clean': 6.0, 'min_bathing': 5.0, 'min_treated': 4.0, 'unit': 'mg/L'},
    'bod': {'max_pristine': 2.0, 'max_bathing': 3.0, 'max_wildlife': 6.0, 'unit': 'mg/L'},
    'ph': {'min': 6.5, 'max': 8.5, 'unit': 'pH units'},
    'total_coliform': {'max_pristine': 50, 'max_bathing': 500, 'max_treated': 5000, 'unit': 'MPN/100ml'},
    'nitrate': {'max_potable': 45.0, 'unit': 'mg/L'},
    'conductivity': {'max_freshwater': 2250.0, 'unit': 'µmhos/cm'}
}


def load_water_artifacts(
    model_path="models/water_quality_model.joblib",
    preprocessor_path="models/water_preprocessor.joblib",
    metadata_path="data/processed/water/water_features_metadata.json"
):
    """
    Loads and caches model, preprocessor, and schema metadata.
    """
    model_path = Path(model_path)
    preprocessor_path = Path(preprocessor_path)
    metadata_path = Path(metadata_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained water model artifact not found at '{model_path}'. "
            "Please run model training first before running inference."
        )

    if not preprocessor_path.exists():
        raise FileNotFoundError(
            f"Fitted water preprocessor artifact not found at '{preprocessor_path}'. "
            "Please run preprocessing first."
        )

    model_key = str(model_path.resolve())
    if model_key not in _MODEL_CACHE:
        _MODEL_CACHE[model_key] = joblib.load(model_path)

    prep_key = str(preprocessor_path.resolve())
    if prep_key not in _PREPROCESSOR_CACHE:
        _PREPROCESSOR_CACHE[prep_key] = joblib.load(preprocessor_path)

    meta_key = str(metadata_path.resolve())
    if meta_key not in _METADATA_CACHE:
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                _METADATA_CACHE[meta_key] = json.load(f)
        else:
            _METADATA_CACHE[meta_key] = {}

    return _MODEL_CACHE[model_key], _PREPROCESSOR_CACHE[prep_key], _METADATA_CACHE[meta_key]


def compute_sample_wqi(measurements):
    """
    Computes statutory Weighted Arithmetic WQI for a measurement dictionary.
    """
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
        val = measurements.get(param)
        if val is not None and not np.isnan(val) and val >= 0:
            s = meta['s']
            v_ideal = meta['v_ideal']
            w = meta['unit_weight']
            
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
    return None


def extract_limiting_factors(measurements):
    """
    Evaluates measurements against official CPCB environmental safety limits
    to provide human-readable, transparent limiting factor explanations.
    """
    limiting_factors = []
    recommendations = []

    do = measurements.get('dissolved_oxygen')
    if do is not None:
        if do < 4.0:
            limiting_factors.append({
                'parameter': 'Dissolved Oxygen (DO)',
                'observed_value': f"{do:.2f} mg/L",
                'threshold': "< 4.0 mg/L (Critical Depletion)",
                'severity': 'Critical',
                'impact': 'Severe hypoxia threatening aquatic life, indicating heavy organic waste decomposition.'
            })
            recommendations.append("Immediate artificial aeration required; locate and intercept untreated organic discharge.")
        elif do < 5.0:
            limiting_factors.append({
                'parameter': 'Dissolved Oxygen (DO)',
                'observed_value': f"{do:.2f} mg/L",
                'threshold': "< 5.0 mg/L (Below Bathing Standard)",
                'severity': 'High',
                'impact': 'Unfit for outdoor bathing and recreational human contact.'
            })
            recommendations.append("Monitor upstream discharges and inspect storm/drain runoff.")

    bod = measurements.get('bod')
    if bod is not None:
        if bod > 6.0:
            limiting_factors.append({
                'parameter': 'Biochemical Oxygen Demand (BOD)',
                'observed_value': f"{bod:.2f} mg/L",
                'threshold': "> 6.0 mg/L (Excessive Organic Pollution)",
                'severity': 'Critical',
                'impact': 'Indicates substantial raw domestic sewage or industrial organic effluent.'
            })
            recommendations.append("Issue high environmental pollution warning; prioritize drainage inspection.")
        elif bod > 3.0:
            limiting_factors.append({
                'parameter': 'Biochemical Oxygen Demand (BOD)',
                'observed_value': f"{bod:.2f} mg/L",
                'threshold': "> 3.0 mg/L (Exceeds Bathing Limits)",
                'severity': 'Moderate',
                'impact': 'Moderately polluted water; requires biological treatment before potable use.'
            })

    ph = measurements.get('ph')
    if ph is not None:
        if ph < 6.5 or ph > 8.5:
            limiting_factors.append({
                'parameter': 'pH Level',
                'observed_value': f"{ph:.2f}",
                'threshold': "Outside 6.5 – 8.5 Permissible Range",
                'severity': 'Moderate',
                'impact': 'Corrosive or alkaline conditions, potentially caused by industrial effluents or chemical leaching.'
            })
            recommendations.append("Inspect nearby industrial facilities for neutralization compliance.")

    coliform = measurements.get('total_coliform')
    if coliform is not None:
        if coliform > 5000:
            limiting_factors.append({
                'parameter': 'Total Coliform',
                'observed_value': f"{int(coliform):,} MPN/100ml",
                'threshold': "> 5,000 MPN/100ml (Pathogenic Loading)",
                'severity': 'Critical',
                'impact': 'Extreme microbial contamination from sewage; direct human health hazard.'
            })
            recommendations.append("Alert local water authorities; issue public health boil/contact advisory.")
        elif coliform > 500:
            limiting_factors.append({
                'parameter': 'Total Coliform',
                'observed_value': f"{int(coliform):,} MPN/100ml",
                'threshold': "> 500 MPN/100ml (Exceeds Bathing Safety)",
                'severity': 'High',
                'impact': 'Microbiological counts too high for recreational swimming or bathing.'
            })

    if not recommendations:
        recommendations.append("Water meets standard outdoor criteria. Maintain regular periodic monitoring.")

    return limiting_factors, recommendations


def predict_water(
    input_data,
    model_path="models/water_quality_model.joblib",
    preprocessor_path="models/water_preprocessor.joblib",
    metadata_path="data/processed/water/water_features_metadata.json"
):
    """
    Executes inference for water quality observations.
    
    Args:
        input_data: Dict with keys matching MODEL_FEATURES, or pandas DataFrame.
        model_path: Path to trained Random Forest model artifact.
        preprocessor_path: Path to fitted scikit-learn preprocessor artifact.
        metadata_path: Path to feature metadata schema JSON.
        
    Returns:
        dict containing:
            - 'status': 'success' or error
            - 'predicted_class': CPCB class name (e.g. 'Class B')
            - 'class_description': Human-readable designation
            - 'confidence': Highest probability (0.0 - 1.0)
            - 'class_probabilities': Dict mapping each class to probability
            - 'wqi_score': Computed Water Quality Index
            - 'risk_level': Environmental risk level
            - 'limiting_factors': List of violated environmental parameters
            - 'recommendations': Actionable remediation recommendations
            - 'warnings': Domain warnings (e.g., physically implausible inputs)
    """
    try:
        model, preprocessor, metadata = load_water_artifacts(model_path, preprocessor_path, metadata_path)
    except FileNotFoundError as e:
        return {
            'status': 'error',
            'error': str(e),
            'predicted_class': None,
            'confidence': 0.0
        }

    # Convert input to DataFrame
    if isinstance(input_data, dict):
        df_input = pd.DataFrame([input_data])
    elif isinstance(input_data, pd.DataFrame):
        df_input = input_data.copy()
    else:
        return {
            'status': 'error',
            'error': "Unsupported input format. Must be dict or pandas DataFrame.",
            'predicted_class': None,
            'confidence': 0.0
        }

    warnings = []
    # Check physical constraints on first sample
    first_row = df_input.iloc[0].to_dict()
    if 'ph' in first_row and pd.notna(first_row['ph']):
        if first_row['ph'] < 0 or first_row['ph'] > 14:
            warnings.append(f"pH value {first_row['ph']} is physically outside standard aqueous scale [0, 14].")

    # Ensure all MODEL_FEATURES exist
    for f in MODEL_FEATURES:
        if f not in df_input.columns:
            # Impute missing feature with metadata median or NaN
            med_val = metadata.get('feature_medians', {}).get(f, np.nan)
            df_input[f] = med_val

    # Reorder columns exactly as expected by preprocessor
    X_raw = df_input[MODEL_FEATURES].copy()
    for f in MODEL_FEATURES:
        X_raw[f] = pd.to_numeric(X_raw[f], errors='coerce')

    # Transform through pipeline
    X_trans = preprocessor.transform(X_raw)

    # Predict
    preds = model.predict(X_trans)
    probas = model.predict_proba(X_trans)

    pred_idx = int(preds[0])
    pred_class = CLASS_MAP.get(pred_idx, f"Class_{pred_idx}")
    confidence = float(np.max(probas[0]))

    class_probs = {
        CLASS_MAP.get(i, f"Class_{i}"): round(float(probas[0][i]), 4)
        for i in range(len(CLASS_MAP))
    }

    # Environmental indicators & explainability
    wqi = compute_sample_wqi(first_row)
    limiting_factors, recommendations = extract_limiting_factors(first_row)
    risk_level = RISK_LEVEL_MAP.get(pred_class, 'Moderate Risk')

    return {
        'status': 'success',
        'predicted_class': pred_class,
        'class_description': CLASS_DESCRIPTIONS.get(pred_class, ''),
        'confidence': round(confidence, 4),
        'class_probabilities': class_probs,
        'wqi_score': wqi,
        'risk_level': risk_level,
        'limiting_factors': limiting_factors,
        'recommendations': recommendations,
        'warnings': warnings,
        'input_features': {f: first_row.get(f) for f in MODEL_FEATURES}
    }


def predict_sample_scenarios(output_json_path="outputs/predictions/water_sample_predictions.json"):
    """
    Runs inference on realistic benchmark environmental scenarios representing
    different water bodies across India, and exports predictions JSON.
    """
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scenarios = [
        {
            'scenario_name': 'Himalayan Mountain Headwater Stream',
            'location': 'Alaknanda River upstream, Uttarakhand',
            'measurements': {
                'dissolved_oxygen': 7.8,
                'ph': 7.4,
                'bod': 1.2,
                'conductivity': 95.0,
                'nitrate': 0.15,
                'total_coliform': 24.0,
                'temperature': 14.5,
                'fecal_coliform': 6.0
            }
        },
        {
            'scenario_name': 'Organized Recreational Bathing Ghat',
            'location': 'Haridwar Ganga Ghat, Uttarakhand',
            'measurements': {
                'dissolved_oxygen': 6.4,
                'ph': 7.5,
                'bod': 2.4,
                'conductivity': 180.0,
                'nitrate': 0.45,
                'total_coliform': 320.0,
                'temperature': 22.0,
                'fecal_coliform': 90.0
            }
        },
        {
            'scenario_name': 'Municipal Drinking Water Intake',
            'location': 'Kaveri River raw intake, Tamil Nadu',
            'measurements': {
                'dissolved_oxygen': 5.5,
                'ph': 7.2,
                'bod': 2.8,
                'conductivity': 380.0,
                'nitrate': 1.20,
                'total_coliform': 2400.0,
                'temperature': 28.0,
                'fecal_coliform': 450.0
            }
        },
        {
            'scenario_name': 'Agricultural Canal & Wetland',
            'location': 'Kuttanad Lake Basin, Kerala',
            'measurements': {
                'dissolved_oxygen': 4.8,
                'ph': 6.8,
                'bod': 4.5,
                'conductivity': 920.0,
                'nitrate': 3.80,
                'total_coliform': 850.0,
                'temperature': 29.5,
                'fecal_coliform': 210.0
            }
        },
        {
            'scenario_name': 'Untreated Urban Sewage & Industrial Drain Outfall',
            'location': 'Najafgarh Drain confluence / Yamuna, Delhi',
            'measurements': {
                'dissolved_oxygen': 1.2,
                'ph': 6.3,
                'bod': 28.5,
                'conductivity': 2450.0,
                'nitrate': 14.2,
                'total_coliform': 48000.0,
                'temperature': 31.0,
                'fecal_coliform': 18000.0
            }
        }
    ]

    results = []
    print("=" * 60, flush=True)
    print("ECOSENTINEL AI - WATER SAMPLE PREDICTIONS & BENCHMARKS", flush=True)
    print("=" * 60, flush=True)

    for item in scenarios:
        pred = predict_water(item['measurements'])
        summary = {
            'scenario_name': item['scenario_name'],
            'location': item['location'],
            'measurements': item['measurements'],
            'prediction': pred
        }
        results.append(summary)

        print(f"\nScenario: {item['scenario_name']} ({item['location']})")
        print(f"  -> Predicted:   {pred['predicted_class']} (Confidence: {pred['confidence']:.2%})")
        print(f"  -> Risk Level:  {pred['risk_level']} | WQI: {pred['wqi_score']}")
        print(f"  -> Description: {pred['class_description']}")
        if pred['limiting_factors']:
            print(f"  -> Violations:  {len(pred['limiting_factors'])} environmental threshold(s) flagged")
            for lf in pred['limiting_factors']:
                print(f"     * {lf['parameter']}: {lf['observed_value']} ({lf['threshold']})")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    print("\n" + "=" * 60)
    print(f"Sample prediction outputs exported to: {output_path}")
    print("=" * 60)
    return results


if __name__ == "__main__":
    predict_sample_scenarios()
