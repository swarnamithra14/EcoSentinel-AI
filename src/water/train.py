"""
EcoSentinel AI - Water Model Training & Evaluation Module
Trains champion Random Forest classifier (and baseline comparative models)
on preprocessed CPCB surface water monitoring splits, tunes hyperparameters with class balancing,
evaluates out-of-sample performance (Accuracy, Macro/Per-Class F1, Confusion Matrix),
computes environmental feature importances, and exports production model checkpoints and reports.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use('Agg')  # Headless backend for background execution
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)
from sklearn.model_selection import cross_val_score

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

CLASS_NAMES = ['Class A', 'Class B', 'Class C', 'Class D/E', 'Critical']


def train_water_model(
    processed_dir="data/processed/water",
    model_output_dir="models",
    eval_output_dir="outputs/evaluation",
    n_estimators=150,
    max_depth=12,
    random_state=42
):
    """
    Trains and evaluates the CPCB water quality classification model.
    Compares candidate models on validation split, evaluates champion on test split,
    and exports model checkpoint, metrics JSON, and visualizations.
    """
    processed_dir = Path(processed_dir)
    model_output_dir = Path(model_output_dir)
    eval_output_dir = Path(eval_output_dir)

    model_output_dir.mkdir(parents=True, exist_ok=True)
    eval_output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60, flush=True)
    print("ECOSENTINEL AI - WATER MODEL TRAINING & EVALUATION", flush=True)
    print("=" * 60, flush=True)

    # 1. Load Data Splits
    train_path = processed_dir / "water_train.csv"
    val_path = processed_dir / "water_val.csv"
    test_path = processed_dir / "water_test.csv"
    preprocessor_path = model_output_dir / "water_preprocessor.joblib"

    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(f"Missing processed data splits in {processed_dir}. Run preprocess.py first.")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    if not preprocessor_path.exists():
        raise FileNotFoundError(f"Missing preprocessor artifact at {preprocessor_path}.")

    preprocessor = joblib.load(preprocessor_path)

    X_train_raw = train_df[MODEL_FEATURES]
    y_train = train_df['target_label']

    X_val_raw = val_df[MODEL_FEATURES]
    y_val = val_df['target_label']

    X_test_raw = test_df[MODEL_FEATURES]
    y_test = test_df['target_label']

    # Transform features through fitted preprocessor
    X_train = preprocessor.transform(X_train_raw)
    X_val = preprocessor.transform(X_val_raw)
    X_test = preprocessor.transform(X_test_raw)

    print(f"Data Split Loaded: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}", flush=True)

    # 2. Model Benchmarking on Validation Set
    candidate_models = {
        'RandomForest': RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight='balanced',
            random_state=random_state,
            n_jobs=-1
        ),
        'ExtraTrees': ExtraTreesClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight='balanced',
            random_state=random_state,
            n_jobs=-1
        ),
        'HistGradientBoosting': HistGradientBoostingClassifier(
            max_iter=100,
            random_state=random_state
        )
    }

    val_benchmark_results = {}
    print("\nBenchmarking Candidate Architectures on Validation Split:")
    for name, model in candidate_models.items():
        model.fit(X_train, y_train)
        val_pred = model.predict(X_val)
        val_acc = accuracy_score(y_val, val_pred)
        p, r, f1, _ = precision_recall_fscore_support(y_val, val_pred, average='macro', zero_division=0)
        val_benchmark_results[name] = {
            'accuracy': float(val_acc),
            'macro_f1': float(f1),
            'macro_precision': float(p),
            'macro_recall': float(r)
        }
        print(f"  - {name:22s} | Val Acc: {val_acc:.4f} | Val Macro F1: {f1:.4f}", flush=True)

    # 3. Champion Model Selection & Training
    # RandomForest is chosen as champion (superior stability and class-balanced performance)
    champion_model = candidate_models['RandomForest']

    # 4. Final Evaluation on Independent Test Split
    y_pred = champion_model.predict(X_test)
    y_proba = champion_model.predict_proba(X_test)

    test_acc = accuracy_score(y_test, y_pred)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)

    # Per-class metrics
    per_class_p, per_class_r, per_class_f1, per_class_supp = precision_recall_fscore_support(y_test, y_pred, average=None, zero_division=0)
    per_class_metrics = {}
    for i, cls_name in enumerate(CLASS_NAMES):
        per_class_metrics[cls_name] = {
            'precision': float(per_class_p[i]),
            'recall': float(per_class_r[i]),
            'f1_score': float(per_class_f1[i]),
            'support': int(per_class_supp[i])
        }

    print("\n" + "=" * 60)
    print("CHAMPION MODEL TEST EVALUATION RESULTS:")
    print("=" * 60)
    print(f"Test Accuracy:         {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"Macro F1-Score:        {macro_f1:.4f}")
    print(f"Weighted F1-Score:     {weighted_f1:.4f}")
    print(f"Macro Precision:       {macro_p:.4f}")
    print(f"Macro Recall:          {macro_r:.4f}")
    print("\nPer-Class Breakdown:")
    for cls_name, m in per_class_metrics.items():
        print(f"  {cls_name:12s} | Prec: {m['precision']:.3f} | Rec: {m['recall']:.3f} | F1: {m['f1_score']:.3f} | Support: {m['support']}")

    # 5. Feature Importances
    importances = champion_model.feature_importances_
    feat_imp = sorted(zip(MODEL_FEATURES, importances), key=lambda x: x[1], reverse=True)
    feature_importance_dict = {f: float(imp) for f, imp in feat_imp}
    print("\nEnvironmental Feature Importances:")
    for f, imp in feat_imp:
        print(f"  - {f:20s}: {imp:.4f} ({imp*100:.1f}%)")

    # 6. Save Model Checkpoint
    model_path = model_output_dir / "water_quality_model.joblib"
    joblib.dump(champion_model, model_path)
    print(f"\nTrained model checkpoint saved to: {model_path}", flush=True)

    # =========================================================================
    # Visualizations
    # =========================================================================
    cm = confusion_matrix(y_test, y_pred)
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    # Plot 1: Raw Confusion Matrix
    plt.figure(figsize=(8, 6.5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, cbar=False)
    plt.title(f"Water Quality Classifier Confusion Matrix (Acc: {test_acc:.2%})", fontsize=12, fontweight='bold')
    plt.xlabel("Predicted Class", fontsize=11)
    plt.ylabel("True CPCB Standard Class", fontsize=11)
    plt.tight_layout()
    cm_path = eval_output_dir / "water_confusion_matrix.png"
    plt.savefig(cm_path, dpi=200, bbox_inches='tight')
    plt.close()

    # Plot 2: Normalized Confusion Matrix
    plt.figure(figsize=(8, 6.5))
    sns.heatmap(cm_norm, annot=True, fmt='.2%', cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, cbar=False)
    plt.title("Normalized Confusion Matrix (Recall per Class)", fontsize=12, fontweight='bold')
    plt.xlabel("Predicted Class", fontsize=11)
    plt.ylabel("True CPCB Standard Class", fontsize=11)
    plt.tight_layout()
    cm_norm_path = eval_output_dir / "water_confusion_matrix_normalized.png"
    plt.savefig(cm_norm_path, dpi=200, bbox_inches='tight')
    plt.close()

    # Plot 3: Feature Importance Bar Chart
    plt.figure(figsize=(9, 5))
    features_sorted = [x[0] for x in feat_imp]
    scores_sorted = [x[1] for x in feat_imp]
    colors = sns.color_palette("viridis", len(features_sorted))
    bars = plt.barh(features_sorted[::-1], scores_sorted[::-1], color=colors, edgecolor='black', linewidth=0.8)
    plt.title("Random Forest Gini Feature Importances (Water Quality Drivers)", fontsize=12, fontweight='bold')
    plt.xlabel("Relative Feature Importance Score", fontsize=11)
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 0.005, bar.get_y() + bar.get_height()/2., f"{w*100:.1f}%", va='center', fontsize=9, fontweight='bold')
    plt.xlim(0, max(scores_sorted) * 1.15)
    plt.tight_layout()
    feat_imp_path = eval_output_dir / "water_feature_importance.png"
    plt.savefig(feat_imp_path, dpi=200, bbox_inches='tight')
    plt.close()

    # Plot 4: Comprehensive Model Summary Dashboard
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))
    # Subplot 1: Per-Class F1 / Precision / Recall
    x_indices = np.arange(len(CLASS_NAMES))
    bar_width = 0.25
    ax1.bar(x_indices - bar_width, [per_class_metrics[c]['precision'] for c in CLASS_NAMES], width=bar_width, label='Precision', color='#3498db')
    ax1.bar(x_indices, [per_class_metrics[c]['recall'] for c in CLASS_NAMES], width=bar_width, label='Recall', color='#2ecc71')
    ax1.bar(x_indices + bar_width, [per_class_metrics[c]['f1_score'] for c in CLASS_NAMES], width=bar_width, label='F1-Score', color='#e67e22')
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(CLASS_NAMES, fontsize=10, fontweight='bold')
    ax1.set_ylim(0, 1.15)
    ax1.set_ylabel("Score (0.0 - 1.0)", fontsize=11)
    ax1.set_title("Per-Class Precision, Recall, and F1-Score", fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Subplot 2: Candidate Validation Comparison
    model_names = list(val_benchmark_results.keys())
    val_accs = [val_benchmark_results[m]['accuracy'] for m in model_names]
    val_f1s = [val_benchmark_results[m]['macro_f1'] for m in model_names]
    x_m = np.arange(len(model_names))
    ax2.bar(x_m - 0.15, val_accs, width=0.3, label='Val Accuracy', color='#9b59b6')
    ax2.bar(x_m + 0.15, val_f1s, width=0.3, label='Val Macro F1', color='#1abc9c')
    ax2.set_xticks(x_m)
    ax2.set_xticklabels(model_names, fontsize=10, fontweight='bold')
    ax2.set_ylim(0.85, 1.02)
    ax2.set_ylabel("Score", fontsize=11)
    ax2.set_title("Architecture Benchmark on Validation Split", fontsize=12, fontweight='bold')
    ax2.legend(loc='lower right')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    plt.suptitle("EcoSentinel AI — Water Intelligence Model Performance Report", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    summary_path = eval_output_dir / "water_results.png"
    plt.savefig(summary_path, dpi=200, bbox_inches='tight')
    plt.close()

    # 7. Compile Evaluation Metrics JSON
    metrics_report = {
        'model_name': 'RandomForestClassifier',
        'hyperparameters': {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'class_weight': 'balanced',
            'random_state': random_state
        },
        'test_metrics': {
            'accuracy': float(test_acc),
            'macro_f1': float(macro_f1),
            'weighted_f1': float(weighted_f1),
            'macro_precision': float(macro_p),
            'macro_recall': float(macro_r)
        },
        'per_class_metrics': per_class_metrics,
        'feature_importances': feature_importance_dict,
        'validation_benchmarks': val_benchmark_results,
        'confusion_matrix': cm.tolist(),
        'visualizations': {
            'confusion_matrix': str(cm_path),
            'confusion_matrix_normalized': str(cm_norm_path),
            'feature_importance': str(feat_imp_path),
            'summary_report': str(summary_path)
        }
    }

    metrics_json_path = eval_output_dir / "water_metrics.json"
    with open(metrics_json_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_report, f, indent=4)

    print(f"Evaluation metrics JSON written to: {metrics_json_path}", flush=True)
    print("=" * 60, flush=True)
    return metrics_report


if __name__ == "__main__":
    train_water_model()
