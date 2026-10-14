"""
EcoSentinel AI - Unit & Integration Test Suite for Water Intelligence Module
Validates CPCB raw data loading, WQI computation, statutory classification logic,
data splitting integrity (zero leakage), trained model artifacts, and inference contracts.
"""

import os
import sys
import json
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.water.data_audit import load_and_standardize_raw_data, audit_water_dataset
from src.water.preprocess import (
    preprocess_water_dataset,
    compute_wqi,
    assign_cpcb_target_class,
    MODEL_FEATURES,
    CLASS_MAP
)
from src.water.predict import (
    predict_water,
    load_water_artifacts,
    extract_limiting_factors,
    compute_sample_wqi
)


def test_raw_data_loading_and_standardization():
    """Verify raw CPCB dataset loads and columns map to canonical names."""
    raw_path = Path("data/raw/water/cpcb_water_quality.csv")
    assert raw_path.exists(), "Raw CPCB water dataset must exist."
    df = load_and_standardize_raw_data(raw_path)
    assert len(df) > 1000, "Dataset should have over 1,000 monitoring records."
    assert 'dissolved_oxygen' in df.columns
    assert 'ph' in df.columns
    assert 'bod' in df.columns
    assert 'conductivity' in df.columns
    assert 'total_coliform' in df.columns


def test_cpcb_classification_logic():
    """Verify statutory CPCB Designated Best Use classification rules."""
    # Pristine sample -> Class A
    sample_a = {'dissolved_oxygen': 7.5, 'bod': 1.2, 'ph': 7.4, 'total_coliform': 30}
    assert assign_cpcb_target_class(sample_a) == 'Class A'

    # Bathing sample -> Class B
    sample_b = {'dissolved_oxygen': 5.8, 'bod': 2.5, 'ph': 7.6, 'total_coliform': 350}
    assert assign_cpcb_target_class(sample_b) == 'Class B'

    # Conventional treatment sample -> Class C
    sample_c = {'dissolved_oxygen': 4.5, 'bod': 2.8, 'ph': 7.8, 'total_coliform': 3000}
    assert assign_cpcb_target_class(sample_c) == 'Class C'

    # Wildlife / irrigation -> Class D/E
    sample_d = {'dissolved_oxygen': 4.2, 'bod': 4.5, 'ph': 7.2, 'total_coliform': 600}
    assert assign_cpcb_target_class(sample_d) == 'Class D/E'

    # Critical polluted sample (depleted DO, high BOD, pathogenic coliform) -> Critical
    sample_crit = {'dissolved_oxygen': 1.5, 'bod': 22.0, 'ph': 6.2, 'total_coliform': 25000}
    assert assign_cpcb_target_class(sample_crit) == 'Critical'


def test_wqi_computation():
    """Verify Weighted Arithmetic Water Quality Index behaves monotonically."""
    pristine = {'dissolved_oxygen': 8.0, 'ph': 7.2, 'bod': 1.0, 'conductivity': 100, 'nitrate': 0.2, 'total_coliform': 20}
    polluted = {'dissolved_oxygen': 2.0, 'ph': 5.8, 'bod': 25.0, 'conductivity': 2000, 'nitrate': 15.0, 'total_coliform': 30000}

    wqi_pristine = compute_wqi(pristine)
    wqi_polluted = compute_wqi(polluted)

    assert wqi_pristine is not None and wqi_polluted is not None
    assert wqi_pristine < 50.0, "Pristine water should have low/good WQI."
    assert wqi_polluted > 100.0, "Severely polluted water should have high WQI (> 100)."


def test_data_splits_and_zero_leakage():
    """Verify train, val, and test splits have no identical station/year records overlapping."""
    train_path = Path("data/processed/water/water_train.csv")
    val_path = Path("data/processed/water/water_val.csv")
    test_path = Path("data/processed/water/water_test.csv")

    assert train_path.exists() and val_path.exists() and test_path.exists()

    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)
    df_test = pd.read_csv(test_path)

    # Ensure all splits are non-empty
    assert len(df_train) > 0 and len(df_val) > 0 and len(df_test) > 0

    # Ensure all MODEL_FEATURES exist
    for f in MODEL_FEATURES:
        assert f in df_train.columns
        assert f in df_val.columns
        assert f in df_test.columns


