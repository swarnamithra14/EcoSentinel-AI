"""
EcoSentinel AI - SQLite Database & Incident Tracking Module
Manages environmental incident reports, status lifecycle (Reported -> Under Review -> Cleanup Assigned -> Resolved),
geospatial metadata, model detections, human audit notes, and before/after verification evidence.
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

DEFAULT_DB_PATH = "data/ecosentinel.db"

VALID_STATUSES = ["Reported", "Under Review", "Cleanup Assigned", "Resolved"]
VALID_SEVERITIES = ["Low", "Medium", "High", "Critical"]


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a database connection with Row factory enabled."""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_type TEXT NOT NULL,                -- 'waste', 'water', 'combined'
        timestamp TEXT NOT NULL,                  -- ISO8601 UTC
        location_name TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        image_path TEXT,
        waste_counts TEXT,                        -- JSON string of class counts
        total_waste_objects INTEGER DEFAULT 0,
        water_measurements TEXT,                  -- JSON string of sensor inputs
        predicted_water_class TEXT,
        wqi_score REAL,
        severity_level TEXT DEFAULT 'Medium',     -- 'Low', 'Medium', 'High', 'Critical'
        status TEXT DEFAULT 'Reported',           -- 'Reported', 'Under Review', 'Cleanup Assigned', 'Resolved'
        human_verified INTEGER DEFAULT 0,        -- 0 = unverified, 1 = verified
        reviewer_notes TEXT,
        resolution_notes TEXT,
        resolved_image_path TEXT,
        resolved_at TEXT,
        priority_score REAL DEFAULT 0.0
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status);
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_reports_location ON reports (location_name);
    """)

    conn.commit()
    conn.close()


def create_report(
    report_type: str,
    location_name: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    image_path: Optional[str] = None,
    waste_counts: Optional[Dict[str, int]] = None,
    total_waste_objects: int = 0,
    water_measurements: Optional[Dict[str, float]] = None,
    predicted_water_class: Optional[str] = None,
    wqi_score: Optional[float] = None,
    severity_level: str = "Medium",
    reviewer_notes: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Inserts a new environmental report into SQLite database."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    now_iso = datetime.now(timezone.utc).isoformat()
    waste_json = json.dumps(waste_counts) if waste_counts else None
    water_json = json.dumps(water_measurements) if water_measurements else None

    cursor.execute("""
    INSERT INTO reports (
        report_type, timestamp, location_name, latitude, longitude,
        image_path, waste_counts, total_waste_objects,
        water_measurements, predicted_water_class, wqi_score,
        severity_level, status, human_verified, reviewer_notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Reported', 0, ?)
    """, (
        report_type, now_iso, location_name, latitude, longitude,
        image_path, waste_json, total_waste_objects,
        water_json, predicted_water_class, wqi_score,
        severity_level, reviewer_notes
    ))

    report_id = cursor.lastrowid

    # Log initial status history
    cursor.execute("""
    INSERT INTO status_history (report_id, old_status, new_status, timestamp, notes)
    VALUES (?, NULL, 'Reported', ?, 'Initial report filed')
    """, (report_id, now_iso))

    conn.commit()
    conn.close()
    return report_id


def get_all_reports(
    status: Optional[str] = None,
    report_type: Optional[str] = None,
    limit: int = 200,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Retrieves all reports with optional status and type filters."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM reports WHERE 1=1"
    params = []

    if status and status in VALID_STATUSES:
        query += " AND status = ?"
        params.append(status)

    if report_type:
        query += " AND report_type = ?"
        params.append(report_type)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        d = dict(row)
        if d['waste_counts']:
            try:
                d['waste_counts'] = json.loads(d['waste_counts'])
            except Exception:
                pass
        if d['water_measurements']:
            try:
                d['water_measurements'] = json.loads(d['water_measurements'])
            except Exception:
                pass
        results.append(d)
    return results


def get_report_by_id(report_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single report by ID along with its status history."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    report = dict(row)
    if report['waste_counts']:
        try:
            report['waste_counts'] = json.loads(report['waste_counts'])
        except Exception:
            pass
    if report['water_measurements']:
        try:
            report['water_measurements'] = json.loads(report['water_measurements'])
        except Exception:
            pass

    # Fetch status history
    cursor.execute("SELECT * FROM status_history WHERE report_id = ? ORDER BY id ASC", (report_id,))
    history_rows = cursor.fetchall()
    report['status_history'] = [dict(h) for h in history_rows]

    conn.close()
    return report


def update_report_status(
    report_id: int,
    new_status: str,
    notes: Optional[str] = None,
    resolved_image_path: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates the lifecycle status of a report and records status history."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {VALID_STATUSES}")

    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    old_status = row['status']
    now_iso = datetime.now(timezone.utc).isoformat()

    resolved_at = now_iso if new_status == "Resolved" else None

    cursor.execute("""
    UPDATE reports
    SET status = ?,
        resolution_notes = COALESCE(?, resolution_notes),
        resolved_image_path = COALESCE(?, resolved_image_path),
        resolved_at = COALESCE(?, resolved_at)
    WHERE id = ?
    """, (new_status, notes, resolved_image_path, resolved_at, report_id))

    cursor.execute("""
    INSERT INTO status_history (report_id, old_status, new_status, timestamp, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (report_id, old_status, new_status, now_iso, notes or f"Status changed to {new_status}"))

    conn.commit()
    conn.close()
    return True


def update_human_verification(
    report_id: int,
    verified: bool = True,
    reviewer_notes: Optional[str] = None,
    severity_level: Optional[str] = None,
    priority_score: Optional[float] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """Updates human verification status, reviewed severity, and priority score."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    verified_int = 1 if verified else 0
    now_iso = datetime.now(timezone.utc).isoformat()

    updates = ["human_verified = ?"]
    params = [verified_int]

    if reviewer_notes is not None:
        updates.append("reviewer_notes = ?")
        params.append(reviewer_notes)

    if severity_level and severity_level in VALID_SEVERITIES:
        updates.append("severity_level = ?")
        params.append(severity_level)

    if priority_score is not None:
        updates.append("priority_score = ?")
        params.append(float(priority_score))

    params.append(report_id)
    sql = f"UPDATE reports SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(sql, params)

    conn.commit()
    conn.close()
    return True


def delete_report(report_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Deletes a report and associated history."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    cursor.execute("DELETE FROM status_history WHERE report_id = ?", (report_id,))
    conn.commit()
    conn.close()
    return True


def seed_sample_reports_if_empty(db_path: str = DEFAULT_DB_PATH) -> int:
    """Seeds realistic demonstration reports if database is currently empty."""
    init_db(db_path)
    existing = get_all_reports(limit=1, db_path=db_path)
    if existing:
        return 0

    sample_reports = [
        {
            'report_type': 'waste',
            'location_name': 'North Campus Lake Gate & Cafeteria Block',
            'latitude': 13.0827,
            'longitude': 80.2707,
            'waste_counts': {'Bottle': 7, 'Plastic_bag': 12, 'Can': 4, 'Cup': 9},
            'total_waste_objects': 32,
            'severity_level': 'High',
            'reviewer_notes': 'Recurring dumping near storm water canal behind student cafeteria.'
        },
        {
            'report_type': 'water',
            'location_name': 'Kaveri River Intake Station #4',
            'latitude': 10.7905,
            'longitude': 78.7047,
            'water_measurements': {
                'dissolved_oxygen': 4.4, 'ph': 7.1, 'bod': 4.2,
                'conductivity': 680.0, 'total_coliform': 3200.0
            },
            'predicted_water_class': 'Class C',
            'wqi_score': 74.5,
            'severity_level': 'Medium',
            'reviewer_notes': 'Seasonal agricultural runoff causing moderate BOD elevation.'
        },
        {
            'report_type': 'combined',
            'location_name': 'Industrial Canal Outfall & Wetland Confluence',
            'latitude': 12.9716,
            'longitude': 77.5946,
            'waste_counts': {'Bottle': 15, 'Plastic_bag': 25, 'Can': 6, 'Cup': 11},
            'total_waste_objects': 57,
            'water_measurements': {
                'dissolved_oxygen': 1.8, 'ph': 6.2, 'bod': 22.5,
                'conductivity': 2100.0, 'total_coliform': 38000.0
            },
            'predicted_water_class': 'Critical',
            'wqi_score': 240.0,
            'severity_level': 'Critical',
            'reviewer_notes': 'Severe untreated sewage and plastic accumulation blocking culvert flow.'
        },
        {
            'report_type': 'waste',
            'location_name': 'Central Sports Pavilion Lawn',
            'latitude': 13.0382,
            'longitude': 80.2215,
            'waste_counts': {'Bottle': 3, 'Plastic_bag': 2, 'Cup': 4},
            'total_waste_objects': 9,
            'severity_level': 'Low',
            'reviewer_notes': 'Post-tournament littering; single event, low recurrence.'
        }
    ]

    count = 0
    for r in sample_reports:
        create_report(
            report_type=r['report_type'],
            location_name=r['location_name'],
            latitude=r.get('latitude'),
            longitude=r.get('longitude'),
            waste_counts=r.get('waste_counts'),
            total_waste_objects=r.get('total_waste_objects', 0),
            water_measurements=r.get('water_measurements'),
            predicted_water_class=r.get('predicted_water_class'),
            wqi_score=r.get('wqi_score'),
            severity_level=r.get('severity_level', 'Medium'),
            reviewer_notes=r.get('reviewer_notes'),
            db_path=db_path
        )
        count += 1
    return count


if __name__ == "__main__":
    init_db()
    seeded = seed_sample_reports_if_empty()
    reports = get_all_reports()
    print(f"Database initialized. Seeded: {seeded}. Total reports: {len(reports)}")
