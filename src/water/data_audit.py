"""
EcoSentinel AI - Water Data Audit Module
Inspects raw Indian CPCB surface water quality dataset, validates schemas,
detects missing values and sentinel strings (e.g. 'NAN'), identifies range anomalies (e.g. pH errors),
analyzes parameter distributions and correlations, and generates visual audit artifacts.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend for background execution
import matplotlib.pyplot as plt
import seaborn as sns

# Column mapping from raw CPCB export to clean standard feature names
RAW_COLUMN_MAP = {
    'STATION CODE': 'station_code',
    'LOCATIONS': 'location',
    'STATE': 'state',
    'Temp': 'temperature',
    'D.O. (mg/l)': 'dissolved_oxygen',
    'PH': 'ph',
    'CONDUCTIVITY (\xb5mhos/cm)': 'conductivity',
    'CONDUCTIVITY (\ufffdmhos/cm)': 'conductivity',
    'B.O.D. (mg/l)': 'bod',
    'NITRATENAN N+ NITRITENANN (mg/l)': 'nitrate',
    'FECAL COLIFORM (MPN/100ml)': 'fecal_coliform',
    'TOTAL COLIFORM (MPN/100ml)Mean': 'total_coliform',
    'year': 'year'
}

NUMERIC_FEATURES = [
    'temperature',
    'dissolved_oxygen',
    'ph',
    'conductivity',
    'bod',
    'nitrate',
    'fecal_coliform',
    'total_coliform'
]


def load_and_standardize_raw_data(raw_csv_path="data/raw/water/cpcb_water_quality.csv"):
    """
    Loads raw CPCB CSV, standardizes column names, and converts numeric columns
    while identifying missing/sentinel entries.
    """
    raw_path = Path(raw_csv_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw water dataset not found at {raw_path}")

    # Read with latin1 encoding to handle degree symbols / mu micro characters
    df = pd.read_csv(raw_path, encoding='latin1')

    # Rename known columns
    rename_dict = {}
    for col in df.columns:
        col_clean = col.strip()
        matched = False
        for raw_k, clean_v in RAW_COLUMN_MAP.items():
            if raw_k in col_clean or clean_v in col_clean.lower():
                rename_dict[col] = clean_v
                matched = True
                break
        if not matched:
            if 'conduct' in col_clean.lower():
                rename_dict[col] = 'conductivity'
            elif 'nitrat' in col_clean.lower():
                rename_dict[col] = 'nitrate'
            elif 'fecal' in col_clean.lower():
                rename_dict[col] = 'fecal_coliform'
            elif 'total coliform' in col_clean.lower():
                rename_dict[col] = 'total_coliform'
            elif 'd.o' in col_clean.lower():
                rename_dict[col] = 'dissolved_oxygen'
            elif 'b.o.d' in col_clean.lower():
                rename_dict[col] = 'bod'
            elif 'temp' in col_clean.lower():
                rename_dict[col] = 'temperature'

    df = df.rename(columns=rename_dict)
    return df


def audit_water_dataset(
    raw_csv_path="data/raw/water/cpcb_water_quality.csv",
    output_dir="outputs/data_audit"
):
    """
    Performs comprehensive exploratory audit on the CPCB surface water quality dataset.
    Generates summary report JSON and high-resolution audit visualizations.
    """
    raw_csv_path = Path(raw_csv_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60, flush=True)
    print("ECOSENTINEL AI - WATER DATA AUDIT (CPCB SURFACE WATER)", flush=True)
    print("=" * 60, flush=True)

    df_raw = load_and_standardize_raw_data(raw_csv_path)
    total_records = len(df_raw)
    total_columns = len(df_raw.columns)
    print(f"Total Raw Records: {total_records} | Columns: {total_columns}", flush=True)

    # 1. Missing and Sentinel Value Audit
    missing_audit = {}
    numeric_df = pd.DataFrame()

    for col in NUMERIC_FEATURES:
        if col in df_raw.columns:
            # Check string sentinel counts before coercion
            raw_series = df_raw[col].astype(str).str.strip().str.upper()
            sentinel_nan_count = int((raw_series.isin(['NAN', 'NULL', 'NA', '?', '', 'NONE'])).sum())
            
            # Numeric conversion
            converted = pd.to_numeric(df_raw[col], errors='coerce')
            numeric_df[col] = converted
            
            total_missing = int(converted.isna().sum())
            missing_pct = round((total_missing / total_records) * 100, 2)
            
            missing_audit[col] = {
                'valid_count': int(converted.notnull().sum()),
                'missing_count': total_missing,
                'missing_pct': missing_pct,
                'sentinel_nan_strings': sentinel_nan_count,
                'min': float(converted.min()) if converted.notnull().any() else None,
                'median': float(converted.median()) if converted.notnull().any() else None,
                'mean': float(converted.mean()) if converted.notnull().any() else None,
                'max': float(converted.max()) if converted.notnull().any() else None,
                'std': float(converted.std()) if converted.notnull().any() else None
            }

    # 2. Domain Anomaly Checks (CPCB physical criteria)
    anomalies = {
        'ph_out_of_range': int(((numeric_df['ph'] < 0) | (numeric_df['ph'] > 14)).sum()),
        'negative_do': int((numeric_df['dissolved_oxygen'] < 0).sum()),
        'negative_bod': int((numeric_df['bod'] < 0).sum()),
        'extreme_conductivity': int((numeric_df['conductivity'] > 50000).sum()),
        'extreme_coliform': int((numeric_df['total_coliform'] > 1e7).sum())
    }

    # Cleaned numeric for statistical plots (filter obvious physical outliers like pH > 14)
    numeric_clean = numeric_df.copy()
    numeric_clean.loc[(numeric_clean['ph'] < 0) | (numeric_clean['ph'] > 14), 'ph'] = np.nan

    # 3. Temporal Coverage Audit
    year_distribution = {}
    if 'year' in df_raw.columns:
        year_counts = df_raw['year'].value_counts().sort_index()
        year_distribution = {str(k): int(v) for k, v in year_counts.items()}

    # 4. State / Spatial Coverage Audit
    state_distribution = {}
    if 'state' in df_raw.columns:
        top_states = df_raw['state'].value_counts().head(10)
        state_distribution = {str(k): int(v) for k, v in top_states.items()}

    # 5. CPCB Class Distribution Simulation
    def get_cpcb_class(row):
        do = row.get('dissolved_oxygen')
        bod = row.get('bod')
        ph = row.get('ph')
        tc = row.get('total_coliform')
        if pd.isna(do) or pd.isna(bod) or pd.isna(ph):
            return 'Unclassified_Missing_Params'
        if do >= 6.0 and bod <= 2.0 and (6.5 <= ph <= 8.5) and (pd.isna(tc) or tc <= 50):
            return 'Class A (Pristine Drinking)'
        elif do >= 5.0 and bod <= 3.0 and (6.5 <= ph <= 8.5) and (pd.isna(tc) or tc <= 500):
            return 'Class B (Outdoor Bathing)'
        elif do >= 4.0 and bod <= 3.0 and (6.0 <= ph <= 9.0) and (pd.isna(tc) or tc <= 5000):
            return 'Class C (Conventional Treatment)'
        elif do >= 4.0 and (6.0 <= ph <= 8.5) and bod <= 6.0:
            return 'Class D/E (Wildlife/Irrigation)'
        else:
            return 'Critical (Polluted / Non-Compliant)'

    classes = numeric_clean.apply(get_cpcb_class, axis=1)
    class_counts = {str(k): int(v) for k, v in classes.value_counts().items()}

    # =========================================================================
    # Visualizations
    # =========================================================================
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    palette = sns.color_palette("deep")

    # Plot 1: Feature Distributions (Histograms + Boxplots)
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    axes = axes.flatten()

    features_to_plot = [
        ('dissolved_oxygen', 'Dissolved Oxygen (mg/L)', [0, 14]),
        ('ph', 'pH (0 - 14)', [4, 10]),
        ('bod', 'BOD (mg/L, log scale)', None),
        ('conductivity', 'Conductivity (µmhos/cm, log scale)', None),
        ('temperature', 'Temperature (°C)', [10, 40]),
        ('nitrate', 'Nitrate (mg/L)', [0, 20]),
        ('fecal_coliform', 'Fecal Coliform (log scale)', None),
        ('total_coliform', 'Total Coliform (log scale)', None),
    ]

    for i, (col, title, xlim) in enumerate(features_to_plot):
        ax = axes[i]
        vals = numeric_clean[col].dropna()
        if len(vals) > 0:
            if 'log scale' in title:
                vals_plot = np.log10(vals[vals > 0] + 1)
                sns.histplot(vals_plot, kde=True, ax=ax, color=palette[i % len(palette)])
                ax.set_xlabel(f"log10({col} + 1)")
            else:
                sns.histplot(vals, kde=True, ax=ax, color=palette[i % len(palette)])
                ax.set_xlabel(col)
            if xlim:
                ax.set_xlim(xlim)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_ylabel("Frequency")

    plt.suptitle("EcoSentinel AI — CPCB Surface Water Parameter Distributions", fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    dist_plot_path = output_dir / "water_feature_distributions.png"
    plt.savefig(dist_plot_path, dpi=200, bbox_inches='tight')
    plt.close()

    # Plot 2: Correlation Matrix Heatmap
    plt.figure(figsize=(9, 7))
    corr_cols = ['dissolved_oxygen', 'ph', 'conductivity', 'bod', 'nitrate', 'total_coliform', 'temperature']
    corr_df = numeric_clean[corr_cols].dropna()
    corr_matrix = corr_df.corr(method='spearman')
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, linewidths=0.5)
    plt.title("Water Quality Parameters Spearman Correlation Heatmap", fontsize=13, fontweight='bold')
    plt.tight_layout()
    corr_plot_path = output_dir / "water_correlation_matrix.png"
    plt.savefig(corr_plot_path, dpi=200, bbox_inches='tight')
    plt.close()

    # Plot 3: CPCB Target Class Distribution
    plt.figure(figsize=(10, 5.5))
    class_order = [
        'Class A (Pristine Drinking)',
        'Class B (Outdoor Bathing)',
        'Class C (Conventional Treatment)',
        'Class D/E (Wildlife/Irrigation)',
        'Critical (Polluted / Non-Compliant)',
        'Unclassified_Missing_Params'
    ]
    plot_labels = [c for c in class_order if c in class_counts]
    plot_vals = [class_counts[c] for c in plot_labels]
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e67e22', '#e74c3c', '#95a5a6'][:len(plot_labels)]

    bars = plt.bar(plot_labels, plot_vals, color=colors, edgecolor='black', linewidth=1)
    plt.title("CPCB Designated Best Use Water Quality Classification Distribution", fontsize=13, fontweight='bold')
    plt.ylabel("Number of Monitoring Observations", fontsize=11)
    plt.xticks(rotation=20, ha='right', fontsize=10)
    for bar in bars:
        height = bar.get_height()
        pct = (height / total_records) * 100
        plt.text(bar.get_x() + bar.get_width()/2., height + 15, f"{height} ({pct:.1f}%)", ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.ylim(0, max(plot_vals) * 1.15)
    plt.tight_layout()
    class_plot_path = output_dir / "water_class_distribution.png"
    plt.savefig(class_plot_path, dpi=200, bbox_inches='tight')
    plt.close()

    # Plot 4: Temporal Trend (Yearly monitoring volume & DO/BOD trends)
    if 'year' in df_raw.columns:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        years_sorted = sorted([int(y) for y in year_distribution.keys()])
        yearly_counts = [year_distribution[str(y)] for y in years_sorted]

        ax1.bar(years_sorted, yearly_counts, color='#bdc3c7', alpha=0.6, label='Observations Count')
        ax1.set_xlabel("Year", fontsize=11)
        ax1.set_ylabel("Monitoring Stations Sampled", fontsize=11, color='#2c3e50')
        ax1.tick_params(axis='y', labelcolor='#2c3e50')

        # Overlay mean DO and BOD
        ax2 = ax1.twinx()
        yearly_means = df_raw.assign(
            do_num=numeric_clean['dissolved_oxygen'],
            bod_num=numeric_clean['bod']
        ).groupby('year')[['do_num', 'bod_num']].mean().reindex(years_sorted)

        ax2.plot(years_sorted, yearly_means['do_num'], color='#27ae60', marker='o', linewidth=2.5, label='Mean DO (mg/L)')
        ax2.plot(years_sorted, yearly_means['bod_num'], color='#c0392b', marker='s', linewidth=2.5, label='Mean BOD (mg/L)')
        ax2.set_ylabel("Mean Parameter Value (mg/L)", fontsize=11, color='#2c3e50')
        ax2.tick_params(axis='y', labelcolor='#2c3e50')

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.title("CPCB Monitoring Network: Longitudinal Volume & Key Parameter Trends", fontsize=13, fontweight='bold')
        plt.tight_layout()
        trend_plot_path = output_dir / "water_temporal_trends.png"
        plt.savefig(trend_plot_path, dpi=200, bbox_inches='tight')
        plt.close()
    else:
        trend_plot_path = None

    # Compile JSON Audit Report
    audit_report = {
        'dataset_name': 'CPCB Indian Surface Water Quality Monitoring Data',
        'raw_source_path': str(raw_csv_path),
        'total_records': total_records,
        'total_columns': total_columns,
        'features_audited': NUMERIC_FEATURES,
        'missing_and_sentinels': missing_audit,
        'domain_anomalies': anomalies,
        'temporal_coverage': year_distribution,
        'top_states': state_distribution,
        'cpcb_class_distribution': class_counts,
        'audit_visualizations': {
            'distributions': str(dist_plot_path),
            'correlation_matrix': str(corr_plot_path),
            'class_distribution': str(class_plot_path),
            'temporal_trends': str(trend_plot_path) if trend_plot_path else None
        }
    }

    report_json_path = output_dir / "water_audit_report.json"
    with open(report_json_path, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=4)

    print(f"Water audit report written to: {report_json_path}", flush=True)
    print(f"Visualizations saved to: {output_dir}", flush=True)
    print("=" * 60, flush=True)
    return audit_report


if __name__ == "__main__":
    audit_water_dataset()
