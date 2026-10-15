"""
EcoSentinel AI - Environmental Risk Prioritization Engine
Calculates transparent, explainable rule-based priority scores (0-100) for environmental reports.
Considers report severity, recurrence at locations, age of unresolved tickets, and water proximity.
Provides full mathematical factor breakdowns and operational triage recommendations.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


# Standard score thresholds
TIER_THRESHOLDS = [
    (70, "Critical Attention", "Immediate intervention or emergency crew dispatch required within 12 hours."),
    (55, "High Priority", "Schedule targeted cleanup or field inspection within 24–48 hours."),
    (35, "Moderate Priority", "Incorporate into routine ward collection and periodic monitoring routes."),
    (0,  "Low Priority", "Isolated or minor incident; monitor for recurrence.")
]

SEVERITY_WEIGHTS = {
    'Critical': 35.0,
    'High': 27.0,
    'Medium': 18.0,
    'Low': 8.0
}


def calculate_age_days(timestamp_iso: str) -> float:
    """Calculates age in days from an ISO8601 UTC timestamp string."""
    try:
        # Handle trailing Z or timezone offsets
        ts = timestamp_iso.replace("Z", "+00:00")
        report_dt = datetime.fromisoformat(ts)
        now_dt = datetime.now(timezone.utc)
        diff = now_dt - report_dt
        return max(0.0, diff.total_seconds() / 86400.0)
    except Exception:
        return 0.0


def calculate_priority_score(
    report: Dict[str, Any],
    location_report_count: int = 1
) -> Dict[str, Any]:
    """
    Computes transparent rule-based Priority Score (0-100) for a single report.
    
    Args:
        report: Dict containing report fields (status, severity_level, total_waste_objects,
                water_measurements, predicted_water_class, timestamp, report_type).
        location_report_count: Number of historical reports associated with this location.
        
    Returns:
        dict containing:
            - 'priority_score': float (0.0 to 100.0)
            - 'priority_tier': string
            - 'factor_breakdown': dict with individual point contributions
            - 'explanation_narrative': text explanation
            - 'recommended_action': operational advice
            - 'disclaimer': academic & responsible use disclaimer
    """
    status = report.get('status', 'Reported')

    # If already resolved, score is zeroed or marked archival
    if status == 'Resolved':
        return {
            'priority_score': 0.0,
            'priority_tier': 'Resolved',
            'factor_breakdown': {
                'severity_points': 0.0,
                'recurrence_points': 0.0,
                'age_penalty_points': 0.0,
                'ecological_sensitivity_points': 0.0
            },
            'explanation_narrative': "This environmental incident has been verified and marked as Resolved.",
            'recommended_action': "Archived ticket; periodic post-cleanup verification.",
            'disclaimer': "Rule-based prototype triage score. Not an authoritative pollution assessment."
        }

    # =========================================================================
    # Factor 1: Severity Score (Max 35 points)
    # =========================================================================
    severity = report.get('severity_level', 'Medium')
    base_severity = SEVERITY_WEIGHTS.get(severity, 18.0)

    # Waste volume or water classification bonus/adjustment
    total_waste = report.get('total_waste_objects', 0)
    water_class = report.get('predicted_water_class', '')

    sev_bonus = 0.0
    if total_waste >= 30 or water_class == 'Critical':
        sev_bonus = 5.0
    elif total_waste >= 15 or water_class in ['Class D/E', 'Class C']:
        sev_bonus = 2.0

    severity_points = min(35.0, base_severity + sev_bonus)

    # =========================================================================
    # Factor 2: Recurrence Score (Max 25 points)
    # =========================================================================
    if location_report_count <= 1:
        recurrence_points = 5.0
        rec_desc = "First recorded incident at this location (isolated event)."
    elif location_report_count <= 3:
        recurrence_points = 12.0
        rec_desc = f"Moderate recurrence ({location_report_count} cumulative reports)."
    elif location_report_count <= 5:
        recurrence_points = 18.0
        rec_desc = f"High recurrence ({location_report_count} reports); indicates emerging chronic dumping site."
    else:
        recurrence_points = 25.0
        rec_desc = f"Severe chronic recurrence ({location_report_count} reports); persistent environmental hotspot."

    # =========================================================================
    # Factor 3: Age & Unresolved Penalty (Max 20 points)
    # =========================================================================
    age_days = calculate_age_days(report.get('timestamp', ''))
    if age_days < 1.0:
        age_points = 4.0
        age_desc = f"Recently filed ({age_days*24:.1f} hours ago)."
    elif age_days <= 3.0:
        age_points = 8.0
        age_desc = f"Unresolved for {age_days:.1f} days."
    elif age_days <= 7.0:
        age_points = 14.0
        age_desc = f"Lingering for {age_days:.1f} days; escalated for delayed action."
    else:
        age_points = 20.0
        age_desc = f"Chronic delay ({age_days:.1f} days unresolved); maximum aging penalty applied."

    # =========================================================================
    # Factor 4: Ecological Sensitivity / Water Proximity (Max 20 points)
    # =========================================================================
    report_type = report.get('report_type', 'waste')
    loc_name = report.get('location_name', '').lower()

    if report_type == 'combined' or 'canal' in loc_name or 'river' in loc_name or 'lake' in loc_name:
        eco_points = 20.0
        eco_desc = "Direct interface with surface water body or dual waste-water hazard."
    elif 'drain' in loc_name or 'culvert' in loc_name:
        eco_points = 14.0
        eco_desc = "Proximity to drainage canal / culvert with potential downstream runoff."
    elif 'cafeteria' in loc_name or 'hostel' in loc_name:
        eco_points = 10.0
        eco_desc = "High-density residential or dining zone with public health implications."
    else:
        eco_points = 5.0
        eco_desc = "Standard terrestrial / roadside observation."

    # Total Score
    total_score = min(100.0, round(severity_points + recurrence_points + age_points + eco_points, 1))

    # Determine Tier
    tier_name = "Low Priority"
    action_text = "Standard routing."
    for threshold, name, action in TIER_THRESHOLDS:
        if total_score >= threshold:
            tier_name = name
            action_text = action
            break

    # Critical severity or critical water contamination automatically escalates to Critical Attention
    if (severity == 'Critical' or water_class == 'Critical' or total_score >= 70.0) and status != 'Resolved':
        tier_name = "Critical Attention"
        action_text = "Immediate intervention or emergency crew dispatch required within 12 hours."

    # Build Narrative
    narrative = (
        f"Assigned score of {total_score}/100 ({tier_name}). "
        f"Contributed by: Severity ({severity_points:.1f} pts from {severity} severity), "
        f"Recurrence ({recurrence_points:.1f} pts: {rec_desc}), "
        f"Aging ({age_points:.1f} pts: {age_desc}), and "
        f"Ecological Sensitivity ({eco_points:.1f} pts: {eco_desc})."
    )

    return {
        'priority_score': total_score,
        'priority_tier': tier_name,
        'factor_breakdown': {
            'severity_points': severity_points,
            'recurrence_points': recurrence_points,
            'age_penalty_points': age_points,
            'ecological_sensitivity_points': eco_points
        },
        'explanation_narrative': narrative,
        'recommended_action': action_text,
        'disclaimer': "Notice: This score is a prototype heuristic triage score for prioritization, not a certified environmental impact prediction."
    }


def prioritize_all_reports(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks a list of reports by calculating cumulative recurrence per location
    and returning them sorted by descending priority score.
    """
    # Count occurrences per location name
    location_counts = {}
    for r in reports:
        loc = r.get('location_name', 'Unknown').strip().lower()
        location_counts[loc] = location_counts.get(loc, 0) + 1

    scored_reports = []
    for r in reports:
        loc = r.get('location_name', 'Unknown').strip().lower()
        rec_count = location_counts.get(loc, 1)
        score_meta = calculate_priority_score(r, location_report_count=rec_count)
        
        # Merge scoring details into report dict
        r_copy = dict(r)
        r_copy['priority_score'] = score_meta['priority_score']
        r_copy['priority_tier'] = score_meta['priority_tier']
        r_copy['factor_breakdown'] = score_meta['factor_breakdown']
        r_copy['explanation_narrative'] = score_meta['explanation_narrative']
        r_copy['recommended_action'] = score_meta['recommended_action']
        scored_reports.append(r_copy)

    # Sort descending by priority score
    scored_reports.sort(key=lambda x: x['priority_score'], reverse=True)
    return scored_reports
