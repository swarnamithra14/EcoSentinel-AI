"""
EcoSentinel AI - Waste Model Training Module
Trains YOLO11n on the preprocessed waste dataset using CPU-optimized parameters.
Saves checkpoints, evaluation metrics (mAP@0.5, mAP@0.5:0.95, Precision, Recall),
and generates training curves and confusion matrix artifacts.
"""

import os
import sys
import shutil
import json
from pathlib import Path
from ultralytics import YOLO


def train_waste_model(
    data_yaml="data/processed/waste/dataset.yaml",
    epochs=5,
    imgsz=320,
    batch=8,
    model_output_dir="models",
    eval_output_dir="outputs/evaluation"
):
    """
    Trains YOLO11n waste object detector, validates performance,
    and exports trained model weights and evaluation reports.
    """
    data_yaml = Path(data_yaml)
    if not data_yaml.exists():
        raise FileNotFoundError(f"Missing dataset configuration at: {data_yaml}")
        
    model_output_dir = Path(model_output_dir)
    eval_output_dir = Path(eval_output_dir)
    model_output_dir.mkdir(parents=True, exist_ok=True)
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60, flush=True)
    print("ECOSENTINEL AI - WASTE MODEL TRAINING (YOLO11n)", flush=True)
    print("=" * 60, flush=True)
    print(f"Dataset YAML: {data_yaml}", flush=True)
    print(f"Epochs: {epochs} | Image Size: {imgsz} | Batch Size: {batch} | Device: CPU", flush=True)
    
    # Initialize YOLO11n base architecture
    base_model = YOLO("yolo11n.pt")
    
    # Train model
    print("Starting training run...", flush=True)
    results = base_model.train(
        data=str(data_yaml.resolve()),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device="cpu",
        workers=0,
        project="runs",
        name="waste_yolo11n",
        exist_ok=True,
        verbose=True,
        plots=True,
        lr0=0.01,
        warmup_epochs=1.0
    )
    
    run_dir = Path(results.save_dir)
    weights_dir = run_dir / "weights"
    best_pt = weights_dir / "best.pt"
    last_pt = weights_dir / "last.pt"
    
    final_checkpoint = best_pt if best_pt.exists() else last_pt
    if not final_checkpoint.exists():
        raise RuntimeError(f"Training failed to produce a valid model checkpoint in {weights_dir}")
        
    target_model_path = model_output_dir / "waste_yolo11n.pt"
    shutil.copy2(final_checkpoint, target_model_path)
    print(f"Successfully saved trained model to: {target_model_path}", flush=True)
    
    # Load trained model for rigorous evaluation on Validation and Test sets
    trained_model = YOLO(str(target_model_path))
    
    print("Running validation set evaluation...", flush=True)
    val_metrics = trained_model.val(
        data=str(data_yaml.resolve()),
        split="val",
        imgsz=imgsz,
        batch=batch,
        device="cpu"
    )
    
    print("Running test set evaluation...", flush=True)
    test_metrics = trained_model.val(
        data=str(data_yaml.resolve()),
        split="test",
        imgsz=imgsz,
        batch=batch,
        device="cpu"
    )
    
    # Extract genuine evaluation metrics
    eval_summary = {
        "model_architecture": "YOLO11n",
        "epochs_trained": epochs,
        "input_image_size": imgsz,
        "batch_size": batch,
        "saved_checkpoint": str(target_model_path),
        "val_metrics": {
            "mAP_50": round(float(val_metrics.box.map50), 4),
            "mAP_50_95": round(float(val_metrics.box.map), 4),
            "precision": round(float(val_metrics.box.mp), 4),
            "recall": round(float(val_metrics.box.mr), 4)
        },
        "test_metrics": {
            "mAP_50": round(float(test_metrics.box.map50), 4),
            "mAP_50_95": round(float(test_metrics.box.map), 4),
            "precision": round(float(test_metrics.box.mp), 4),
            "recall": round(float(test_metrics.box.mr), 4)
        },
        "target_classes": val_metrics.names
    }
    
    # Save evaluation report JSON
    eval_json_path = eval_output_dir / "waste_metrics.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)
    print(f"Saved evaluation metrics to: {eval_json_path}", flush=True)
    
    # Copy evaluation plots to outputs/evaluation
    plot_files = ["results.png", "confusion_matrix.png", "confusion_matrix_normalized.png", "PR_curve.png", "F1_curve.png"]
    for pf in plot_files:
        src_plot = run_dir / pf
        if src_plot.exists():
            shutil.copy2(src_plot, eval_output_dir / f"waste_{pf}")
            print(f"Copied plot: {pf} -> outputs/evaluation/waste_{pf}", flush=True)
            
    print("=" * 60, flush=True)
    print("WASTE MODEL EVALUATION SUMMARY:")
    print(f"Validation mAP@0.5: {eval_summary['val_metrics']['mAP_50']}")
    print(f"Validation mAP@0.5:0.95: {eval_summary['val_metrics']['mAP_50_95']}")
    print(f"Validation Precision: {eval_summary['val_metrics']['precision']}")
    print(f"Validation Recall: {eval_summary['val_metrics']['recall']}")
    print(f"Test mAP@0.5: {eval_summary['test_metrics']['mAP_50']}")
    print("=" * 60, flush=True)
    
    return eval_summary


