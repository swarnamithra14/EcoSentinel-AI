import React, { useState, useEffect } from 'react';
import { 
  Droplets, 
  Sparkles, 
  AlertTriangle, 
  CheckCircle, 
  FileCheck, 
  HelpCircle,
  ShieldCheck,
  TrendingDown
} from 'lucide-react';

const PRESET_SCENARIOS = {
  "Himalayan Headwater Stream (Pristine)": {
    dissolved_oxygen: 7.8, ph: 7.4, bod: 1.2, conductivity: 95.0,
    nitrate: 0.15, total_coliform: 24.0, temperature: 14.5, fecal_coliform: 6.0
  },
  "Recreational Bathing Ghat (Ganga)": {
    dissolved_oxygen: 6.4, ph: 7.5, bod: 2.4, conductivity: 180.0,
    nitrate: 0.45, total_coliform: 320.0, temperature: 22.0, fecal_coliform: 90.0
  },
  "Municipal Raw Drinking Intake (Kaveri)": {
    dissolved_oxygen: 5.5, ph: 7.2, bod: 2.8, conductivity: 380.0,
    nitrate: 1.20, total_coliform: 2400.0, temperature: 28.0, fecal_coliform: 450.0
  },
  "Agricultural Canal & Wetland (Kuttanad)": {
    dissolved_oxygen: 4.8, ph: 6.8, bod: 4.5, conductivity: 920.0,
    nitrate: 3.80, total_coliform: 850.0, temperature: 29.5, fecal_coliform: 210.0
  },
  "Untreated Urban Sewage Drain (Yamuna)": {
    dissolved_oxygen: 1.2, ph: 6.3, bod: 28.5, conductivity: 2450.0,
    nitrate: 14.2, total_coliform: 48000.0, temperature: 31.0, fecal_coliform: 18000.0
  }
};

