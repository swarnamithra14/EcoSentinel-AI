import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  MapPin, 
  Activity, 
  ShieldAlert, 
  TrendingUp, 
  ArrowRight,
  Filter
} from 'lucide-react';

export default function HotspotsView({ onRefreshNeeded }) {
  const [hotspots, setHotspots] = useState([]);
  const [filterTier, setFilterTier] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [actionSuccess, setActionSuccess] = useState('');
  const [actionError, setActionError] = useState('');
  const [updatingId, setUpdatingId] = useState(null);

  const fetchHotspots = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/hotspots');
      const data = await res.json();
      if (res.ok && data.hotspots) {
        setHotspots(data.hotspots);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHotspots();
  }, []);

  const handleStatusUpdate = async (reportId, newStatus) => {
    setUpdatingId(reportId);
    setActionError('');
    setActionSuccess('');

    try {
      const res = await fetch(`/api/reports/${reportId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          note: `Transitioned to ${newStatus} via Priority Triage Engine`
        })
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setActionSuccess(`✓ Ticket #${reportId} status successfully transitioned to '${newStatus}'!`);
        await fetchHotspots();
        if (onRefreshNeeded) onRefreshNeeded();
        setTimeout(() => setActionSuccess(''), 5000);
      } else {
        setActionError(data.message || `Failed to update ticket #${reportId}.`);
      }
    } catch (err) {
      setActionError(`Network error: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  const filtered = hotspots.filter(h => {
    if (filterTier === 'ALL') return true;
    return h.priority_tier?.toUpperCase() === filterTier.toUpperCase();
  });

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
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <AlertTriangle className="text-amber-400" size={30} color="#f59e0b" />
            Priority Hotspot Triage Engine
          </h1>
          <p className="page-subtitle">
            Explainable mathematical risk ranking prioritizing municipal cleanup resources by recurrence, severity, and age.
          </p>
        </div>

        {/* Tier Filter Tabs */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(15, 23, 42, 0.7)', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          {['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'RESOLVED'].map(tier => (
            <button
              key={tier}
              onClick={() => setFilterTier(tier)}
              style={{
                background: filterTier === tier ? 'var(--emerald-600)' : 'transparent',
                color: filterTier === tier ? '#ffffff' : 'var(--text-secondary)',
                border: 'none',
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {actionSuccess && (
        <div style={{
          marginBottom: '20px',
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(16, 185, 129, 0.2)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          color: '#86efac',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '13px',
          fontWeight: '600',
          boxShadow: '0 0 15px rgba(16, 185, 129, 0.2)'
        }}>
          <CheckCircle2 size={18} /> {actionSuccess}
        </div>
      )}

      {actionError && (
        <div style={{
          marginBottom: '20px',
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(239, 68, 68, 0.2)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#fca5a5',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '13px'
        }}>
          <AlertTriangle size={18} /> {actionError}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          Calculating priority scorecards...
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {filtered.map((hotspot, idx) => {
            const breakdown = hotspot.factor_breakdown || {};
            return (
              <div 
                key={hotspot.id} 
                className="glass-card"
                style={{
                  borderLeft: hotspot.priority_tier === 'Critical' ? '4px solid var(--rose-500)' :
                              hotspot.priority_tier === 'High' ? '4px solid var(--amber-500)' :
                              '4px solid var(--emerald-500)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '14px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-muted)' }}>
                        #{hotspot.id}
                      </span>
                      <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: '700' }}>
                        {hotspot.location_name}
                      </h3>
                      <span className={`badge ${getTierBadge(hotspot.priority_tier)}`}>
                        {hotspot.priority_tier}
                      </span>
                      <span style={{
                        fontSize: '11px',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        background: 'rgba(51, 65, 85, 0.5)',
                        color: 'var(--text-secondary)'
                      }}>
                        Status: {hotspot.status}
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: '16px', marginTop: '6px', color: 'var(--text-secondary)', fontSize: '13px' }}>
                      <span>Type: <strong style={{ color: 'var(--text-primary)' }}>{hotspot.report_type?.toUpperCase()}</strong></span>
                      {hotspot.total_waste_objects ? (
                        <span>Litter Count: <strong style={{ color: 'var(--text-primary)' }}>{hotspot.total_waste_objects}</strong></span>
                      ) : null}
                      {hotspot.wqi_score ? (
                        <span>WQI Score: <strong style={{ color: 'var(--text-primary)' }}>{hotspot.wqi_score} ({hotspot.water_class})</strong></span>
                      ) : null}
                      <span>Recurrence Count: <strong style={{ color: 'var(--text-primary)' }}>{hotspot.location_recurrence || 1}</strong></span>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: 'var(--font-heading)', fontSize: '32px', fontWeight: '800', color: 'var(--text-primary)', lineHeight: '1' }}>
                      {hotspot.priority_score?.toFixed(1) || 0}
                      <span style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: '500' }}> / 100 pts</span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Calculated Heuristic Score
                    </div>
                  </div>
                </div>

                {/* Mathematical Factor Score Breakdown Cards */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: '10px',
                  margin: '14px 0',
                  padding: '12px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)'
                }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Severity Weight</div>
                    <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      +{breakdown.severity_points || 0} pts
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Recurrence Weight</div>
                    <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      +{breakdown.recurrence_points || 0} pts
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Age Weight</div>
                    <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      +{breakdown.age_points || 0} pts
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Litter/Hazard Load</div>
                    <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      +{breakdown.object_points || 0} pts
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Status Penalty</div>
                    <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      {breakdown.status_factor === 1 ? '100% (Active)' : `${Math.round(breakdown.status_factor * 100)}%`}
                    </div>
                  </div>
                </div>

                {/* Narrative Explanation */}
                {hotspot.explanation_narrative && (
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', fontStyle: 'italic', marginBottom: '14px' }}>
                    "{hotspot.explanation_narrative}"
                  </p>
                )}

                {/* Interactive Status Transition Actions */}
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>
                    Dispatch & Action:
                  </span>
                  
                  {hotspot.status !== 'Under Review' && (
                    <button 
                      onClick={() => handleStatusUpdate(hotspot.id, 'Under Review')}
                      disabled={updatingId === hotspot.id}
                      className="btn btn-secondary"
                      style={{ fontSize: '12px', padding: '6px 12px', opacity: updatingId === hotspot.id ? 0.6 : 1 }}
                    >
                      {updatingId === hotspot.id ? 'Updating...' : 'Assign to Field Review'}
                    </button>
                  )}

                  {hotspot.status !== 'Cleanup Assigned' && hotspot.status !== 'Resolved' && (
                    <button 
                      onClick={() => handleStatusUpdate(hotspot.id, 'Cleanup Assigned')}
                      disabled={updatingId === hotspot.id}
                      className="btn btn-cyan"
                      style={{ fontSize: '12px', padding: '6px 12px', opacity: updatingId === hotspot.id ? 0.6 : 1 }}
                    >
                      {updatingId === hotspot.id ? 'Updating...' : 'Dispatch Sanitation Crew'}
                    </button>
                  )}

                  {hotspot.status !== 'Resolved' && (
                    <button 
                      onClick={() => handleStatusUpdate(hotspot.id, 'Resolved')}
                      disabled={updatingId === hotspot.id}
                      className="btn btn-primary"
                      style={{ fontSize: '12px', padding: '6px 12px', opacity: updatingId === hotspot.id ? 0.6 : 1 }}
                    >
                      <CheckCircle2 size={14} /> {updatingId === hotspot.id ? 'Updating...' : 'Mark as Remediated'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
