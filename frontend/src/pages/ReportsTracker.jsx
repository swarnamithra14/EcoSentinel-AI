import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Trash2, 
  CheckCircle, 
  Clock, 
  ShieldCheck, 
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  MapPin
} from 'lucide-react';

export default function ReportsTracker({ onRefreshNeeded }) {
  const [reports, setReports] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/reports');
      const data = await res.json();
      if (res.ok && data.reports) {
        setReports(data.reports);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleToggleVerification = async (reportId, currentStatus) => {
    try {
      const res = await fetch(`/api/reports/${reportId}/verify`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_verified: !currentStatus,
          verified_by: 'Inspector SMB',
          notes: 'Verified via high-resolution telemetry inspection'
        })
      });
      if (res.ok) {
        fetchReports();
        if (onRefreshNeeded) onRefreshNeeded();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteReport = async (reportId) => {
    if (!window.confirm(`Delete Incident Ticket #${reportId}?`)) return;
    try {
      const res = await fetch(`/api/reports/${reportId}`, { method: 'DELETE' });
      if (res.ok) {
        fetchReports();
        if (onRefreshNeeded) onRefreshNeeded();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = reports.filter(r => {
    const matchesSearch = r.location_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || r.status?.toUpperCase() === statusFilter.toUpperCase();
    return matchesSearch && matchesStatus;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <FileText className="text-emerald-400" size={30} color="#10b981" />
            Incident Tracking & SQLite Audit Trail
          </h1>
          <p className="page-subtitle">
            Persistent database records maintaining complete status lifecycle transitions and field verification stamps.
          </p>
        </div>

        {/* Search Bar */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ position: 'relative', minWidth: '260px' }}>
            <input 
              type="text"
              placeholder="Search location..."
              className="form-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '34px' }}
            />
            <Search size={16} color="#64748b" style={{ position: 'absolute', left: '10px', top: '12px' }} />
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {['ALL', 'REPORTED', 'UNDER REVIEW', 'CLEANUP ASSIGNED', 'RESOLVED'].map(st => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            style={{
              background: statusFilter === st ? 'rgba(16, 185, 129, 0.2)' : 'rgba(15, 23, 42, 0.5)',
              color: statusFilter === st ? 'var(--emerald-400)' : 'var(--text-secondary)',
              border: statusFilter === st ? '1px solid var(--emerald-400)' : '1px solid var(--border-subtle)',
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Location Landmark</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Verification</th>
              <th>Priority Pts</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(r => {
              const isExpanded = expandedId === r.id;
              return (
                <React.Fragment key={r.id}>
                  <tr>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: '600' }}>#{r.id}</td>
                    <td>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: '700',
                        background: r.report_type === 'water' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                        color: r.report_type === 'water' ? 'var(--cyan-400)' : 'var(--emerald-400)'
                      }}>
                        {r.report_type?.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontWeight: '600' }}>{r.location_name}</td>
                    <td>
                      <span className={`badge ${
                        r.severity_level === 'Critical' ? 'badge-critical' :
                        r.severity_level === 'High' ? 'badge-high' :
                        r.severity_level === 'Medium' ? 'badge-moderate' : 'badge-low'
                      }`}>
                        {r.severity_level}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: '500' }}>
                        {r.status}
                      </span>
                    </td>
                    <td>
                      <button 
                        onClick={() => handleToggleVerification(r.id, r.human_verified)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          color: r.human_verified ? 'var(--emerald-400)' : 'var(--text-muted)',
                          fontSize: '12px'
                        }}
                      >
                        {r.human_verified ? <ShieldCheck size={16} /> : <ShieldAlert size={16} />}
                        {r.human_verified ? 'Verified' : 'Unverified'}
                      </button>
                    </td>
                    <td style={{ fontFamily: 'var(--font-heading)', fontWeight: '700' }}>
                      {r.priority_score?.toFixed(1) || 0}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        onClick={() => setExpandedId(isExpanded ? null : r.id)}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '11px', marginRight: '6px' }}
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />} Details
                      </button>
                      <button 
                        onClick={() => handleDeleteReport(r.id)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#ef4444',
                          cursor: 'pointer',
                          padding: '4px'
                        }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>

                  {/* Expanded Audit Details */}
                  {isExpanded && (
                    <tr>
                      <td colSpan={8} style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '20px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                          <div>
                            <h4 style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                              Observation Metrics:
                            </h4>
                            <div style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6' }}>
                              {r.total_waste_objects ? (
                                <div>• Total Waste Items: <strong>{r.total_waste_objects}</strong></div>
                              ) : null}
                              {r.waste_counts && Object.keys(r.waste_counts).length > 0 ? (
                                <div>• Item Breakdown: {JSON.stringify(r.waste_counts)}</div>
                              ) : null}
                              {r.wqi_score ? (
                                <div>• WQI Score: <strong>{r.wqi_score}</strong> ({r.water_class})</div>
                              ) : null}
                              <div>• Reviewer Field Notes: <em>{r.reviewer_notes || 'None'}</em></div>
                              <div>• Reported At: {r.timestamp}</div>
                            </div>
                          </div>

                          <div>
                            <h4 style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                              Lifecycle Status Audit Log:
                            </h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                              {r.status_history && r.status_history.map((h, i) => (
                                <div key={i} style={{
                                  fontSize: '12px',
                                  padding: '6px 10px',
                                  background: 'rgba(30, 41, 59, 0.5)',
                                  borderRadius: 'var(--radius-sm)',
                                  display: 'flex',
                                  justifyContent: 'space-between'
                                }}>
                                  <span>
                                    <strong>{h.new_status}</strong>: {h.note}
                                  </span>
                                  <span style={{ color: 'var(--text-muted)' }}>
                                    {h.timestamp ? new Date(h.timestamp).toLocaleTimeString() : ''}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
