"""
EcoSentinel AI - REST API Server (Flask)
Exposes ML inference, hotspot scoring, SQLite persistence, and evaluation analytics
to the React frontend.
"""

import os
import sys
import io
import base64
import json
from pathlib import Path
from PIL import Image
from flask import Flask, request, jsonify, send_file, send_from_directory

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.waste.predict import predict_waste
from src.water.predict import predict_water
from src.database import (
    init_db,
    seed_sample_reports_if_empty,
    create_report,
    get_all_reports,
    get_report_by_id,
    update_report_status,
    update_human_verification,
    delete_report,
    VALID_STATUSES
)
from src.hotspot_scoring import prioritize_all_reports, calculate_priority_score

# Initialize DB on startup
init_db()
seed_sample_reports_if_empty()

app = Flask(__name__)

# Global CORS Handler
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,PATCH,OPTIONS'
    return response

# Handle preflight OPTIONS requests across all routes
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return ('', 204)


@app.route('/', methods=['GET'])
def root_index():
    return jsonify({
        "status": "online",
        "service": "EcoSentinel AI REST API Server",
        "frontend": "http://localhost:3000",
        "endpoints": [
            "/api/health",
            "/api/stats",
            "/api/reports",
            "/api/hotspots",
            "/api/samples/waste",
            "/api/predict/waste",
            "/api/predict/water"
        ]
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health status and model readiness check."""
    waste_model_exists = (ROOT_DIR / "models" / "waste_yolo11n.pt").exists()
    water_model_exists = (ROOT_DIR / "models" / "water_quality_model.joblib").exists()
    db_exists = (ROOT_DIR / "data" / "ecosentinel.db").exists()
    
    return jsonify({
        "status": "healthy",
        "service": "EcoSentinel AI Intelligence Grid API",
        "version": "2.0.0",
        "models": {
            "waste_yolo11n": "ready" if waste_model_exists else "missing",
            "water_random_forest": "ready" if water_model_exists else "missing"
        },
        "database": "connected" if db_exists else "initializing"
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Aggregated environmental metrics and telemetry."""
    reports = get_all_reports()
    prioritized = prioritize_all_reports(reports)
    
    total_reports = len(reports)
    status_counts = {"Reported": 0, "Under Review": 0, "Cleanup Assigned": 0, "Resolved": 0}
    total_waste_objects = 0
    wqi_vals = []
    
    for r in reports:
        st = r.get("status", "Reported")
        status_counts[st] = status_counts.get(st, 0) + 1
        total_waste_objects += r.get("total_waste_objects", 0) or 0
        if r.get("wqi_score") is not None:
            wqi_vals.append(r["wqi_score"])
            
    avg_wqi = round(sum(wqi_vals) / len(wqi_vals), 1) if wqi_vals else 68.4
    critical_hotspots = sum(
        1 for p in prioritized 
        if p.get("status") != "Resolved" and (
            "critical" in str(p.get("priority_tier", "")).lower() or 
            p.get("severity_level") == "Critical" or 
            (p.get("priority_score") or 0) >= 70
        )
    )
    
    return jsonify({
        "total_reports": total_reports,
        "status_breakdown": status_counts,
        "total_waste_detected": total_waste_objects,
        "average_wqi": avg_wqi,
        "critical_hotspots": critical_hotspots,
        "recent_reports": prioritized[:5]
    })


@app.route('/api/predict/waste', methods=['POST'])
def run_waste_inference():
    """
    Accepts uploaded image file or a sample image filename,
    runs YOLO11n waste detection, and returns bounding boxes and annotated image.
    """
    conf = float(request.form.get("conf_threshold", 0.15))
    sample_name = request.form.get("sample_name")
    
    image = None
    original_filename = "custom_image.jpg"
    
    if 'image' in request.files and request.files['image'].filename:
        file = request.files['image']
        original_filename = file.filename
        try:
            image = Image.open(file.stream).convert('RGB')
        except Exception as e:
            return jsonify({"status": "error", "message": f"Invalid image file: {str(e)}"}), 400
    elif sample_name:
        # Check in test samples
        sample_path = ROOT_DIR / "data" / "processed" / "waste" / "images" / "test" / sample_name
        if not sample_path.exists():
            # Check outputs/predictions
            sample_path = ROOT_DIR / "outputs" / "predictions" / sample_name
        if sample_path.exists():
            original_filename = sample_name
            image = Image.open(sample_path).convert('RGB')
        else:
            return jsonify({"status": "error", "message": f"Sample image '{sample_name}' not found"}), 404
    else:
        return jsonify({"status": "error", "message": "No image or sample_name provided"}), 400
        
    width, height = image.size
    
    results = predict_waste(image, conf_threshold=conf)
    
    if results['status'] != 'success':
        return jsonify(results), 500
        
    # Convert annotated image to Base64 JPEG
    annotated_pil = results.get('annotated_image')
    annotated_b64 = None
    if annotated_pil:
        buffer = io.BytesIO()
        annotated_pil.save(buffer, format='JPEG', quality=90)
        annotated_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
        
    return jsonify({
        "status": "success",
        "filename": original_filename,
        "image_dimensions": {"width": width, "height": height},
        "total_detections": results['total_detections'],
        "counts": results['counts'],
        "detections": results['detections'],
        "annotated_image_b64": annotated_b64
    })


@app.route('/api/predict/water', methods=['POST'])
def run_water_inference():
    """
    Accepts JSON body with 8 chemical parameters and returns CPCB class, WQI, and limiting factors.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "error", "message": "JSON body required"}), 400
        
    required_keys = ['dissolved_oxygen', 'ph', 'bod', 'conductivity', 'nitrate', 'total_coliform', 'temperature', 'fecal_coliform']
    # Supply sensible defaults for any omitted keys
    sample_input = {
        'dissolved_oxygen': float(data.get('dissolved_oxygen', 6.5)),
        'ph': float(data.get('ph', 7.4)),
        'bod': float(data.get('bod', 2.2)),
        'conductivity': float(data.get('conductivity', 250.0)),
        'nitrate': float(data.get('nitrate', 0.8)),
        'total_coliform': float(data.get('total_coliform', 450.0)),
        'temperature': float(data.get('temperature', 25.0)),
        'fecal_coliform': float(data.get('fecal_coliform', 120.0))
    }
    
    results = predict_water(sample_input)
    return jsonify(results)


@app.route('/api/reports', methods=['GET', 'POST'])
def handle_reports():
    """List all reports (with priority scores) or submit a new incident report."""
    if request.method == 'GET':
        reports = get_all_reports()
        prioritized = prioritize_all_reports(reports)
        return jsonify({"reports": prioritized, "total": len(prioritized)})
        
    # POST - Create new report
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "error", "message": "JSON payload required"}), 400
        
    try:
        wqi_val = float(data["wqi_score"]) if data.get("wqi_score") is not None else None
        pred_water_class = data.get("predicted_water_class") or data.get("water_class")
        
        report_id = create_report(
            report_type=data.get("report_type", "waste"),
            location_name=data.get("location_name", "Unspecified Landmark"),
            latitude=float(data.get("latitude", 13.0827)),
            longitude=float(data.get("longitude", 80.2707)),
            image_path=data.get("image_path"),
            waste_counts=data.get("waste_counts", {}),
            total_waste_objects=int(data.get("total_waste_objects", 0)),
            water_measurements=data.get("water_measurements"),
            predicted_water_class=pred_water_class,
            wqi_score=wqi_val,
            severity_level=data.get("severity_level", "Medium"),
            reviewer_notes=data.get("reviewer_notes", "")
        )
        new_report = get_report_by_id(report_id)
        return jsonify({"status": "success", "report_id": report_id, "report": new_report}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_single_report(report_id):
    """Retrieve single report by ID for citizen tracking."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"status": "error", "message": f"Incident Ticket #{report_id} not found."}), 404
    return jsonify({"status": "success", "report": report})


@app.route('/api/reports/<int:report_id>/status', methods=['PATCH'])
def update_status(report_id):
    """Transition a report's lifecycle status."""
    data = request.get_json(force=True, silent=True) or {}
    new_status = data.get("status")
    notes = data.get("note") or data.get("notes") or "Status updated via dashboard"
    resolved_image_path = data.get("resolved_image_path")
    
    if new_status not in VALID_STATUSES:
        return jsonify({
            "status": "error",
            "message": f"Invalid status '{new_status}'. Allowed: {VALID_STATUSES}"
        }), 400
        
    try:
        success = update_report_status(
            report_id, 
            new_status, 
            notes=notes, 
            resolved_image_path=resolved_image_path
        )
        if not success:
            return jsonify({"status": "error", "message": "Report not found"}), 404
            
        updated = get_report_by_id(report_id)
        return jsonify({"status": "success", "report": updated})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# Demo user database for role-based authentication
DEMO_USERS = {
    "admin@ecosentinel.gov": {
        "email": "admin@ecosentinel.gov",
        "password": "admin123",
        "name": "Admin Officer Swarna",
        "role": "admin",
        "role_title": "Chief Municipal Sanitation Officer",
        "badge_id": "ADM-7749",
        "department": "City Environmental Protection & Sanitation Directorate"
    },
    "worker@sanitation.gov": {
        "email": "worker@sanitation.gov",
        "password": "cleaner123",
        "name": "Ravi Kumar",
        "role": "worker",
        "role_title": "Senior Field Sanitation Specialist",
        "badge_id": "SN-CREW-12",
        "department": "Zone 4 Rapid Cleanup & Hazardous Waste Unit"
    },
    "user@ecosentinel.org": {
        "email": "user@ecosentinel.org",
        "password": "citizen123",
        "name": "Surya Prakash",
        "role": "citizen",
        "role_title": "Verified Community Sentinel",
        "badge_id": "CIT-3301",
        "department": "Public Environmental Watch Volunteer"
    },
    "suryaprakash9320@gmail.com": {
        "email": "suryaprakash9320@gmail.com",
        "password": "citizen123",
        "name": "Surya Prakash",
        "role": "citizen",
        "role_title": "Verified Community Sentinel",
        "badge_id": "CIT-9320",
        "department": "Civic Environmental Action Group"
    }
}


@app.route('/api/auth/demo-accounts', methods=['GET'])
def get_demo_accounts():
    """Returns sample demo logins for quick 1-click testing."""
    accounts = []
    for user in DEMO_USERS.values():
        accounts.append({
            "email": user["email"],
            "password": user["password"],
            "name": user["name"],
            "role": user["role"],
            "role_title": user["role_title"],
            "badge_id": user["badge_id"],
            "department": user["department"]
        })
    return jsonify({"status": "success", "accounts": accounts})


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Authenticates users, admins, and sanitation workers."""
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    requested_role = data.get("role", "").strip().lower()

    if not email:
        return jsonify({"status": "error", "message": "Email address or username required."}), 400

    # Check registered demo user
    matched_user = None
    for k, u in DEMO_USERS.items():
        if k.lower() == email or u["email"].lower() == email:
            matched_user = u
            break

    if matched_user:
        # If password is provided, verify it (demo allows password or matches)
        if password and password != matched_user["password"]:
            return jsonify({"status": "error", "message": "Incorrect password. Use demo password or 1-click login."}), 401
        
        # Override role if explicitly chosen by user
        user_data = dict(matched_user)
        if requested_role and requested_role in ["citizen", "admin", "worker"]:
            user_data["role"] = requested_role
            if requested_role == "worker":
                user_data["role_title"] = "Field Sanitation Specialist"
            elif requested_role == "admin":
                user_data["role_title"] = "Municipal Admin Officer"
            else:
                user_data["role_title"] = "Verified Community Sentinel"
        
        return jsonify({
            "status": "success",
            "message": f"Welcome back, {user_data['name']}!",
            "user": user_data
        })

    # Graceful fallback for custom emails/usernames
    role = requested_role if requested_role in ["citizen", "admin", "worker"] else "citizen"
    display_name = email.split("@")[0].replace(".", " ").title()
    
    role_titles = {
        "admin": "Municipal Sanitation Officer",
        "worker": "Sanitation Field Crew Operator",
        "citizen": "Public Community Sentinel"
    }
    
    custom_user = {
        "email": email,
        "name": display_name,
        "role": role,
        "role_title": role_titles.get(role, "Environmental Sentinel"),
        "badge_id": f"{role[:3].upper()}-{abs(hash(email)) % 9000 + 1000}",
        "department": "EcoSentinel Civic Action Network"
    }
    
    return jsonify({
        "status": "success",
        "message": f"Logged in as {custom_user['name']} ({role.capitalize()})",
        "user": custom_user
    })


@app.route('/api/worker/tasks', methods=['GET'])
def get_worker_tasks():
    """Returns priority work orders specifically for sanitation workers."""
    reports = get_all_reports()
    prioritized = prioritize_all_reports(reports)
    
    # Priority status filter: Cleanup Assigned, Reported, Under Review
    active_tasks = [
        r for r in prioritized 
        if r.get("status") in ["Cleanup Assigned", "Reported", "Under Review"]
    ]
    
    # Completed tasks for shift history
    completed_tasks = [
        r for r in prioritized
        if r.get("status") == "Resolved"
    ]
    
    return jsonify({
        "status": "success",
        "total_active": len(active_tasks),
        "total_completed": len(completed_tasks),
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks[:20]
    })


@app.route('/api/reports/<int:report_id>/verify', methods=['PATCH'])
def update_verification(report_id):
    """Toggle human verification for a report."""
    data = request.get_json(force=True, silent=True) or {}
    is_verified = bool(data.get("is_verified", True))
    notes = data.get("notes") or data.get("reviewer_notes") or "Verified via field inspection"
    
    try:
        success = update_human_verification(report_id, verified=is_verified, reviewer_notes=notes)
        if not success:
            return jsonify({"status": "error", "message": "Report not found"}), 404
            
        updated = get_report_by_id(report_id)
        return jsonify({"status": "success", "report": updated})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report_endpoint(report_id):
    """Delete a report."""
    success = delete_report(report_id)
    if not success:
        return jsonify({"status": "error", "message": "Report not found"}), 404
    return jsonify({"status": "success", "message": f"Report #{report_id} deleted"})


@app.route('/api/hotspots', methods=['GET'])
def get_hotspots():
    """Ranked priority hotspots with full explainability scorecards."""
    reports = get_all_reports()
    ranked = prioritize_all_reports(reports)
    return jsonify({"hotspots": ranked, "count": len(ranked)})


@app.route('/api/samples/waste', methods=['GET'])
def list_sample_images():
    """Returns curated list of waste sample images available for demonstration."""
    sample_dir = ROOT_DIR / "data" / "processed" / "waste" / "images" / "test"
    samples = []
    
    if sample_dir.exists():
        for img_path in sorted(sample_dir.glob("*.*")):
            if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                samples.append({
                    "filename": img_path.name,
                    "url": f"/api/samples/waste/{img_path.name}"
                })
    return jsonify({"samples": samples})


@app.route('/api/samples/waste/<path:filename>', methods=['GET'])
def serve_sample_image(filename):
    """Serves a test waste image."""
    sample_dir = ROOT_DIR / "data" / "processed" / "waste" / "images" / "test"
    file_path = sample_dir / filename
    if file_path.exists():
        return send_file(file_path, mimetype='image/jpeg')
    return jsonify({"status": "error", "message": "File not found"}), 404


@app.route('/api/evaluation/metrics', methods=['GET'])
def get_evaluation_metrics():
    """Returns genuine trained evaluation metrics for both Waste and Water modules."""
    waste_metrics_path = ROOT_DIR / "outputs" / "evaluation" / "waste_metrics.json"
    water_metrics_path = ROOT_DIR / "outputs" / "evaluation" / "water_metrics.json"
    
    waste_data = {}
    water_data = {}
    
    if waste_metrics_path.exists():
        with open(waste_metrics_path, 'r') as f:
            waste_data = json.load(f)
            
    if water_metrics_path.exists():
        with open(water_metrics_path, 'r') as f:
            water_data = json.load(f)
            
    return jsonify({
        "waste": waste_data,
        "water": water_data
    })


@app.route('/api/evaluation/images/<path:filename>', methods=['GET'])
def serve_evaluation_image(filename):
    """Serves evaluation plots and confusion matrices."""
    eval_dir = ROOT_DIR / "outputs" / "evaluation"
    file_path = eval_dir / filename
    if not file_path.exists():
        eval_dir = ROOT_DIR / "outputs" / "data_audit"
        file_path = eval_dir / filename
        
    if file_path.exists():
        return send_file(file_path, mimetype='image/png')
    return jsonify({"status": "error", "message": "Plot not found"}), 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 EcoSentinel AI REST API Server starting on http://localhost:{port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
