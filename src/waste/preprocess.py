"""
EcoSentinel AI - Waste Data Preprocessing Module
Handles loading raw TACO annotations, downloading image subsets,
converting COCO bounding boxes to YOLO format using native catalog reference coordinates,
and organizing train/val/test splits without leakage.
"""

import os
import json
import shutil
import urllib.request
import random
from collections import defaultdict
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target classes mapped to unified superclasses
CLASS_MAPPING = {
    'Bottle': 0,
    'Plastic bag & wrapper': 1,
    'Can': 2,
    'Cup': 3
}

CLASS_NAMES = ['Bottle', 'Plastic_bag', 'Can', 'Cup']


def convert_coco_to_yolo(bbox, orig_w, orig_h):
    """
    Convert COCO bounding box [x_min, y_min, w, h] to YOLO normalized format [x_center, y_center, w, h]
    using the original catalog image dimensions (orig_w, orig_h).
    """
    if orig_w <= 0 or orig_h <= 0:
        return None
        
    x_min, y_min, w, h = map(float, bbox)
    
    if w <= 0 or h <= 0:
        return None
        
    x_center = (x_min + w / 2.0) / float(orig_w)
    y_center = (y_min + h / 2.0) / float(orig_h)
    yolo_w = w / float(orig_w)
    yolo_h = h / float(orig_h)
    
    # Clip normalized coordinates to [0.0, 1.0]
    x_center = max(0.001, min(0.999, x_center))
    y_center = max(0.001, min(0.999, y_center))
    yolo_w = max(0.001, min(1.0, yolo_w))
    yolo_h = max(0.001, min(1.0, yolo_h))
    
    return [x_center, y_center, yolo_w, yolo_h]


def download_single_image(img_info, raw_img_dir):
    """
    Download a single image from TACO Flickr URL and verify integrity.
    """
    img_id = img_info['id']
    url = img_info.get('flickr_640_url') or img_info.get('flickr_url')
    if not url:
        return None, False
        
    ext = os.path.splitext(url.split('?')[0])[-1] or '.jpg'
    filename = f"taco_{img_id:05d}{ext}"
    filepath = Path(raw_img_dir) / filename
    
    if filepath.exists() and filepath.stat().st_size > 1000:
        try:
            with Image.open(filepath) as im:
                im.verify()
            return filepath, True
        except Exception:
            pass
            
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read()
            if len(content) < 1000:
                return None, False
            with open(filepath, 'wb') as f:
                f.write(content)
        with Image.open(filepath) as im:
            im.verify()
        return filepath, True
    except Exception:
        if filepath.exists():
            try:
                filepath.unlink()
            except OSError:
                pass
        return None, False


