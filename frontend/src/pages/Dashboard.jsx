import React from 'react';
import { 
  Activity, 
  Trash2, 
  Droplets, 
  AlertTriangle, 
  ArrowRight, 
  CheckCircle2, 
  Clock, 
  ShieldAlert,
  MapPin,
  TrendingUp
} from 'lucide-react';

export default function Dashboard({ stats, setTab, onSelectReport }) {
  const statusCounts = stats?.status_breakdown || {
    "Reported": 0,
    "Under Review": 0,
    "Cleanup Assigned": 0,
    "Resolved": 0
  };

  const getTierBadge = (tier) => {
    switch (tier) {
      case 'Critical': return 'badge-critical';
      case 'High': return 'badge-high';
      case 'Moderate': return 'badge-moderate';
      case 'Resolved': return 'badge-low';
      default: return 'badge-low';
    }
  };

  return (
    <div>
      {/* Header Banner */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Activity className="text-emerald-400" size={32} color="#10b981" />
            Environmental Intelligence Dashboard
          </h1>
          <p className="page-subtitle">
            Autonomous dual-domain monitoring grid fusing YOLO11n computer vision and CPCB surface water quality analytics.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => setTab('waste')} className="btn btn-primary">
            <Trash2 size={16} /> Scan Waste Image
          </button>
          <button onClick={() => setTab('water')} className="btn btn-cyan">
            <Droplets size={16} /> Test Water Sample
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon emerald">
            <Activity size={24} />
          </div>
          <div>
            <div className="stat-value">{stats?.total_reports || 0}</div>
            <div className="stat-label">Total Logged Reports</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon rose">
            <AlertTriangle size={24} />
          </div>
          <div>
            <div className="stat-value">{stats?.critical_hotspots || 0}</div>
            <div className="stat-label">Critical Hotspots</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon cyan">
            <Droplets size={24} />
          </div>
          <div>
            <div className="stat-value">{stats?.average_wqi || 68.4}</div>
            <div className="stat-label">Average WQI Score</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon amber">
            <Trash2 size={24} />
          </div>
          <div>
            <div className="stat-value">{stats?.total_waste_detected || 0}</div>
            <div className="stat-label">Litter Objects Identified</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Hotspot Leaderboard + Status Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '24px', marginBottom: '30px' }}>
        {/* Hotspots Leaderboard */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <div>
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: '700' }}>
                Priority Triage Leaderboard
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                Highest risk incidents ranked by recurrence, age, and pollution load
              </p>
            </div>
            <button 
              onClick={() => setTab('hotspots')} 
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '6px 12px' }}
            >
              View All <ArrowRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {stats?.recent_reports && stats.recent_reports.length > 0 ? (
              stats.recent_reports.slice(0, 4).map((report, idx) => (
                <div 
                  key={report.id || idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '14px 16px',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid var(--border-subtle)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '14px',
                      fontWeight: '700',
                      color: idx === 0 ? 'var(--rose-500)' : 'var(--text-secondary)',
                      width: '24px'
                    }}>
                      #{idx + 1}
                    </div>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>
                        {report.location_name}
                      </div>
                      <div style={{ display: 'flex', gap: '12px', color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
                        <span>Type: {report.report_type?.toUpperCase()}</span>
                        {report.total_waste_objects ? (
                          <span>Objects: {report.total_waste_objects}</span>
                        ) : null}
                        {report.wqi_score ? (
                          <span>WQI: {report.wqi_score}</span>
                        ) : null}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span className={`badge ${getTierBadge(report.priority_tier)}`}>
                      {report.priority_tier || 'Moderate'} ({report.priority_score || 0} pts)
                    </span>
                    <button 
                      onClick={() => setTab('hotspots')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer'
                      }}
                    >
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                No incident reports currently queued.
              </div>
            )}
          </div>
        </div>

        {/* Resolution Lifecycle Breakdown */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: '700', marginBottom: '6px' }}>
              Incident Lifecycle Triage
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
              Current municipal cleanup pipeline status
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {[
                { label: 'Newly Reported', key: 'Reported', color: '#f59e0b', icon: Clock },
                { label: 'Under Field Review', key: 'Under Review', color: '#3b82f6', icon: Activity },
                { label: 'Cleanup Assigned', key: 'Cleanup Assigned', color: '#06b6d4', icon: TrendingUp },
                { label: 'Remediated & Resolved', key: 'Resolved', color: '#10b981', icon: CheckCircle2 },
              ].map((item) => {
                const count = statusCounts[item.key] || 0;
                const total = stats?.total_reports || 1;
                const pct = Math.round((count / total) * 100);
                const Icon = item.icon;
                return (
                  <div key={item.key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                        <Icon size={14} color={item.color} />
                        {item.label}
                      </span>
                      <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div style={{
                      height: '6px',
                      background: 'rgba(51, 65, 85, 0.4)',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${pct}%`,
                        height: '100%',
                        background: item.color,
                        borderRadius: '4px',
                        transition: 'width 0.4s ease'
                      }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{
            marginTop: '20px',
            padding: '14px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <ShieldAlert size={20} color="#10b981" />
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              All tickets maintain an immutable timestamped audit trail in SQLite.
            </div>
          </div>
        </div>
      </div>

      {/* Visual Workflow Callout */}
      <div className="glass-card" style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.05) 100%)',
        borderColor: 'rgba(16, 185, 129, 0.2)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '16px', fontWeight: '700', color: '#ffffff' }}>
              Want to see how EcoSentinel AI connects end-to-end?
            </h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '2px' }}>
              Explore the interactive system workflow diagram, CPCB legal standards, and mathematical scoring models.
            </p>
          </div>
          <button onClick={() => setTab('workflow')} className="btn btn-secondary">
            Explore Workflow Guide <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
