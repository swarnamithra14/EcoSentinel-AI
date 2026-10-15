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

  const matchesTier = (h, tab) => {
    if (tab === 'ALL') return true;

    const tier = (h.priority_tier || '').toUpperCase();
    const sev = (h.severity_level || '').toUpperCase();
    const status = (h.status || '').toUpperCase();

    if (tab === 'RESOLVED') {
      return status === 'RESOLVED' || tier.includes('RESOLVED');
    }

    if (tab === 'CRITICAL') {
      return (tier.includes('CRITICAL') || sev === 'CRITICAL') && status !== 'RESOLVED';
    }

    if (tab === 'HIGH') {
      return (tier.includes('HIGH') || sev === 'HIGH') && !tier.includes('CRITICAL') && sev !== 'CRITICAL' && status !== 'RESOLVED';
    }

    if (tab === 'MODERATE') {
      return (tier.includes('MODERATE') || tier.includes('MEDIUM') || sev === 'MEDIUM' || sev === 'MODERATE') && status !== 'RESOLVED';
    }

    if (tab === 'LOW') {
      return (tier.includes('LOW') || sev === 'LOW') && status !== 'RESOLVED';
    }

    return tier.includes(tab);
  };

  const filtered = hotspots.filter(h => matchesTier(h, filterTier));

  const counts = {
    ALL: hotspots.length,
    CRITICAL: hotspots.filter(h => matchesTier(h, 'CRITICAL')).length,
    HIGH: hotspots.filter(h => matchesTier(h, 'HIGH')).length,
    MODERATE: hotspots.filter(h => matchesTier(h, 'MODERATE')).length,
    LOW: hotspots.filter(h => matchesTier(h, 'LOW')).length,
    RESOLVED: hotspots.filter(h => matchesTier(h, 'RESOLVED')).length
  };

  const getTierBadge = (tier, severity) => {
    const t = (tier || '').toLowerCase();
    const s = (severity || '').toLowerCase();
    if (t.includes('critical') || s === 'critical') return 'badge-critical';
    if (t.includes('high') || s === 'high') return 'badge-high';
    if (t.includes('moderate') || t.includes('medium') || s === 'medium') return 'badge-moderate';
    if (t.includes('resolved')) return 'badge-low';
    return 'badge-low';
  };

  const getCardBorder = (hotspot) => {
    const t = (hotspot.priority_tier || '').toLowerCase();
    const s = (hotspot.severity_level || '').toLowerCase();
    const status = (hotspot.status || '').toLowerCase();

    if (status === 'resolved') return '4px solid #10b981';
    if (t.includes('critical') || s === 'critical') return '4px solid #ef4444';
    if (t.includes('high') || s === 'high') return '4px solid #f59e0b';
    if (t.includes('moderate') || s === 'medium') return '4px solid #38bdf8';
    return '4px solid #10b981';
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
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(15, 23, 42, 0.7)', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', flexWrap: 'wrap' }}>
          {['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW', 'RESOLVED'].map(tier => {
            const count = counts[tier] ?? 0;
            const isActive = filterTier === tier;
            return (
              <button
                key={tier}
                onClick={() => setFilterTier(tier)}
                style={{
                  background: isActive ? 'var(--emerald-600)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <span>{tier}</span>
                <span style={{
                  fontSize: '10px',
                  padding: '1px 6px',
                  borderRadius: '10px',
                  background: isActive ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.08)',
                  color: isActive ? '#ffffff' : 'var(--text-muted)',
                  fontWeight: '700'
                }}>
                  {count}
                </span>
              </button>
            );
          })}
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
      ) : filtered.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '50px 20px' }}>
          <CheckCircle2 size={36} color="var(--emerald-400)" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: '700' }}>No {filterTier.toLowerCase()} priority hotspots</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px' }}>
            No incident reports currently match the "{filterTier}" filter criteria.
          </p>
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
                  borderLeft: getCardBorder(hotspot)
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
                      <span className={`badge ${getTierBadge(hotspot.priority_tier, hotspot.severity_level)}`}>
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