def prepare_waste_dataset(
    raw_anno_path="data/raw/waste/annotations.json",
    raw_img_dir="data/raw/waste/images",
    processed_dir="data/processed/waste",
    max_images=120,
    train_ratio=0.70,
    val_ratio=0.20,
    test_ratio=0.10,
    seed=42
):
    """
    Selects balanced subset with verified target annotations, downloads raw images,
    creates mathematically correct YOLO annotations, and organizes splits without leakage.
    """
    random.seed(seed)
    raw_anno_path = Path(raw_anno_path)
    raw_img_dir = Path(raw_img_dir)
    processed_dir = Path(processed_dir)
    
    raw_img_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean previous processed images/labels to guarantee zero leakage between runs
    for sub in ['images', 'labels']:
        sub_path = processed_dir / sub
        if sub_path.exists():
            shutil.rmtree(sub_path)
            
    with open(raw_anno_path, 'r', encoding='utf-8') as f:
        coco = json.load(f)
        
    categories = {c['id']: c for c in coco['categories']}
    images_dict = {img['id']: img for img in coco['images']}
    
    # Group annotations by image
    img_to_anns = defaultdict(list)
    for ann in coco['annotations']:
        cat_id = ann['category_id']
        supercat = categories.get(cat_id, {}).get('supercategory', '')
        if supercat in CLASS_MAPPING:
            cls_idx = CLASS_MAPPING[supercat]
            img_to_anns[ann['image_id']].append({
                'class_id': cls_idx,
                'supercat': supercat,
                'bbox': ann['bbox']
            })
            
    # Candidate images are only images that have at least one target annotation
    candidate_img_ids = [iid for iid, anns in img_to_anns.items() if len(anns) > 0]
    random.shuffle(candidate_img_ids)
    
    selected_img_ids = set()
    per_class_quota = max_images // len(CLASS_MAPPING)
    
    for cls_idx in sorted(CLASS_MAPPING.values()):
        cls_imgs = [iid for iid in candidate_img_ids if any(a['class_id'] == cls_idx for a in img_to_anns[iid])]
        for iid in cls_imgs[:per_class_quota + 15]:
            if len(selected_img_ids) < max_images:
                selected_img_ids.add(iid)
                
    for iid in candidate_img_ids:
        if len(selected_img_ids) >= max_images:
            break
        selected_img_ids.add(iid)
        
    selected_list = sorted(list(selected_img_ids))
    print(f"Selected {len(selected_list)} images with confirmed waste annotations for dataset generation...")
    
    # Download images using thread pool
    download_targets = [images_dict[iid] for iid in selected_list if iid in images_dict]
    valid_downloads = {}
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_info = {executor.submit(download_single_image, info, raw_img_dir): info for info in download_targets}
        for future in as_completed(future_to_info):
            info = future_to_info[future]
            path, success = future.result()
            if success and path is not None:
                valid_downloads[info['id']] = path
                
    print(f"Successfully validated {len(valid_downloads)} downloaded images.")
    
    valid_ids = sorted(list(valid_downloads.keys()))
    random.shuffle(valid_ids)
    
    n_total = len(valid_ids)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    
    train_ids = set(valid_ids[:n_train])
    val_ids = set(valid_ids[n_train:n_train + n_val])
    test_ids = set(valid_ids[n_train + n_val:])
    
    splits = {
        'train': train_ids,
        'val': val_ids,
        'test': test_ids
    }
    
    for split in ['train', 'val', 'test']:
        (processed_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
        (processed_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
    split_stats = defaultdict(lambda: defaultdict(int))
    
    for split, id_set in splits.items():
        for iid in id_set:
            src_path = valid_downloads[iid]
            img_info = images_dict[iid]
            orig_w = img_info['width']
            orig_h = img_info['height']
            
            dest_img_path = processed_dir / 'images' / split / src_path.name
            with open(src_path, 'rb') as f_src, open(dest_img_path, 'wb') as f_dst:
                f_dst.write(f_src.read())
                
            label_file = processed_dir / 'labels' / split / f"{src_path.stem}.txt"
            yolo_lines = []
            for ann in img_to_anns[iid]:
                yolo_bbox = convert_coco_to_yolo(ann['bbox'], orig_w, orig_h)
                if yolo_bbox is not None:
                    cls_id = ann['class_id']
                    line = f"{cls_id} {yolo_bbox[0]:.6f} {yolo_bbox[1]:.6f} {yolo_bbox[2]:.6f} {yolo_bbox[3]:.6f}\n"
                    yolo_lines.append(line)
                    split_stats[split][CLASS_NAMES[cls_id]] += 1
                    
            with open(label_file, 'w', encoding='utf-8') as f_lbl:
                f_lbl.writelines(yolo_lines)
                
            split_stats[split]['total_images'] += 1
            
    yaml_content = f"""# EcoSentinel AI - Waste Dataset Configuration (YOLO11n)
path: {processed_dir.resolve().as_posix()}
train: images/train
val: images/val
test: images/test

names:
  0: Bottle
  1: Plastic_bag
  2: Can
  3: Cup
"""
    yaml_path = processed_dir / "dataset.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f_yaml:
        f_yaml.write(yaml_content)
        
    print(f"Saved YOLO dataset config to: {yaml_path}")
    print("Dataset Preparation Summary:")
    for split, stats in split_stats.items():
        print(f"  {split.upper()}: {stats['total_images']} images, Annotations: {dict(stats)}")
        
    return {
        'yaml_path': str(yaml_path),
        'split_stats': {k: dict(v) for k, v in split_stats.items()},
        'class_names': CLASS_NAMES
    }


if __name__ == "__main__":
    prepare_waste_dataset()
