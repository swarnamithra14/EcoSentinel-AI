"""
EcoSentinel AI - Waste Model Inference Module
Loads trained YOLO11n checkpoint, runs inference on user images,
returns structured detections, class counts, and annotated images.
Never trains during prediction; handles missing models gracefully.
"""

import os
from pathlib import Path
from PIL import Image
import numpy as np
from ultralytics import YOLO

# Global cache for loaded model to avoid reloading on every prediction call
_MODEL_CACHE = {}


def get_waste_model(model_path="models/waste_yolo11n.pt"):
    """
    Returns cached YOLO model instance or loads from disk.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained waste model artifact not found at '{model_path}'. "
            "Please run model training first before running inference."
        )
    key = str(model_path.resolve())
    if key not in _MODEL_CACHE:
        _MODEL_CACHE[key] = YOLO(key)
    return _MODEL_CACHE[key]


def predict_waste(image_input, conf_threshold=0.20, model_path="models/waste_yolo11n.pt"):
    """
    Runs inference on an uploaded image.
    
    Args:
        image_input: File path (str/Path), PIL Image, or numpy array.
        conf_threshold: Minimum confidence score (0.0 - 1.0).
        model_path: Path to the trained .pt model checkpoint.
        
    Returns:
        dict containing:
            - 'detections': List of dicts [class_name, class_id, confidence, bbox]
            - 'counts': Dict mapping class names to detected counts
            - 'total_detections': Total waste objects detected
            - 'annotated_image': PIL Image with bounding boxes and labels
            - 'status': 'success' or error description
    """
    try:
        model = get_waste_model(model_path)
    except FileNotFoundError as e:
        return {
            'status': 'error',
            'error': str(e),
            'detections': [],
            'counts': {},
            'total_detections': 0,
            'annotated_image': None
        }
        
    # Input validation
    if isinstance(image_input, (str, Path)):
        img_path = Path(image_input)
        if not img_path.exists():
            return {
                'status': 'error',
                'error': f"Input image does not exist: {img_path}",
                'detections': [],
                'counts': {},
                'total_detections': 0,
                'annotated_image': None
            }
        pil_img = Image.open(img_path).convert("RGB")
    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("RGB")
    elif isinstance(image_input, np.ndarray):
        pil_img = Image.fromarray(image_input).convert("RGB")
    else:
        return {
            'status': 'error',
            'error': f"Unsupported image input type: {type(image_input)}",
            'detections': [],
            'counts': {},
            'total_detections': 0,
            'annotated_image': None
        }
        
    # Run inference
    results = model.predict(pil_img, conf=conf_threshold, verbose=False, device="cpu")
    result = results[0]
    
    detections = []
    counts = {}
    names = result.names
    
    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        xyxy = [float(coord) for coord in box.xyxy[0].tolist()]
        cls_name = names.get(cls_id, f"Class_{cls_id}")
        
        detections.append({
            'class_id': cls_id,
            'class_name': cls_name,
            'confidence': round(conf, 4),
            'bbox': [round(c, 2) for c in xyxy]
        })
        
        counts[cls_name] = counts.get(cls_name, 0) + 1
        
    # Generate annotated image
    annotated_arr = result.plot()  # Returns BGR numpy array
    # Convert BGR to RGB PIL image
    annotated_rgb = annotated_arr[:, :, ::-1]
    annotated_pil = Image.fromarray(annotated_rgb)
    
    return {
        'status': 'success',
        'detections': detections,
        'counts': counts,
        'total_detections': len(detections),
        'annotated_image': annotated_pil
    }


if __name__ == "__main__":
    # Test execution when model is present
    sample_test_img = Path("data/processed/waste/images/test")
    test_files = list(sample_test_img.glob("*.*"))
    if test_files:
        print(f"Testing prediction on: {test_files[0]}")
        res = predict_waste(test_files[0])
        print(f"Result Status: {res['status']}")
        print(f"Detected Counts: {res['counts']}")
