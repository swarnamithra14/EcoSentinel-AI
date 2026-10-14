"""Water Intelligence module for EcoSentinel AI."""

from src.water.data_audit import audit_water_dataset
from src.water.preprocess import preprocess_water_dataset, compute_wqi, assign_cpcb_target_class
from src.water.train import train_water_model
from src.water.predict import predict_water, load_water_artifacts, predict_sample_scenarios

__all__ = [
    'audit_water_dataset',
    'preprocess_water_dataset',
    'compute_wqi',
    'assign_cpcb_target_class',
    'train_water_model',
    'predict_water',
    'load_water_artifacts',
    'predict_sample_scenarios'
]
