import React from 'react';
import { 
  HelpCircle, 
  Trash2, 
  Droplets, 
  AlertTriangle, 
  Database, 
  LayoutDashboard, 
  ArrowRight,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

export default function WorkflowGuide({ setTab }) {
  const steps = [
    {
      num: "01",
      title: "Field Data Capture & Ingestion",
      icon: LayoutDashboard,
      color: "#3b82f6",
      desc: "Raw environmental observations are collected from drone cameras, public field inspection photos, or water sensor telemetry (chemical parameters like DO, pH, BOD, Coliform)."
    },
    {
      num: "02",
      title: "Dual Machine Learning Intelligence",
      icon: Trash2,
      color: "#10b981",
      desc: "Waste photos pass through our fine-tuned YOLO11n model to detect plastic bottles, bags, and cans with bounding boxes. Water chemical measurements pass through our CPCB Random Forest model to calculate the Water Quality Index (WQI) and legal best-use classes."
    },
    {
      num: "03",
      title: "Explainable Hotspot Prioritization",
      icon: AlertTriangle,
      color: "#f59e0b",
      desc: "Because municipal cleanup crews have limited bandwidth, our heuristic engine ranks incidents (0–100 pts) evaluating report recurrence, age of unresolved tickets, human severity, and total contaminant volume."
    },
    {
      num: "04",
      title: "SQLite Persistence & Audit Trail",
      icon: Database,
      color: "#06b6d4",
      desc: "Incident tickets are saved into an SQLite database (ecosentinel.db) with a full status lifecycle: Reported ➔ Under Review ➔ Cleanup Assigned ➔ Remediated, ensuring full civic accountability."
    },
    {
      num: "05",
      title: "Modern Command & Triage Portal",
      icon: ShieldCheck,
      color: "#a855f7",
      desc: "Environmental officers and field workers inspect live telemetry, adjust detection thresholds, trigger dispatch assignments, and view empirical model cards via this React portal."
    }
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <HelpCircle className="text-emerald-400" size={30} color="#10b981" />
            Project Architecture & Workflow Guide
          </h1>
          <p className="page-subtitle">
            A comprehensive, transparent walkthrough of the EcoSentinel AI intelligent environmental grid.
          </p>
        </div>
      </div>

      {/* 5-Step Pipeline Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
        {steps.map((s) => {
          const Icon = s.icon;
          return (
            <div 
              key={s.num} 
              className="glass-card"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '24px',
                padding: '20px 24px'
              }}
            >
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '28px',
                fontWeight: '800',
                color: s.color,
                opacity: 0.9,
                minWidth: '40px'
              }}>
                {s.num}
              </div>

              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255, 255, 255, 0.05)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: s.color,
                flexShrink: 0
              }}>
                <Icon size={24} />
              </div>

              <div style={{ flex: 1 }}>
                <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', color: 'var(--text-primary)' }}>
                  {s.title}
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px', lineHeight: '1.5' }}>
                  {s.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Mathematical Hotspot Formula Card */}
      <div className="glass-card" style={{ marginBottom: '32px' }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: '700', marginBottom: '10px' }}>
          📐 Transparent Hotspot Scoring Formula
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
          In real-world municipal governance, black-box AI is unacceptable. EcoSentinel AI provides a deterministic, explainable heuristic score:
        </p>

        <div style={{
          padding: '16px',
          background: 'rgba(15, 23, 42, 0.8)',
          borderRadius: 'var(--radius-md)',
          fontFamily: 'var(--font-mono)',
          fontSize: '14px',
          color: 'var(--emerald-400)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '16px'
        }}>
          Score = [ Severity (max 35) + Recurrence (max 25) + Age (max 20) + Volume Load (max 20) ] × Status_Penalty
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', fontSize: '13px' }}>
          <div style={{ padding: '12px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: 'var(--radius-sm)' }}>
            <strong>Severity (0 - 35 pts)</strong>
            <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Critical: 35 | High: 25 | Medium: 15 | Low: 5</div>
          </div>
          <div style={{ padding: '12px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: 'var(--radius-sm)' }}>
            <strong>Recurrence (0 - 25 pts)</strong>
            <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Repeated dumps at the same landmark scale up to 25 pts</div>
          </div>
          <div style={{ padding: '12px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: 'var(--radius-sm)' }}>
            <strong>Age Factor (0 - 20 pts)</strong>
            <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Older unaddressed tickets gain points daily (1 pt/day)</div>
          </div>
          <div style={{ padding: '12px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: 'var(--radius-sm)' }}>
            <strong>Status Factor (Multiplier)</strong>
            <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Active: 1.0x | Cleanup Assigned: 0.5x | Resolved: 0.0x</div>
          </div>
        </div>
      </div>

      {/* CPCB Classification Reference */}
      <div className="glass-card">
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: '700', marginBottom: '14px' }}>
          💧 Central Pollution Control Board (CPCB) Statutory Best-Use Classes
        </h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Class</th>
                <th>Designated Best Use</th>
                <th>Dissolved Oxygen</th>
                <th>BOD (5-day 20°C)</th>
                <th>Total Coliform (MPN/100mL)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><span className="badge badge-class-a">Class A</span></td>
                <td>Drinking water source without conventional treatment (disinfection only)</td>
                <td>≥ 6.0 mg/L</td>
                <td>≤ 2.0 mg/L</td>
                <td>≤ 50</td>
              </tr>
              <tr>
                <td><span className="badge badge-class-b">Class B</span></td>
                <td>Outdoor bathing (organized)</td>
                <td>≥ 5.0 mg/L</td>
                <td>≤ 3.0 mg/L</td>
                <td>≤ 500</td>
              </tr>
              <tr>
                <td><span className="badge badge-class-c">Class C</span></td>
                <td>Drinking water source with conventional treatment and disinfection</td>
                <td>≥ 4.0 mg/L</td>
                <td>≤ 3.0 mg/L</td>
                <td>≤ 5000</td>
              </tr>
              <tr>
                <td><span className="badge badge-class-d">Class D/E</span></td>
                <td>Fish culture, wildlife propagation, agriculture, industrial cooling</td>
                <td>≥ 4.0 mg/L</td>
                <td>No standard</td>
                <td>Free standard</td>
              </tr>
              <tr>
                <td><span className="badge badge-critical">Critical</span></td>
                <td>Severely contaminated / untreated industrial sewage toxic outfall</td>
                <td>&lt; 3.0 mg/L</td>
                <td>&gt; 6.0 mg/L</td>
                <td>&gt; 5000</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
