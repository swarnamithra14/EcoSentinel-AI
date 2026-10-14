"""
EcoSentinel AI - Unified Environmental Monitoring & Risk Prioritization System
Interactive Streamlit Application connecting:
  1. Waste Intelligence (YOLO11n Litter Detection)
  2. Water Intelligence (CPCB Surface Water Classifier & WQI Engine)
  3. Environmental Risk Prioritization Engine (Explainable Hotspot Triage)
  4. Incident & Resolution Tracking (SQLite Lifecycle Management)
  5. Audit & Model Analytics Dashboard
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np
import pandas as pd
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.waste.predict import predict_waste
from src.water.predict import predict_water, extract_limiting_factors
from src.database import (
    init_db,
    create_report,
    get_all_reports,
    get_report_by_id,
    update_report_status,
    update_human_verification,
    delete_report,
    seed_sample_reports_if_empty,
    VALID_STATUSES
)
from src.hotspot_scoring import prioritize_all_reports, calculate_priority_score

# Page configuration
st.set_page_config(
    page_title="EcoSentinel AI — Smart Waste & Water Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Global Font & Brand */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header hero */
    .hero-banner {
        background: linear-gradient(135deg, #0d3b2e 0%, #11694e 50%, #0a4d68 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .hero-title {
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #d1fae5;
        margin-top: 6px;
        font-weight: 400;
    }

    /* Metric cards */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-lbl {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }

    /* Badges */
    .badge-class-a { background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 12px; }
    .badge-class-b { background: #e0f2fe; color: #075985; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 12px; }
    .badge-class-c { background: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 12px; }
    .badge-class-d { background: #ffedd5; color: #9a3412; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 12px; }
    .badge-critical { background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 12px; }

    /* Priority Tiers */
    .tier-critical { color: #dc2626; font-weight: 700; }
    .tier-high { color: #ea580c; font-weight: 700; }
    .tier-moderate { color: #d97706; font-weight: 600; }
    .tier-low { color: #16a34a; font-weight: 600; }

    /* Form styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_db()
seed_sample_reports_if_empty()

# Sidebar Navigation
with st.sidebar:
    st.image("https://raw.githubusercontent.com/feathericons/feather/master/icons/activity.svg", width=40)
    st.title("EcoSentinel AI")
    st.caption("AI-Powered Waste & Water Monitoring Grid")
    st.markdown("---")
    
    app_mode = st.radio(
        "Navigation",
        [
            "🛰️ Waste Intelligence",
            "💧 Water Intelligence",
            "⚠️ Priority Hotspot Engine",
            "📋 Incident Tracking (SQLite)",
            "📊 Analytics & Model Cards",
            "ℹ️ System Overview"
        ],
        index=0
    )
    st.markdown("---")
    st.info("**Environment:** Local Inference\n**Waste Model:** YOLO11n\n**Water Model:** CPCB Random Forest\n**Storage:** SQLite Engine")

# =============================================================================
# PAGE 1: WASTE INTELLIGENCE
# =============================================================================
if app_mode == "🛰️ Waste Intelligence":
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">🛰️ Waste Intelligence Module</h1>
        <div class="hero-subtitle">Automated visible litter detection, spatial object counts, and localization powered by Ultralytics YOLO11n.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("1. Input Image")
        input_choice = st.radio(
            "Select Input Source:",
            ["Choose from Test Samples", "Upload Image File"],
            horizontal=True
        )

        image_to_process = None
        image_name = "custom_image.jpg"

        if input_choice == "Choose from Test Samples":
            sample_dir = Path("data/processed/waste/images/test")
            sample_files = list(sample_dir.glob("*.*")) if sample_dir.exists() else []
            if sample_files:
                sample_map = {f.name: f for f in sample_files}
                selected_sample = st.selectbox("Select Test Image:", list(sample_map.keys()))
                image_to_process = sample_map[selected_sample]
                image_name = selected_sample
                st.image(Image.open(image_to_process), caption=f"Selected Sample: {selected_sample}", use_container_width=True)
            else:
                st.warning("No sample images found in test directory.")
        else:
            uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                image_to_process = Image.open(uploaded_file)
                image_name = uploaded_file.name
                st.image(image_to_process, caption="Uploaded Image", use_container_width=True)

        conf_threshold = st.slider("Detection Confidence Threshold", min_value=0.01, max_value=0.50, value=0.05, step=0.01,
                                   help="Lower thresholds capture faint or distant litter in challenging outdoor conditions.")
        
        run_btn = st.button("🚀 Run YOLO11n Detection", type="primary", use_container_width=True)

    with col2:
        st.subheader("2. Detection Output & Breakdown")
        if run_btn and image_to_process is not None:
            with st.spinner("Analyzing waste objects with YOLO11n..."):
                results = predict_waste(
                    image_to_process,
                    conf_threshold=conf_threshold,
                    model_path="models/waste_yolo11n.pt"
                )

            if results['status'] == 'success':
                st.image(results['annotated_image'], caption="YOLO11n Detection Visualizer", use_container_width=True)
                
                # Metric Cards
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Total Objects", results['total_detections'])
                with m2:
                    st.metric("Primary Class", max(results['counts'], key=results['counts'].get) if results['counts'] else "None")
                with m3:
                    st.metric("Classes Detected", len(results['counts']))

                # Breakdown Table
                st.markdown("##### Detected Waste Classification:")
                if results['counts']:
                    counts_df = pd.DataFrame([
                        {"Waste Category": k, "Objects Detected": v}
                        for k, v in results['counts'].items()
                    ])
                    st.dataframe(counts_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No waste objects exceeded the confidence threshold in this frame.")

                # Actionable Save to Database
                st.markdown("---")
                st.markdown("##### 📌 File this Observation as an Incident Ticket:")
                with st.form("log_waste_report_form"):
                    loc_name = st.text_input("Incident Location Name / Landmark:", value="Campus Canal Berm / Block C")
                    lat_col, lon_col = st.columns(2)
                    with lat_col:
                        lat_val = st.number_input("Latitude (optional):", value=13.0827, format="%.4f")
                    with lon_col:
                        lon_val = st.number_input("Longitude (optional):", value=80.2707, format="%.4f")
                    sev_level = st.selectbox("Reviewed Severity Level:", ["Low", "Medium", "High", "Critical"], index=1 if results['total_detections'] < 10 else 2)
                    notes = st.text_area("Field Notes:", value=f"Detected {results['total_detections']} litter objects ({results['counts']}).")
                    
                    submit_ticket = st.form_submit_button("Submit Incident to Triage Queue", use_container_width=True)
                    if submit_ticket:
                        new_id = create_report(
                            report_type="waste",
                            location_name=loc_name,
                            latitude=lat_val,
                            longitude=lon_val,
                            image_path=str(image_name),
                            waste_counts=results['counts'],
                            total_waste_objects=results['total_detections'],
                            severity_level=sev_level,
                            reviewer_notes=notes
                        )
                        st.success(f"Incident Ticket #{new_id} successfully created in SQLite database!")
            else:
                st.error(f"Inference error: {results.get('error')}")
        elif not run_btn:
            st.info("Select or upload an image and click 'Run YOLO11n Detection' to view results.")

# =============================================================================
# PAGE 2: WATER INTELLIGENCE
# =============================================================================
elif app_mode == "💧 Water Intelligence":
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">💧 Water Intelligence Module</h1>
        <div class="hero-subtitle">CPCB Designated Best Use Classification, Water Quality Index (WQI), and explainable limiting factor alerts.</div>
    </div>
    """, unsafe_allow_html=True)

    # Pre-set scenario selector
    preset_scenarios = {
        "Custom Input": None,
        "Himalayan Mountain Headwater Stream (Pristine)": {
            'dissolved_oxygen': 7.8, 'ph': 7.4, 'bod': 1.2, 'conductivity': 95.0,
            'nitrate': 0.15, 'total_coliform': 24.0, 'temperature': 14.5, 'fecal_coliform': 6.0
        },
        "Organized Recreational Bathing Ghat (Ganga)": {
            'dissolved_oxygen': 6.4, 'ph': 7.5, 'bod': 2.4, 'conductivity': 180.0,
            'nitrate': 0.45, 'total_coliform': 320.0, 'temperature': 22.0, 'fecal_coliform': 90.0
        },
        "Municipal Raw Drinking Intake (Kaveri)": {
            'dissolved_oxygen': 5.5, 'ph': 7.2, 'bod': 2.8, 'conductivity': 380.0,
            'nitrate': 1.20, 'total_coliform': 2400.0, 'temperature': 28.0, 'fecal_coliform': 450.0
        },
        "Agricultural Canal & Wetland (Kuttanad)": {
            'dissolved_oxygen': 4.8, 'ph': 6.8, 'bod': 4.5, 'conductivity': 920.0,
            'nitrate': 3.80, 'total_coliform': 850.0, 'temperature': 29.5, 'fecal_coliform': 210.0
        },
        "Untreated Urban Sewage Drain (Najafgarh Drain / Yamuna)": {
            'dissolved_oxygen': 1.2, 'ph': 6.3, 'bod': 28.5, 'conductivity': 2450.0,
            'nitrate': 14.2, 'total_coliform': 48000.0, 'temperature': 31.0, 'fecal_coliform': 18000.0
        }
    }

    selected_scenario = st.selectbox("Load Benchmark Scenario:", list(preset_scenarios.keys()))
    default_vals = preset_scenarios[selected_scenario] or {
        'dissolved_oxygen': 6.5, 'ph': 7.3, 'bod': 2.0, 'conductivity': 220.0,
        'nitrate': 0.5, 'total_coliform': 450.0, 'temperature': 25.0, 'fecal_coliform': 110.0
    }

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.subheader("1. Physicochemical Measurements")
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            val_do = st.number_input("Dissolved Oxygen (DO mg/L):", value=float(default_vals['dissolved_oxygen']), min_value=0.0, max_value=20.0, step=0.1, help="Statutory Clean: >= 6.0 | Bathing: >= 5.0 | Severe Hypoxia: < 4.0")
            val_bod = st.number_input("Biochemical Oxygen Demand (BOD mg/L):", value=float(default_vals['bod']), min_value=0.0, max_value=600.0, step=0.5, help="Statutory Pristine: <= 2.0 | Bathing: <= 3.0 | Critical Sewage: > 6.0")
            val_ph = st.number_input("pH Level (0 – 14):", value=float(default_vals['ph']), min_value=0.0, max_value=14.0, step=0.1, help="CPCB Permissible: 6.5 – 8.5")
            val_cond = st.number_input("Conductivity (µmhos/cm):", value=float(default_vals['conductivity']), min_value=0.0, max_value=70000.0, step=10.0)

        with r1_c2:
            val_tc = st.number_input("Total Coliform (MPN/100ml):", value=float(default_vals['total_coliform']), min_value=0.0, max_value=1e8, step=50.0, help="Statutory Pristine: <= 50 | Bathing: <= 500 | Treated: <= 5000")
            val_fc = st.number_input("Fecal Coliform (MPN/100ml):", value=float(default_vals['fecal_coliform']), min_value=0.0, max_value=1e8, step=20.0)
            val_nitrate = st.number_input("Nitrate-N (mg/L):", value=float(default_vals['nitrate']), min_value=0.0, max_value=150.0, step=0.1, help="Drinking Standard Limit: 45.0 mg/L")
            val_temp = st.number_input("Water Temperature (°C):", value=float(default_vals['temperature']), min_value=5.0, max_value=50.0, step=0.5)

        eval_btn = st.button("🔬 Analyze Water Quality", type="primary", use_container_width=True)

    with col2:
        st.subheader("2. Quality Assessment & Triage")
        # Prepare payload
        input_measurements = {
            'dissolved_oxygen': val_do,
            'ph': val_ph,
            'bod': val_bod,
            'conductivity': val_cond,
            'nitrate': val_nitrate,
            'total_coliform': val_tc,
            'temperature': val_temp,
            'fecal_coliform': val_fc
        }

        # Run prediction
        res = predict_water(input_measurements)

        if res['status'] == 'success':
            pred_cls = res['predicted_class']
            conf = res['confidence']
            wqi = res['wqi_score']
            risk = res['risk_level']

            # Badge selection
            badge_class = "badge-critical" if pred_cls == "Critical" else (
                "badge-class-a" if pred_cls == "Class A" else (
                    "badge-class-b" if pred_cls == "Class B" else (
                        "badge-class-c" if pred_cls == "Class C" else "badge-class-d"
                    )
                )
            )

            st.markdown(f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 18px; font-weight: 700; color: #0f172a;">CPCB Classification</span>
                    <span class="{badge_class}">{pred_cls}</span>
                </div>
                <div style="font-size: 13px; color: #475569; margin-top: 8px;"><b>Designation:</b> {res['class_description']}</div>
                <div style="font-size: 13px; color: #475569; margin-top: 4px;"><b>Model Confidence:</b> {conf:.1%} | <b>Risk Tier:</b> {risk}</div>
            </div>
            """, unsafe_allow_html=True)

            m1, m2 = st.columns(2)
            with m1:
                st.metric("Water Quality Index (WQI)", f"{wqi:.1f}" if wqi else "N/A",
                          delta="Polluted (>100)" if wqi and wqi > 100 else ("Good (<50)" if wqi and wqi < 50 else "Moderate"),
                          delta_color="inverse")
            with m2:
                st.metric("Safety Rating", "UNFIT / DANGER" if pred_cls == "Critical" else ("RESTRICTED" if pred_cls in ["Class C", "Class D/E"] else "SAFE"))

            # Limiting Factors
            st.markdown("##### ⚠️ Explainable Limiting Factor Violations:")
            if res['limiting_factors']:
                for lf in res['limiting_factors']:
                    st.warning(f"**{lf['parameter']}**: Observed `{lf['observed_value']}` against standard `{lf['threshold']}`.\n*Impact:* {lf['impact']}")
            else:
                st.success("✅ All evaluated parameters meet standard outdoor recreational and drinking thresholds.")

            st.markdown("##### 🛠️ Remediation Guidance:")
            for rec in res['recommendations']:
                st.info(f"• {rec}")

            # One-click Database Log
            st.markdown("---")
            with st.expander("📌 File Water Quality Incident Ticket to Database"):
                with st.form("log_water_report_form"):
                    w_loc = st.text_input("Station / Water Body Name:", value=selected_scenario if selected_scenario != "Custom Input" else "River Basin Station #1")
                    w_sev = "Critical" if pred_cls == "Critical" else ("High" if pred_cls == "Class D/E" else "Medium")
                    w_notes = st.text_area("Field Assessment Notes:", value=f"Predicted {pred_cls} (WQI {wqi}). Flagged {len(res['limiting_factors'])} threshold violations.")
                    submit_water_ticket = st.form_submit_button("Submit Water Ticket", use_container_width=True)
                    if submit_water_ticket:
                        wid = create_report(
                            report_type="water",
                            location_name=w_loc,
                            water_measurements=input_measurements,
                            predicted_water_class=pred_cls,
                            wqi_score=wqi,
                            severity_level=w_sev,
                            reviewer_notes=w_notes
                        )
                        st.success(f"Water Monitoring Ticket #{wid} logged successfully!")

# =============================================================================
# PAGE 3: PRIORITY HOTSPOT ENGINE
# =============================================================================
elif app_mode == "⚠️ Priority Hotspot Engine":
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">⚠️ Environmental Risk Prioritization Engine</h1>
        <div class="hero-subtitle">Explainable multi-factor triage score (0–100) aggregating severity, recurring dump frequency, ticket aging, and water proximity.</div>
    </div>
    """, unsafe_allow_html=True)

    # Fetch all reports
    raw_reports = get_all_reports(limit=200)
    if not raw_reports:
        st.warning("No incident reports found in database. Seed sample reports or file new tickets.")
    else:
        ranked_reports = prioritize_all_reports(raw_reports)

        # Overview Metrics
        m1, m2, m3, m4 = st.columns(4)
        crit_count = sum(1 for r in ranked_reports if r['priority_tier'] == 'Critical Attention')
        high_count = sum(1 for r in ranked_reports if r['priority_tier'] == 'High Priority')
        mod_count = sum(1 for r in ranked_reports if r['priority_tier'] == 'Moderate Priority')
        res_count = sum(1 for r in ranked_reports if r['status'] == 'Resolved')

        with m1:
            st.metric("Critical Hotspots", crit_count)
        with m2:
            st.metric("High Priority", high_count)
        with m3:
            st.metric("Moderate Priority", mod_count)
        with m4:
            st.metric("Resolved Tickets", res_count)

        # Filters
        st.markdown("---")
        fc1, fc2 = st.columns(2)
        with fc1:
            filter_status = st.multiselect("Filter by Status:", VALID_STATUSES, default=["Reported", "Under Review", "Cleanup Assigned"])
        with fc2:
            filter_tier = st.multiselect("Filter by Triage Tier:", ["Critical Attention", "High Priority", "Moderate Priority", "Low Priority", "Resolved"], default=["Critical Attention", "High Priority", "Moderate Priority"])

        filtered = [
            r for r in ranked_reports
            if (not filter_status or r['status'] in filter_status) and
               (not filter_tier or r['priority_tier'] in filter_tier)
        ]

        st.subheader(f"Ranked Incident Hotspots ({len(filtered)} items)")

        for r in filtered:
            tier_class = "tier-critical" if r['priority_tier'] == "Critical Attention" else (
                "tier-high" if r['priority_tier'] == "High Priority" else (
                    "tier-moderate" if r['priority_tier'] == "Moderate Priority" else "tier-low"
                )
            )

            with st.expander(f"📍 #{r['id']} — {r['location_name']} | Score: {r['priority_score']:.1f} ({r['priority_tier']}) | Status: {r['status']}"):
                col_a, col_b = st.columns([1.2, 1])
                with col_a:
                    st.markdown(f"**Location:** `{r['location_name']}` (Type: `{r['report_type'].upper()}`)")
                    st.markdown(f"**Filed At:** `{r['timestamp']}`")
                    st.markdown(f"**Triage Narrative:** {r['explanation_narrative']}")
                    st.markdown(f"**Recommended Field Action:** `{r['recommended_action']}`")
                    if r.get('reviewer_notes'):
                        st.info(f"**Reviewer Notes:** {r['reviewer_notes']}")

                with col_b:
                    st.markdown("##### 🧮 Mathematical Factor Breakdown:")
                    fb = r['factor_breakdown']
                    breakdown_df = pd.DataFrame([
                        {"Factor": "Severity Weight", "Points": f"{fb['severity_points']:.1f} / 35.0"},
                        {"Factor": "Location Recurrence", "Points": f"{fb['recurrence_points']:.1f} / 25.0"},
                        {"Factor": "Aging Penalty", "Points": f"{fb['age_penalty_points']:.1f} / 20.0"},
                        {"Factor": "Ecological / Water Interface", "Points": f"{fb['ecological_sensitivity_points']:.1f} / 20.0"},
                    ])
                    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