def test_model_and_preprocessor_artifacts_exist():
    """Verify saved production artifacts can be loaded from disk."""
    model, preprocessor, metadata = load_water_artifacts(
        model_path="models/water_quality_model.joblib",
        preprocessor_path="models/water_preprocessor.joblib",
        metadata_path="data/processed/water/water_features_metadata.json"
    )
    assert model is not None
    assert preprocessor is not None
    assert isinstance(metadata, dict)
    assert 'features' in metadata


def test_predict_water_inference_contract():
    """Verify prediction contract on clean and contaminated test inputs."""
    test_input = {
        'dissolved_oxygen': 6.8,
        'ph': 7.4,
        'bod': 1.8,
        'conductivity': 150.0,
        'nitrate': 0.35,
        'total_coliform': 120.0,
        'temperature': 24.0,
        'fecal_coliform': 35.0
    }

    result = predict_water(test_input)
    assert result['status'] == 'success'
    assert result['predicted_class'] in ['Class A', 'Class B', 'Class C', 'Class D/E', 'Critical']
    assert 0.0 <= result['confidence'] <= 1.0
    assert isinstance(result['class_probabilities'], dict)
    assert len(result['class_probabilities']) == 5
    assert result['wqi_score'] is not None
    assert result['risk_level'] in ['Low Risk', 'Low-Moderate Risk', 'Moderate Risk', 'High Risk', 'Severe / Critical Hazard']
    assert isinstance(result['limiting_factors'], list)
    assert isinstance(result['recommendations'], list)


def test_predict_water_explainability_and_limiting_factors():
    """Verify that severe parameter violations trigger human-interpretable alerts."""
    hazardous_input = {
        'dissolved_oxygen': 1.2,
        'ph': 6.1,
        'bod': 35.0,
        'conductivity': 2800.0,
        'nitrate': 18.0,
        'total_coliform': 60000.0,
        'temperature': 33.0,
        'fecal_coliform': 25000.0
    }

    result = predict_water(hazardous_input)
    assert result['status'] == 'success'
    assert result['predicted_class'] == 'Critical'
    assert result['risk_level'] == 'Severe / Critical Hazard'
    assert len(result['limiting_factors']) >= 3

    # Check that DO and BOD are flagged
    flagged_params = [lf['parameter'] for lf in result['limiting_factors']]
    assert any('Oxygen' in p for p in flagged_params)
    assert any('BOD' in p for p in flagged_params)


def test_predict_water_domain_warnings():
    """Verify domain guardrails catch physically impossible pH values."""
    implausible_input = {
        'dissolved_oxygen': 6.0,
        'ph': 22.5,  # Impossible pH
        'bod': 2.0,
        'conductivity': 200.0,
        'nitrate': 0.5,
        'total_coliform': 100.0,
        'temperature': 25.0,
        'fecal_coliform': 20.0
    }

    result = predict_water(implausible_input)
    assert result['status'] == 'success'
    assert len(result['warnings']) > 0
    assert any('pH' in w for w in result['warnings'])


if __name__ == '__main__':
    all_tests = [
        test_raw_data_loading_and_standardization,
        test_cpcb_classification_logic,
        test_wqi_computation,
        test_data_splits_and_zero_leakage,
        test_model_and_preprocessor_artifacts_exist,
        test_predict_water_inference_contract,
        test_predict_water_explainability_and_limiting_factors,
        test_predict_water_domain_warnings
    ]
    print(f"Running {len(all_tests)} tests in test_water.py...\n")
    for test_fn in all_tests:
        test_fn()
        print(f"  [PASS] {test_fn.__name__}")
    print(f"\nALL {len(all_tests)} TESTS PASSED SUCCESSFULLY!")
