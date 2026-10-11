"""
EcoSentinel AI - Waste Data Audit Module
Inspects waste dataset, validates annotations and image files, checks for corruptions,
verifies split separation (zero leakage), and generates distribution plots and audit reports.
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use('Agg')  # Headless backend for background execution
import matplotlib.pyplot as plt
from collections import defaultdict


def audit_waste_dataset(
    processed_dir="data/processed/waste",
    output_dir="outputs/data_audit"
):
    """
    Performs comprehensive audit on the processed YOLO waste dataset.
    Generates summary report and visualizations.
    """
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    yaml_path = processed_dir / "dataset.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Missing dataset.yaml at {yaml_path}")
        
    class_names = {
        0: 'Bottle',
        1: 'Plastic_bag',
        2: 'Can',
        3: 'Cup'
    }
    
    splits = ['train', 'val', 'test']
    split_images = {}
    split_annotations = defaultdict(lambda: defaultdict(int))
    bbox_dimensions = []
    corrupt_images = []
    invalid_bboxes = 0
    
    total_images_checked = 0
    print("Starting waste dataset audit...", flush=True)
    
    for split in splits:
        img_dir = processed_dir / 'images' / split
        lbl_dir = processed_dir / 'labels' / split
        
        if not img_dir.exists():
            continue
            
        images = list(img_dir.glob("*.*"))
        split_images[split] = set(img.name for img in images)
        print(f"Auditing split '{split}': {len(images)} images found.", flush=True)
        
        for img_path in images:
            total_images_checked += 1
            # 1. Image readability check
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
                    if w <= 0 or h <= 0:
                        raise ValueError(f"Invalid dimensions: {w}x{h}")
            except Exception as e:
                corrupt_images.append({'file': str(img_path), 'error': str(e)})
                continue
                
            # 2. Label file validation
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            if lbl_path.exists():
                with open(lbl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) == 5:
                            cls_id = int(parts[0])
                            xc, yc, bw, bh = map(float, parts[1:])
                            
                            # Range check
                            if 0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < bw <= 1.0 and 0.0 < bh <= 1.0:
                                cls_name = class_names.get(cls_id, f"Class_{cls_id}")
                                split_annotations[split][cls_name] += 1
                                bbox_dimensions.append({
                                    'class': cls_name,
                                    'width': bw,
                                    'height': bh,
                                    'aspect_ratio': bw / bh if bh > 0 else 0
                                })
                            else:
                                invalid_bboxes += 1
                                
    # 3. Check split leakage
    train_set = split_images.get('train', set())
    val_set = split_images.get('val', set())
    test_set = split_images.get('test', set())
    
    leakage_train_val = list(train_set.intersection(val_set))
    leakage_train_test = list(train_set.intersection(test_set))
    leakage_val_test = list(val_set.intersection(test_set))
    has_leakage = bool(leakage_train_val or leakage_train_test or leakage_val_test)
    
    print("Generating class distribution chart...", flush=True)
    # 4. Generate Visualizations
    fig, ax = plt.subplots(figsize=(9, 5))
    classes = list(class_names.values())
    x = range(len(classes))
    width = 0.25
    
    train_counts = [split_annotations['train'].get(c, 0) for c in classes]
    val_counts = [split_annotations['val'].get(c, 0) for c in classes]
    test_counts = [split_annotations['test'].get(c, 0) for c in classes]
    
    ax.bar([i - width for i in x], train_counts, width=width, label='Train', color='#2b5c8f')
    ax.bar(x, val_counts, width=width, label='Val', color='#48a999')
    ax.bar([i + width for i in x], test_counts, width=width, label='Test', color='#e07a5f')
    
    ax.set_ylabel('Number of Annotations', fontsize=12)
    ax.set_title('Waste Dataset Class Distribution Across Splits', fontsize=14, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(classes, fontsize=11)
    ax.legend(frameon=True)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    chart_path = output_dir / "waste_class_distribution.png"
    plt.savefig(chart_path, dpi=150)
    plt.close(fig)
    
    # Audit summary dictionary
    audit_results = {
        'total_images_checked': total_images_checked,
        'split_counts': {s: len(imgs) for s, imgs in split_images.items()},
        'class_distribution': {s: dict(split_annotations[s]) for s in splits},
        'corrupt_images_found': len(corrupt_images),
        'invalid_bounding_boxes': invalid_bboxes,
        'split_leakage_detected': has_leakage,
        'leakage_details': {
            'train_val_overlap': len(leakage_train_val),
            'train_test_overlap': len(leakage_train_test),
            'val_test_overlap': len(leakage_val_test)
        },
        'target_classes': class_names,
        'visualization_saved': str(chart_path)
    }
    
    report_path = output_dir / "waste_audit_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, indent=2)
        
    print("=" * 60, flush=True)
    print("ECOSENTINEL AI - WASTE DATASET AUDIT REPORT", flush=True)
    print("=" * 60, flush=True)
    print(f"Total Images Validated: {total_images_checked}", flush=True)
    print(f"Splits: Train={len(train_set)}, Val={len(val_set)}, Test={len(test_set)}", flush=True)
    print(f"Corrupt Images: {len(corrupt_images)}", flush=True)
    print(f"Invalid Bounding Boxes: {invalid_bboxes}", flush=True)
    print(f"Data Leakage Detected: {has_leakage}", flush=True)
    print("Class Counts per Split:", flush=True)
    for s in splits:
        print(f"  {s.upper()}: {dict(split_annotations[s])}", flush=True)
    print(f"Saved Visualization: {chart_path}", flush=True)
    print(f"Saved Audit Report: {report_path}", flush=True)
    print("=" * 60, flush=True)
    
    return audit_results


if __name__ == "__main__":
    audit_waste_dataset()