# =============================================================================
# PAGE 4: INCIDENT & RESOLUTION TRACKING
# =============================================================================
elif app_mode == "📋 Incident Tracking (SQLite)":
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">📋 Incident & Resolution Tracking</h1>
        <div class="hero-subtitle">End-to-end lifecycle management: Reported ➔ Under Review ➔ Cleanup Assigned ➔ Resolved with photographic evidence.</div>
    </div>
    """, unsafe_allow_html=True)

    tab_view, tab_update, tab_create = st.tabs(["📑 All Active Tickets", "🔄 Update Ticket Status", "➕ File New Report"])

    with tab_view:
        all_reps = get_all_reports(limit=200)
        if all_reps:
            rep_table_data = []
            for r in all_reps:
                rep_table_data.append({
                    "Ticket ID": r['id'],
                    "Type": r['report_type'].upper(),
                    "Location": r['location_name'],
                    "Severity": r['severity_level'],
                    "Status": r['status'],
                    "Human Verified": "✅ Yes" if r['human_verified'] else "⏳ Pending",
                    "Timestamp": r['timestamp'][:16].replace("T", " ")
                })
            st.dataframe(pd.DataFrame(rep_table_data), use_container_width=True, hide_index=True)
        else:
            st.info("No reports found.")

    with tab_update:
        st.subheader("Update Ticket Lifecycle Status")
        tickets = get_all_reports(limit=100)
        ticket_options = {f"#{t['id']} — {t['location_name']} ({t['status']})": t['id'] for t in tickets}

        if ticket_options:
            sel_ticket_label = st.selectbox("Select Ticket to Modify:", list(ticket_options.keys()))
            selected_ticket_id = ticket_options[sel_ticket_label]
            current_ticket = get_report_by_id(selected_ticket_id)

            if current_ticket:
                st.markdown(f"**Current Status:** `{current_ticket['status']}` | **Severity:** `{current_ticket['severity_level']}` | **Location:** `{current_ticket['location_name']}`")
                
                with st.form("status_update_form"):
                    next_status = st.selectbox("Assign New Status:", VALID_STATUSES, index=VALID_STATUSES.index(current_ticket['status']))
                    status_notes = st.text_area("Audit Notes / Contractor Progress / Resolution Details:", value=f"Updated to {next_status}")
                    verified_check = st.checkbox("Mark as Human Verified", value=bool(current_ticket['human_verified']))
                    
                    submitted = st.form_submit_button("Save Status Transition", use_container_width=True)
                    if submitted:
                        update_report_status(selected_ticket_id, next_status, notes=status_notes)
                        update_human_verification(selected_ticket_id, verified=verified_check, reviewer_notes=status_notes)
                        st.success(f"Ticket #{selected_ticket_id} updated to '{next_status}'!")
                        st.rerun()

                # View Audit History Trail
                st.markdown("##### 📜 Audit History Trail:")
                if current_ticket.get('status_history'):
                    hist_df = pd.DataFrame([
                        {
                            "Step": i + 1,
                            "Transition": f"{h.get('old_status') or 'Created'} ➔ {h['new_status']}",
                            "Timestamp": h['timestamp'][:19].replace("T", " "),
                            "Notes": h.get('notes') or ""
                        }
                        for i, h in enumerate(current_ticket['status_history'])
                    ])
                    st.dataframe(hist_df, use_container_width=True, hide_index=True)

    with tab_create:
        st.subheader("Manually File an Incident Ticket")
        with st.form("create_new_incident_form"):
            new_type = st.selectbox("Incident Type:", ["waste", "water", "combined"])
            new_loc = st.text_input("Location Name / Landmark:", value="Lake Berm Walkway")
            c1, c2 = st.columns(2)
            with c1:
                new_lat = st.number_input("Latitude:", value=13.0827, format="%.4f")
            with c2:
                new_lon = st.number_input("Longitude:", value=80.2707, format="%.4f")
            new_sev = st.selectbox("Severity Rating:", ["Low", "Medium", "High", "Critical"], index=1)
            new_notes = st.text_area("Observer Notes:")
            create_btn = st.form_submit_button("Submit Incident", use_container_width=True)
            if create_btn:
                nid = create_report(
                    report_type=new_type,
                    location_name=new_loc,
                    latitude=new_lat,
                    longitude=new_lon,
                    severity_level=new_sev,
                    reviewer_notes=new_notes
                )
                st.success(f"New incident ticket #{nid} created successfully!")
                st.rerun()

# =============================================================================
# PAGE 5: ANALYTICS & MODEL CARDS
# =============================================================================
elif app_mode == "📊 Analytics & Model Cards":
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">📊 Analytics & Academic Model Cards</h1>
        <div class="hero-subtitle">Comprehensive model performance metrics, confusion matrices, and environmental feature importances.</div>
    </div>
    """, unsafe_allow_html=True)

    tab_waste_m, tab_water_m = st.tabs(["🛰️ Waste Model (YOLO11n)", "💧 Water Model (CPCB Random Forest)"])

    with tab_waste_m:
        st.subheader("Waste Detection Model (YOLO11n Nano)")
        m_json_path = Path("outputs/evaluation/waste_metrics.json")
        if m_json_path.exists():
            with open(m_json_path, 'r') as f:
                w_metrics = json.load(f)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Architecture", w_metrics.get('model', 'YOLO11n'))
            with c2:
                st.metric("Classes", w_metrics.get('num_classes', 4))
            with c3:
                st.metric("Image Size", f"{w_metrics.get('imgsz', 320)}px")
            with c4:
                st.metric("Device", w_metrics.get('device', 'CPU'))

        c_img1, c_img2 = st.columns(2)
        with c_img1:
            cm_waste = Path("outputs/evaluation/waste_confusion_matrix.png")
            if cm_waste.exists():
                st.image(str(cm_waste), caption="Waste Model Confusion Matrix", use_container_width=True)
        with c_img2:
            res_waste = Path("outputs/evaluation/waste_results.png")
            if res_waste.exists():
                st.image(str(res_waste), caption="Waste Training Curves & Loss", use_container_width=True)

    with tab_water_m:
        st.subheader("Water Intelligence Model (CPCB Classifier)")
        water_m_path = Path("outputs/evaluation/water_metrics.json")
        if water_m_path.exists():
            with open(water_m_path, 'r') as f:
                water_metrics = json.load(f)
            
            t_met = water_metrics['test_metrics']
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Test Accuracy", f"{t_met['accuracy']:.2%}")
            with c2:
                st.metric("Macro F1-Score", f"{t_met['macro_f1']:.4f}")
            with c3:
                st.metric("Weighted F1-Score", f"{t_met['weighted_f1']:.4f}")
            with c4:
                st.metric("Evaluated Test Samples", sum(water_metrics['per_class_metrics'][c]['support'] for c in water_metrics['per_class_metrics']))

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            cm_water = Path("outputs/evaluation/water_confusion_matrix.png")
            if cm_water.exists():
                st.image(str(cm_water), caption="CPCB Water Classification Confusion Matrix", use_container_width=True)
        with col_w2:
            feat_imp = Path("outputs/evaluation/water_feature_importance.png")
            if feat_imp.exists():
                st.image(str(feat_imp), caption="Gini Feature Importance (Environmental Pollutants)", use_container_width=True)

        st.markdown("---")
        long_trend = Path("outputs/data_audit/water_temporal_trends.png")
        if long_trend.exists():
            st.image(str(long_trend), caption="Longitudinal CPCB Monitoring Volumes & Parameters Over Time", use_container_width=True)

