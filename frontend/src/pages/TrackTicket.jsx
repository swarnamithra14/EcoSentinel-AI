import React, { useState, useEffect } from 'react';
import { 
  Search, 
  CheckCircle2, 
  Clock, 
  TrendingUp, 
  ShieldCheck, 
  MapPin, 
  AlertCircle,
  FileText,
  Trash2,
  Droplets
} from 'lucide-react';

export default function TrackTicket({ initialTicketId, setTab }) {
  const [ticketIdInput, setTicketIdInput] = useState(initialTicketId || '');
  const [ticketData, setTicketData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchTicket = async (idToSearch) => {
    const id = idToSearch || ticketIdInput;
    if (!id) {
      setError('Please enter a ticket number.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`/api/reports/${id}`);
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setTicketData(data.report);
      } else {
        setTicketData(null);
        setError(data.message || `No incident ticket found with ID #${id}.`);
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialTicketId) {
      searchTicket(initialTicketId);
    }
  }, [initialTicketId]);

  // Status mapping for progress stepper
  const steps = [
    { key: 'Reported', label: '1. Incident Registered', desc: 'AI verified & logged into database' },
    { key: 'Under Review', label: '2. Under Field Inspection', desc: 'Municipal officer assigned to inspect' },
    { key: 'Cleanup Assigned', label: '3. Sanitation Dispatched', desc: 'Sanitation team deployed for remediation' },
    { key: 'Resolved', label: '4. Remediated & Cleaned', desc: 'Hazard cleared and verified' }
  ];

  const getStepStatus = (stepKey, currentStatus) => {
    const order = ['Reported', 'Under Review', 'Cleanup Assigned', 'Resolved'];
    const currentIndex = order.indexOf(currentStatus);
    const stepIndex = order.indexOf(stepKey);

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Search className="text-emerald-400" size={30} color="#10b981" />
            Track Incident Resolution
          </h1>
          <p className="page-subtitle">
            Citizen transparency portal: Check the real-time status and municipal cleanup progress of your reported incident.
          </p>
        </div>
      </div>

      {/* Ticket Search Bar */}
      <div className="glass-card" style={{ maxWidth: '640px', marginBottom: '28px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '10px' }}>
          Lookup Your Incident Tracking Number:
        </h3>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="number"
            className="form-input"
            placeholder="e.g. 1, 3, 5, 7"
            value={ticketIdInput}
            onChange={(e) => setTicketIdInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchTicket()}
            style={{ fontSize: '15px' }}
          />
          <button 
            onClick={() => searchTicket()} 
            disabled={loading}
            className="btn btn-primary"
            style={{ minWidth: '130px' }}
          >
            {loading ? 'Searching...' : 'Track Ticket'}
          </button>
        </div>

        {error && (
          <div style={{
            marginTop: '14px',
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}
      </div>

      {/* Ticket Details & Stepper */}
      {ticketData && (
        <div className="glass-card" style={{ maxWidth: '820px' }}>
          {/* Header Card */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '18px', marginBottom: '24px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--text-muted)' }}>
                  Ticket #{ticketData.id}
                </span>
                <span style={{
                  padding: '3px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '700',
                  background: ticketData.report_type === 'water' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                  color: ticketData.report_type === 'water' ? 'var(--cyan-400)' : 'var(--emerald-400)'
                }}>
                  {ticketData.report_type?.toUpperCase()}
                </span>
                {ticketData.human_verified ? (
                  <span style={{ fontSize: '11px', color: 'var(--emerald-400)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheck size={14} /> Authority Verified
                  </span>
                ) : null}
              </div>

              <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '22px', fontWeight: '700', marginTop: '6px' }}>
                {ticketData.location_name}
              </h2>
              <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>
                Reported on: {new Date(ticketData.timestamp).toLocaleString()}
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span className={`badge ${
                ticketData.status === 'Resolved' ? 'badge-low' :
                ticketData.status === 'Cleanup Assigned' ? 'badge-moderate' :
                'badge-high'
              }`} style={{ fontSize: '13px', padding: '6px 14px' }}>
                {ticketData.status}
              </span>
            </div>
          </div>

          {/* 4-Step Visual Progress Stepper */}
          <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>
            Remediation Progress:
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px', marginBottom: '28px' }}>
            {steps.map((s) => {
              const st = getStepStatus(s.key, ticketData.status);
              const isCompleted = st === 'completed';
              const isActive = st === 'active';

              return (
                <div 
                  key={s.key}
                  style={{
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    background: isActive ? 'rgba(16, 185, 129, 0.15)' : isCompleted ? 'rgba(30, 41, 59, 0.6)' : 'rgba(15, 23, 42, 0.4)',
                    border: isActive ? '1px solid var(--emerald-400)' : isCompleted ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid var(--border-subtle)',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    {isCompleted ? (
                      <CheckCircle2 size={16} color="#10b981" />
                    ) : isActive ? (
                      <div className="status-dot" style={{ width: '10px', height: '10px' }} />
                    ) : (
                      <Clock size={16} color="#64748b" />
                    )}
                    <span style={{
                      fontSize: '13px',
                      fontWeight: '700',
                      color: isActive ? 'var(--emerald-400)' : isCompleted ? 'var(--text-primary)' : 'var(--text-muted)'
                    }}>
                      {s.label}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                    {s.desc}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Observation Summary */}
          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginBottom: '20px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '8px', color: 'var(--text-secondary)' }}>
              Observation Summary:
            </h4>
            <div style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-primary)' }}>
              {ticketData.total_waste_objects ? (
                <div>• Litter Identified: <strong>{ticketData.total_waste_objects} objects</strong> ({JSON.stringify(ticketData.waste_counts)})</div>
              ) : null}
              {ticketData.wqi_score ? (
                <div>• Water Quality: <strong>WQI {ticketData.wqi_score}</strong> ({ticketData.predicted_water_class})</div>
              ) : null}
              <div>• Severity Level: <strong>{ticketData.severity_level}</strong></div>
              <div>• Field Notes: <em>{ticketData.reviewer_notes || 'Submitted by citizen.'}</em></div>
            </div>
          </div>

          {/* Status History Timeline */}
          {ticketData.status_history && ticketData.status_history.length > 0 && (
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '10px', color: 'var(--text-secondary)' }}>
                Official Action History:
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {ticketData.status_history.map((h, i) => (
                  <div key={i} style={{
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(30, 41, 59, 0.4)',
                    fontSize: '12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <strong style={{ color: 'var(--emerald-400)' }}>{h.new_status}</strong>: {h.notes}
                    </div>
                    <div style={{ color: 'var(--text-muted)' }}>
                      {h.timestamp ? new Date(h.timestamp).toLocaleString() : ''}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
