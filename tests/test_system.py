"""
EcoSentinel AI - Unit Test Suite for Database & Prioritization Engine
Validates SQLite database operations, lifecycle transitions, status history logs,
and rule-based priority scoring with explainability factor breakdowns.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import (
    init_db,
    create_report,
    get_all_reports,
    get_report_by_id,
    update_report_status,
    update_human_verification,
    delete_report,
    VALID_STATUSES
)
from src.hotspot_scoring import (
    calculate_priority_score,
    prioritize_all_reports,
    calculate_age_days
)


def test_database_crud_operations():
    """Verify report creation, retrieval, status update, and deletion in a temp db."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name

    try:
        init_db(temp_db)

        # 1. Create Report
        rep_id = create_report(
            report_type="waste",
            location_name="Engineering Hostel Quadrangle",
            latitude=13.0123,
            longitude=80.2345,
            waste_counts={"Bottle": 5, "Can": 2},
            total_waste_objects=7,
            severity_level="Medium",
            reviewer_notes="Plastic bottles scattered near drainage duct.",
            db_path=temp_db
        )
        assert rep_id > 0, "Report ID must be positive integer."

        # 2. Retrieve Report
        rep = get_report_by_id(rep_id, db_path=temp_db)
        assert rep is not None
        assert rep["location_name"] == "Engineering Hostel Quadrangle"
        assert rep["status"] == "Reported"
        assert rep["waste_counts"]["Bottle"] == 5
        assert len(rep["status_history"]) == 1

        # 3. Update Status to Under Review
        success = update_report_status(rep_id, "Under Review", notes="Assigned to inspector", db_path=temp_db)
        assert success is True
        rep_updated = get_report_by_id(rep_id, db_path=temp_db)
        assert rep_updated["status"] == "Under Review"
        assert len(rep_updated["status_history"]) == 2

        # 4. Human Verification
        update_human_verification(rep_id, verified=True, severity_level="High", priority_score=75.0, db_path=temp_db)
        rep_verified = get_report_by_id(rep_id, db_path=temp_db)
        assert rep_verified["human_verified"] == 1
        assert rep_verified["severity_level"] == "High"
        assert rep_verified["priority_score"] == 75.0

        # 5. Delete Report
        del_success = delete_report(rep_id, db_path=temp_db)
        assert del_success is True
        assert get_report_by_id(rep_id, db_path=temp_db) is None

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_invalid_status_raises_error():
    """Verify that an invalid status raises a ValueError."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name

    try:
        init_db(temp_db)
        rep_id = create_report(report_type="water", location_name="Test Lake", db_path=temp_db)
        try:
            update_report_status(rep_id, "CompletelyDoneInvalidStatus", db_path=temp_db)
            assert False, "Should have raised ValueError on invalid status."
        except ValueError:
            pass
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_priority_score_calculation():
    """Verify prioritization score calculation and factor breakdown."""
    critical_report = {
        'status': 'Reported',
        'severity_level': 'Critical',
        'total_waste_objects': 45,
        'predicted_water_class': 'Critical',
        'report_type': 'combined',
        'location_name': 'Yamuna Riverbank Culvert Drain',
        'timestamp': '2026-10-01T10:00:00+00:00'
    }

    score_result = calculate_priority_score(critical_report, location_report_count=6)
    assert score_result['priority_score'] >= 80.0
    assert score_result['priority_tier'] == 'Critical Attention'
    assert 'factor_breakdown' in score_result
    assert score_result['factor_breakdown']['severity_points'] == 35.0
    assert score_result['factor_breakdown']['recurrence_points'] == 25.0
    assert 'explanation_narrative' in score_result
    assert 'disclaimer' in score_result


def test_resolved_report_has_zero_score():
    """Verify resolved reports receive zero priority score and resolved tier."""
    resolved_report = {
        'status': 'Resolved',
        'severity_level': 'High',
        'total_waste_objects': 25,
        'report_type': 'waste',
        'location_name': 'Cleaned Park',
        'timestamp': '2026-10-01T10:00:00+00:00'
    }

    score_result = calculate_priority_score(resolved_report, location_report_count=2)
    assert score_result['priority_score'] == 0.0
    assert score_result['priority_tier'] == 'Resolved'


def test_prioritize_all_reports_sorting():
    """Verify multiple reports are sorted in descending priority order."""
    reports = [
        {'id': 1, 'status': 'Reported', 'severity_level': 'Low', 'total_waste_objects': 2, 'location_name': 'Quiet Pathway', 'report_type': 'waste'},
        {'id': 2, 'status': 'Reported', 'severity_level': 'Critical', 'total_waste_objects': 50, 'location_name': 'Lake Outfall', 'report_type': 'combined'},
        {'id': 3, 'status': 'Reported', 'severity_level': 'Medium', 'total_waste_objects': 10, 'location_name': 'Campus Canteen', 'report_type': 'waste'}
    ]

    ranked = prioritize_all_reports(reports)
    assert ranked[0]['id'] == 2, "Critical Lake Outfall should be ranked #1."
    assert ranked[0]['priority_score'] > ranked[1]['priority_score']
    assert ranked[1]['priority_score'] > ranked[2]['priority_score']


if __name__ == '__main__':
    tests = [
        test_database_crud_operations,
        test_invalid_status_raises_error,
        test_priority_score_calculation,
        test_resolved_report_has_zero_score,
        test_prioritize_all_reports_sorting
    ]
    print(f"Running {len(tests)} system tests...\n")
    for t in tests:
        t()
        print(f"  [PASS] {t.__name__}")
    print(f"\nALL {len(tests)} SYSTEM TESTS PASSED SUCCESSFULLY!")