export default function WaterLab({ onReportCreated, onTrackTicket }) {
  const [params, setParams] = useState(PRESET_SCENARIOS["Himalayan Headwater Stream (Pristine)"]);
  const [selectedPreset, setSelectedPreset] = useState("Himalayan Headwater Stream (Pristine)");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastTicketId, setLastTicketId] = useState(null);
  const [ticketSuccess, setTicketSuccess] = useState('');
  const [locationName, setLocationName] = useState('Central River Intake / Monitoring Stn 4');
  const [severity, setSeverity] = useState('Medium');

  // Run water inference whenever parameters change (with debounce)
  useEffect(() => {
    const timer = setTimeout(() => {
      runWaterAnalysis();
    }, 250);
    return () => clearTimeout(timer);
  }, [params]);

  const runWaterAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/predict/water', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setResults(data);
        if (data.predicted_class === 'Critical') setSeverity('Critical');
        else if (data.predicted_class === 'Class D/E') setSeverity('High');
        else if (data.predicted_class === 'Class C') setSeverity('Medium');
        else setSeverity('Low');
      }
    } catch (err) {
      console.error("Water analysis failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (presetName) => {
    setSelectedPreset(presetName);
    if (PRESET_SCENARIOS[presetName]) {
      setParams(PRESET_SCENARIOS[presetName]);
    }
  };

  const handleSliderChange = (paramKey, value) => {
    setSelectedPreset('Custom');
    setParams(prev => ({
      ...prev,
      [paramKey]: parseFloat(value)
    }));
  };

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const submitIncidentReport = async (e) => {
    e.preventDefault();
    if (!results) return;

    setSubmitting(true);
    setSubmitError('');
    setTicketSuccess('');

    try {
      const payload = {
        report_type: 'water',
        location_name: locationName,
        latitude: 13.0827,
        longitude: 80.2707,
        wqi_score: results.wqi_score,
        predicted_water_class: results.predicted_class,
        severity_level: severity,
        reviewer_notes: `Predicted ${results.predicted_class} (WQI: ${results.wqi_score}). Limiting factors: ${results.limiting_factors?.map(f => f.parameter).join(', ') || 'None'}.`
      };

      const res = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setLastTicketId(data.report_id);
        setTicketSuccess(`✅ Acknowledged! Incident Ticket #${data.report_id} filed successfully in SQLite database.`);
        if (onReportCreated) onReportCreated();
      } else {
        setSubmitError(data.message || 'Failed to submit report.');
      }
    } catch (err) {
      setSubmitError(`Network error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const getClassBadgeStyle = (cls) => {
    switch (cls) {
      case 'Class A': return 'badge-class-a';
      case 'Class B': return 'badge-class-b';
      case 'Class C': return 'badge-class-c';
      case 'Class D/E': return 'badge-class-d';
      case 'Critical': return 'badge-critical';
      default: return 'badge-low';
    }
  };

  // SVG Gauge calculations
  const wqi = results?.wqi_score || 75;
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (wqi / 100) * circumference;
  
  const getGaugeColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#06b6d4';
    if (score >= 45) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Droplets className="text-cyan-400" size={30} color="#06b6d4" />
            Water Quality Lab
          </h1>
          <p className="page-subtitle">
            Statutory CPCB Designated Best Use classification, Brown et al. WQI engine, and explainable limiting factor alerts.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '28px' }}>
        {/* Left Column: Parameter Sliders & Presets */}
        <div>
          <div className="glass-card" style={{ marginBottom: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '14px' }}>
              1. Chemical & Biological Parameter Sliders
            </h3>

            {/* Benchmark Preset Selector */}
            <div className="form-group">
              <label className="form-label">Load Real-World Benchmark Scenario:</label>
              <select 
                className="form-select"
                value={selectedPreset}
                onChange={(e) => handlePresetSelect(e.target.value)}
              >
                {Object.keys(PRESET_SCENARIOS).map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
                {selectedPreset === 'Custom' && <option value="Custom">Custom Parameter Profile</option>}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '20px' }}>
              {/* Dissolved Oxygen */}
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-name">Dissolved Oxygen (DO):</span>
                  <span className="slider-val">{params.dissolved_oxygen} mg/L</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="14" 
                  step="0.1" 
                  value={params.dissolved_oxygen}
                  onChange={(e) => handleSliderChange('dissolved_oxygen', e.target.value)}
                />
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>CPCB Standard: ≥6.0 mg/L (Class A), ≥5.0 (Class B)</div>
              </div>

              {/* pH */}
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-name">pH Level:</span>
                  <span className="slider-val">{params.ph}</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="14" 
                  step="0.1" 
                  value={params.ph}
                  onChange={(e) => handleSliderChange('ph', e.target.value)}
                />
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Safe Range: 6.5 – 8.5</div>
              </div>

              {/* BOD */}
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-name">Biochemical Oxygen Demand (BOD):</span>
                  <span className="slider-val">{params.bod} mg/L</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="40" 
                  step="0.1" 
                  value={params.bod}
                  onChange={(e) => handleSliderChange('bod', e.target.value)}
                />
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>CPCB Limit: ≤2.0 (Class A), ≤3.0 (Class B/C)</div>
              </div>

              {/* Total Coliform */}
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-name">Total Coliform Bacteria:</span>
                  <span className="slider-val">{params.total_coliform} MPN/100mL</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="50000" 
                  step="50" 
                  value={params.total_coliform}
                  onChange={(e) => handleSliderChange('total_coliform', e.target.value)}
                />
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>CPCB Limit: ≤50 (Class A), ≤500 (Class B), ≤5000 (Class C)</div>
              </div>

              {/* Electrical Conductivity */}
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-name">Electrical Conductivity:</span>
                  <span className="slider-val">{params.conductivity} µS/cm</span>
                </div>
                <input 
                  type="range" 
                  min="20" 
                  max="3000" 
                  step="10" 
                  value={params.conductivity}
                  onChange={(e) => handleSliderChange('conductivity', e.target.value)}
                />
              </div>

              {/* Nitrates */}
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-name">Nitrate ($NO_3$):</span>
                  <span className="slider-val">{params.nitrate} mg/L</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="25" 
                  step="0.1" 
                  value={params.nitrate}
                  onChange={(e) => handleSliderChange('nitrate', e.target.value)}
                />
              </div>

              {/* Temperature */}
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-name">Water Temperature:</span>
                  <span className="slider-val">{params.temperature} °C</span>
                </div>
                <input 
                  type="range" 
                  min="5" 
                  max="45" 
                  step="0.5" 
                  value={params.temperature}
                  onChange={(e) => handleSliderChange('temperature', e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic WQI Gauge, Classification & Limiting Factors */}
        <div>
          <div className="glass-card" style={{ marginBottom: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '20px' }}>
              2. Real-Time Water Quality Assessment
            </h3>

            {/* Circular Gauge */}
            <div className="gauge-container" style={{ margin: '15px 0' }}>
              <svg width="180" height="180">
                <circle 
                  stroke="rgba(51, 65, 85, 0.4)" 
                  fill="transparent" 
                  strokeWidth="12" 
                  r={radius} 
                  cx="90" 
                  cy="90" 
                />
                <circle 
                  className="gauge-circle"
                  stroke={getGaugeColor(wqi)} 
                  fill="transparent" 
                  strokeWidth="12" 
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  r={radius} 
                  cx="90" 
                  cy="90" 
                  style={{ transition: 'stroke-dashoffset 0.4s ease, stroke 0.4s ease' }}
                />
                <text 
                  x="90" 
                  y="92" 
                  textAnchor="middle" 
                  className="gauge-value-text"
                >
                  {wqi}
                </text>
                <text 
                  x="90" 
                  y="114" 
                  textAnchor="middle" 
                  className="gauge-label-text"
                >
                  WQI Index
                </text>
              </svg>

              <div style={{ marginTop: '12px', textAlign: 'center' }}>
                <span className={`badge ${getClassBadgeStyle(results?.predicted_class)}`} style={{ fontSize: '14px', padding: '6px 14px' }}>
                  {results?.predicted_class || 'Calculating...'}
                </span>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  {results?.risk_level || 'Safe for Use'}
                </div>
              </div>
            </div>

            {/* Limiting Factors Section */}
            {results?.limiting_factors && results.limiting_factors.length > 0 && (
              <div style={{ marginTop: '24px' }}>
                <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px', color: '#fca5a5' }}>
                  <AlertTriangle size={16} /> Limiting Contaminants Flagged:
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {results.limiting_factors.map((lf, i) => (
                    <div key={i} style={{
                      padding: '10px 12px',
                      background: 'rgba(239, 68, 68, 0.08)',
                      border: '1px solid rgba(239, 68, 68, 0.25)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px'
                    }}>
                      <div style={{ fontWeight: '700', color: '#fca5a5' }}>{lf.parameter}</div>
                      <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>{lf.reason}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Ticket Submission Form */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '20px', marginTop: '24px' }}>
              <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileCheck size={18} color="#06b6d4" />
                Submit Water Hazard Incident
              </h4>

              <form onSubmit={submitIncidentReport}>
                <div className="form-group">
                  <label className="form-label">Water Body / Intake Landmark:</label>
                  <input 
                    className="form-input"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Incident Priority Triage Tier:</label>
                  <select 
                    className="form-select"
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                  >
                    <option value="Low">Low Priority</option>
                    <option value="Medium">Medium Priority</option>
                    <option value="High">High Priority</option>
                    <option value="Critical">Critical Emergency</option>
                  </select>
                </div>

                <button 
                  type="submit" 
                  disabled={submitting} 
                  className="btn btn-cyan" 
                  style={{ width: '100%', opacity: submitting ? 0.7 : 1 }}
                >
                  {submitting ? 'Submitting to Triage Queue...' : 'Submit Water Report to Triage Queue'}
                </button>
              </form>

              {ticketSuccess && (
                <div style={{
                  marginTop: '16px',
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(16, 185, 129, 0.2)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#86efac',
                  fontSize: '13px',
                  fontWeight: '600',
                  boxShadow: '0 0 15px rgba(16, 185, 129, 0.2)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: onTrackTicket && lastTicketId ? '10px' : '0' }}>
                    <CheckCircle size={18} /> {ticketSuccess}
                  </div>
                  {onTrackTicket && lastTicketId && (
                    <button
                      type="button"
                      onClick={() => onTrackTicket(lastTicketId)}
                      className="btn btn-secondary"
                      style={{
                        fontSize: '12px',
                        padding: '6px 12px',
                        background: 'rgba(15, 23, 42, 0.8)',
                        color: '#34d399',
                        borderColor: 'rgba(16, 185, 129, 0.4)'
                      }}
                    >
                      🔍 Track This Incident Resolution Status →
                    </button>
                  )}
                </div>
              )}

              {submitError && (
                <div style={{
                  marginTop: '16px',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#fca5a5',
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <AlertTriangle size={18} /> {submitError}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