def export_existing_run(
    source_run_dir="runs/detect/runs/detect/waste_yolo11n",
    data_yaml="data/processed/waste/dataset.yaml",
    model_output_dir="models",
    eval_output_dir="outputs/evaluation",
    epochs=5,
    imgsz=320,
    batch=8
):

    """
    Exports and evaluates an already completed training run to avoid re-training.
    """
    run_dir = Path(source_run_dir)
    model_output_dir = Path(model_output_dir)
    eval_output_dir = Path(eval_output_dir)
    model_output_dir.mkdir(parents=True, exist_ok=True)
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    
    weights_dir = run_dir / "weights"
    best_pt = weights_dir / "best.pt"
    last_pt = weights_dir / "last.pt"
    
    final_checkpoint = best_pt if best_pt.exists() else last_pt
    if not final_checkpoint.exists():
        raise RuntimeError(f"Missing checkpoint in {weights_dir}")
        
    target_model_path = model_output_dir / "waste_yolo11n.pt"
    shutil.copy2(final_checkpoint, target_model_path)
    print(f"Successfully copied trained checkpoint to: {target_model_path}", flush=True)
    
    data_yaml = Path(data_yaml)
    trained_model = YOLO(str(target_model_path))
    
    print("Running validation evaluation...", flush=True)
    val_metrics = trained_model.val(
        data=str(data_yaml.resolve()),
        split="val",
        imgsz=imgsz,
        batch=batch,
        device="cpu"
    )
    
    print("Running test evaluation...", flush=True)
    test_metrics = trained_model.val(
        data=str(data_yaml.resolve()),
        split="test",
        imgsz=imgsz,
        batch=batch,
        device="cpu"
    )
    
    eval_summary = {
        "model_architecture": "YOLO11n",
        "epochs_trained": epochs,
        "input_image_size": imgsz,
        "batch_size": batch,
        "saved_checkpoint": str(target_model_path),
        "val_metrics": {
            "mAP_50": round(float(val_metrics.box.map50), 4),
            "mAP_50_95": round(float(val_metrics.box.map), 4),
            "precision": round(float(val_metrics.box.mp), 4),
            "recall": round(float(val_metrics.box.mr), 4)
        },
        "test_metrics": {
            "mAP_50": round(float(test_metrics.box.map50), 4),
            "mAP_50_95": round(float(test_metrics.box.map), 4),
            "precision": round(float(test_metrics.box.mp), 4),
            "recall": round(float(test_metrics.box.mr), 4)
        },
        "target_classes": val_metrics.names
    }
    
    eval_json_path = eval_output_dir / "waste_metrics.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)
    print(f"Saved evaluation metrics to: {eval_json_path}", flush=True)
    
    plot_files = ["results.png", "confusion_matrix.png", "confusion_matrix_normalized.png", "PR_curve.png", "F1_curve.png"]
    for pf in plot_files:
        src_plot = run_dir / pf
        if src_plot.exists():
            shutil.copy2(src_plot, eval_output_dir / f"waste_{pf}")
            print(f"Copied plot: {pf} -> outputs/evaluation/waste_{pf}", flush=True)
            
    print("=" * 60, flush=True)
    print("WASTE MODEL EVALUATION SUMMARY:")
    print(f"Validation mAP@0.5: {eval_summary['val_metrics']['mAP_50']}")
    print(f"Validation mAP@0.5:0.95: {eval_summary['val_metrics']['mAP_50_95']}")
    print(f"Validation Precision: {eval_summary['val_metrics']['precision']}")
    print(f"Validation Recall: {eval_summary['val_metrics']['recall']}")
    print(f"Test mAP@0.5: {eval_summary['test_metrics']['mAP_50']}")
    print("=" * 60, flush=True)
    
    return eval_summary


if __name__ == "__main__":
    train_waste_model(epochs=15, imgsz=320, batch=8)