# =============================================================================
# PAGE 6: SYSTEM OVERVIEW
# =============================================================================
elif app_mode == "ℹ️ System Overview":
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">ℹ️ System Overview & Academic Architecture</h1>
        <div class="hero-subtitle">EcoSentinel AI: AI-Powered Smart Waste and Water Monitoring, Analysis, and Environmental Risk Prioritization System.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### Project Mission
    **EcoSentinel AI** integrates visible waste image detection and water quality analysis into a unified environmental monitoring workflow.
    It transitions from isolated ML predictions into an explainable **Decision Support System** that helps sanitation and water teams triage and resolve real-world environmental hazards.

    ---
    ### Core System Modules
    1. **Waste Intelligence (YOLO11n):**
       * Detects 4 core litter categories (`Bottle`, `Plastic_bag`, `Can`, `Cup`) from photographic evidence.
       * Generates bounding boxes, confidence scores, and categorical count distributions.
    2. **Water Intelligence (CPCB Classifier & WQI Engine):**
       * Evaluates 8 key physicochemical parameters: Dissolved Oxygen, BOD, pH, Electrical Conductivity, Total Coliform, Nitrate, Fecal Coliform, and Temperature.
       * Predicts statutory **CPCB Designated Best Use Classes** (`Class A` to `Critical`) and calculates **Weighted Arithmetic WQI**.
       * Identifies specific parameter safety threshold violations with actionable mitigation recommendations.
    3. **Environmental Risk Prioritization Engine:**
       * Transparent heuristic score ($0 - 100$) combining **Severity**, **Location Recurrence**, **Ticket Aging Delay**, and **Ecological Water Interface Sensitivity**.
    4. **Report & Resolution Tracking (SQLite):**
       * Audited lifecycle progression: `Reported` $\rightarrow$ `Under Review` $\rightarrow$ `Cleanup Assigned` $\rightarrow$ `Resolved`.
       * Preserves human verification separate from raw model predictions.

    ---
    ### Responsible Use & Limitations
    > **⚠️ Academic & Decision Support Notice:**
    > * EcoSentinel AI is an assistive decision-support triage aid. It is **not** a legal substitute for accredited laboratory water testing or statutory regulatory authorities.
    > * Prioritization scores are prototype triage heuristics, not scientifically certified environmental contamination forecasts.
    """)
