import React, { useState, useEffect } from 'react';
import { 
  Truck, 
  MapPin, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ShieldCheck, 
  Camera, 
  Upload, 
  ExternalLink, 
  RefreshCw,
  FileCheck,
  CheckSquare,
  Square,
  Navigation,
  Compass,
  Layers,
  Sparkles
} from 'lucide-react';

export default function SanitationWorkerPortal({ user, onRefreshStats }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'critical', 'assigned', 'resolved'
  const [activeResolvingId, setActiveResolvingId] = useState(null);
  const [resolutionNote, setResolutionNote] = useState('');
  const [resolvingImagePreview, setResolvingImagePreview] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Field safety checklist state
  const [checklist, setChecklist] = useState({
    vest: true,
    gloves: true,
    mask: true,
    sharpsBox: true,
    binCapacity: false
  });

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/reports');
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (err) {
      console.error("Failed to load worker tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 4000);
  };

  const handleUpdateStatus = async (reportId, newStatus, defaultNote = '') => {
    setActionLoading(true);
    try {
      const payload = {
        status: newStatus,
        notes: defaultNote || `Action by Field Crew (${user?.name || 'Sanitation Team'})`
      };

      if (newStatus === 'Resolved' && resolvingImagePreview) {
        payload.resolved_image_path = resolvingImagePreview;
        payload.notes = resolutionNote || "Site cleaned and restored by Rapid Sanitation Unit.";
      }

      const res = await fetch(`/api/reports/${reportId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        showToast(`Work Order #${reportId} updated to: ${newStatus}`);
        setActiveResolvingId(null);
        setResolutionNote('');
        setResolvingImagePreview(null);
        await fetchTasks();
        if (onRefreshStats) onRefreshStats();
      } else {
        alert("Failed to update status on server.");
      }
    } catch (err) {
      console.error("Status update error:", err);
      alert("Network error updating status.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (uploadEvent) => {
        setResolvingImagePreview(uploadEvent.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Filter tasks
  const filteredTasks = tasks.filter(t => {
    if (filter === 'critical') {
      return (t.severity_level === 'Critical' || t.severity_level === 'High') && t.status !== 'Resolved';
    }
    if (filter === 'assigned') {
      return t.status === 'Cleanup Assigned' || t.status === 'Under Review';
    }
    if (filter === 'resolved') {
      return t.status === 'Resolved';
    }
    return true; // 'all'
  });

  const activeCount = tasks.filter(t => t.status !== 'Resolved').length;
  const criticalCount = tasks.filter(t => (t.severity_level === 'Critical' || t.severity_level === 'High') && t.status !== 'Resolved').length;
  const completedTodayCount = tasks.filter(t => t.status === 'Resolved').length;

  return (
    <div className="worker-portal-container">
      
      {/* Toast Alert */}
      {toastMessage && (
        <div className="worker-toast">
          <CheckCircle2 size={18} color="#10b981" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="worker-hero-banner">
        <div className="worker-hero-content">
          <div className="worker-badge-pill">
            <Truck size={16} />
            <span>FIELD SANITATION DISPATCH PORTAL</span>
          </div>
          <h1>Welcome, {user?.name || 'Sanitation Specialist'}</h1>
          <p>
            Assigned Unit: <strong>{user?.department || 'Zone 4 Rapid Cleanup Unit #12'}</strong> • Badge: <code>{user?.badge_id || 'SN-CREW-12'}</code>
          </p>
          <div className="worker-telemetry-strip">
            <span>📍 Vehicle ID: <strong>TN-01-SN-8842 (Compactor)</strong></span>
            <span>📡 GPS Status: <strong style={{ color: '#10b981' }}>Locked & Calibrated</strong></span>
            <span>🕒 Shift: <strong>Morning Rapid Response (06:00 - 15:00)</strong></span>
          </div>
        </div>

        <button 
          onClick={fetchTasks} 
          disabled={loading}
          className="btn btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px', alignSelf: 'flex-start' }}
        >
          <RefreshCw size={16} className={loading ? 'spin-anim' : ''} />
          <span>Sync Work Orders</span>
        </button>
      </div>

      {/* Metric Cards Row */}
      <div className="worker-metrics-grid">
        <div className="worker-kpi-card">
          <div className="kpi-icon active">
            <Clock size={22} />
          </div>
          <div className="kpi-data">
            <span className="kpi-label">Active Work Orders</span>
            <span className="kpi-val">{activeCount}</span>
          </div>
        </div>

        <div className="worker-kpi-card">
          <div className="kpi-icon critical">
            <AlertTriangle size={22} />
          </div>
          <div className="kpi-data">
            <span className="kpi-label">Critical / High Urgency</span>
            <span className="kpi-val" style={{ color: '#f87171' }}>{criticalCount}</span>
          </div>
        </div>

        <div className="worker-kpi-card">
          <div className="kpi-icon success">
            <CheckCircle2 size={22} />
          </div>
          <div className="kpi-data">
            <span className="kpi-label">Remediated & Verified</span>
            <span className="kpi-val" style={{ color: '#34d399' }}>{completedTodayCount}</span>
          </div>
        </div>

        <div className="worker-kpi-card">
          <div className="kpi-icon truck">
            <Truck size={22} />
          </div>
          <div className="kpi-data">
            <span className="kpi-label">Truck Bin Payload</span>
            <span className="kpi-val" style={{ color: '#fbbf24' }}>68% Full</span>
          </div>
        </div>
      </div>

      {/* Middle Row: Field Safety Checklist & Routing Notice */}
      <div className="worker-aux-grid">
        <div className="surface-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <ShieldCheck size={20} color="var(--emerald-400)" />
            <h3 style={{ fontSize: '15px', fontWeight: '700' }}>Pre-Departure Field Safety Checklist</h3>
          </div>
          
          <div className="checklist-items-grid">
            <div 
              className="checklist-item" 
              onClick={() => setChecklist(prev => ({ ...prev, vest: !prev.vest }))}
            >
              {checklist.vest ? <CheckSquare size={16} color="var(--emerald-400)" /> : <Square size={16} />}
              <span>High-Visibility Safety Vest Equipped</span>
            </div>

            <div 
              className="checklist-item" 
              onClick={() => setChecklist(prev => ({ ...prev, gloves: !prev.gloves }))}
            >
              {checklist.gloves ? <CheckSquare size={16} color="var(--emerald-400)" /> : <Square size={16} />}
              <span>Heavy-Duty Puncture-Resistant Gloves</span>
            </div>

            <div 
              className="checklist-item" 
              onClick={() => setChecklist(prev => ({ ...prev, mask: !prev.mask }))}
            >
              {checklist.mask ? <CheckSquare size={16} color="var(--emerald-400)" /> : <Square size={16} />}
              <span>Respirator / Biohazard Particulate Mask</span>
            </div>

            <div 
              className="checklist-item" 
              onClick={() => setChecklist(prev => ({ ...prev, sharpsBox: !prev.sharpsBox }))}
            >
              {checklist.sharpsBox ? <CheckSquare size={16} color="var(--emerald-400)" /> : <Square size={16} />}
              <span>Sharps & Medical Waste Rigid Safe Box</span>
            </div>
          </div>
        </div>

        <div className="surface-card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.04)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <Navigation size={20} color="#fbbf24" />
            <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#fbbf24' }}>Field Dispatch Standard Operating Procedure</h3>
          </div>
          <ol style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '18px', lineHeight: '1.7' }}>
            <li>Review critical hotspot coordinates before starting vehicle ignition.</li>
            <li>Press <strong>"Accept Work Order"</strong> to notify the command center you are en route.</li>
            <li>Upon arrival, verify the AI-detected waste objects match field reality.</li>
            <li>After cleaning, snap a clear photo and click <strong>"Submit Resolution Proof"</strong> to close the ticket.</li>
          </ol>
        </div>
      </div>

      {/* Filter Tabs Bar */}
      <div className="worker-filter-bar">
        <div className="filter-buttons-group">
          <button 
            className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All Orders ({tasks.length})
          </button>
          <button 
            className={`filter-tab ${filter === 'critical' ? 'active' : ''}`}
            onClick={() => setFilter('critical')}
          >
            ⚠️ High & Critical ({criticalCount})
          </button>
          <button 
            className={`filter-tab ${filter === 'assigned' ? 'active' : ''}`}
            onClick={() => setFilter('assigned')}
          >
            🚛 En Route / In Progress
          </button>
          <button 
            className={`filter-tab ${filter === 'resolved' ? 'active' : ''}`}
            onClick={() => setFilter('resolved')}
          >
            ✅ Completed & Cleared ({completedTodayCount})
          </button>
        </div>

        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Showing <strong>{filteredTasks.length}</strong> work orders
        </span>
      </div>

      {/* Tasks Queue Cards */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <RefreshCw size={32} className="spin-anim" style={{ margin: '0 auto 16px' }} />
          <div>Synchronizing assigned sanitation work orders...</div>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="surface-card" style={{ textAlign: 'center', padding: '50px 20px' }}>
          <CheckCircle2 size={40} color="var(--emerald-400)" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: '700' }}>No pending tasks in this category!</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px' }}>
            All designated cleanup routes have been completed or no matching incident reports exist.
          </p>
        </div>
      ) : (
        <div className="worker-task-list">
          {filteredTasks.map((task) => {
            const isResolved = task.status === 'Resolved';
            const isCritical = task.severity_level === 'Critical';
            const isHigh = task.severity_level === 'High';
            const isResolvingThis = activeResolvingId === task.id;

            return (
              <div 
                key={task.id} 
                className="worker-task-card"
                style={{
                  borderLeftColor: isResolved ? '#10b981' : isCritical ? '#ef4444' : isHigh ? '#f59e0b' : '#38bdf8'
                }}
              >
                {/* Task Header */}
                <div className="task-card-header">
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span className="task-ticket-badge">#{task.id}</span>
                      <span className={`task-severity-badge ${task.severity_level?.toLowerCase() || 'medium'}`}>
                        {task.severity_level || 'Medium'} Severity
                      </span>
                      <span className={`task-status-pill ${task.status?.toLowerCase().replace(/\s+/g, '-')}`}>
                        {task.status}
                      </span>
                      {task.report_type && (
                        <span className="task-type-badge">
                          {task.report_type.toUpperCase()} HAZARD
                        </span>
                      )}
                    </div>

                    <h2 className="task-location-title">{task.location_name}</h2>
                    
                    <div className="task-geo-row">
                      <MapPin size={14} color="var(--emerald-400)" />
                      <span>GPS: {task.latitude?.toFixed(4)}, {task.longitude?.toFixed(4)}</span>
                      <a 
                        href={`https://maps.google.com/?q=${task.latitude},${task.longitude}`} 
                        target="_blank" 
                        rel="noreferrer"
                        className="geo-maps-link"
                      >
                        Navigate on Map <ExternalLink size={12} />
                      </a>
                    </div>
                  </div>

                  {/* Quick Action Button for Status */}
                  <div className="task-actions-stack">
                    {!isResolved && task.status === 'Reported' && (
                      <button
                        onClick={() => handleUpdateStatus(task.id, 'Cleanup Assigned', `Assigned to ${user?.name || 'Sanitation Unit #12'}`)}
                        disabled={actionLoading}
                        className="btn btn-primary"
                        style={{ background: 'linear-gradient(135deg, #0ea5e9, #0284c7)', fontSize: '13px' }}
                      >
                        <Truck size={14} /> Accept Work Order
                      </button>
                    )}

                    {!isResolved && task.status === 'Cleanup Assigned' && (
                      <button
                        onClick={() => handleUpdateStatus(task.id, 'Under Review', `Crew arrived on site, cleanup started`)}
                        disabled={actionLoading}
                        className="btn btn-secondary"
                        style={{ borderColor: '#f59e0b', color: '#fbbf24', fontSize: '13px' }}
                      >
                        <Navigation size={14} /> Arrived On-Site (In Progress)
                      </button>
                    )}

                    {!isResolved && (
                      <button
                        onClick={() => setActiveResolvingId(isResolvingThis ? null : task.id)}
                        className="btn btn-primary"
                        style={{ background: 'linear-gradient(135deg, var(--emerald-500), var(--emerald-600))', fontSize: '13px' }}
                      >
                        <FileCheck size={14} /> {isResolvingThis ? 'Cancel Resolution' : 'Complete & Upload Proof'}
                      </button>
                    )}

                    {isResolved && (
                      <div className="resolved-checkmark-banner">
                        <CheckCircle2 size={16} /> Remediated
                      </div>
                    )}
                  </div>
                </div>

                {/* Waste Objects and Measurements Row */}
                <div className="task-details-row">
                  {task.waste_counts && typeof task.waste_counts === 'object' && Object.keys(task.waste_counts).length > 0 && (
                    <div className="task-tags-group">
                      <span className="task-tag-label">Litter Breakdown:</span>
                      {Object.entries(task.waste_counts).map(([cls, cnt]) => (
                        <span key={cls} className="waste-count-tag">
                          {cls}: <strong>{cnt}</strong>
                        </span>
                      ))}
                      <span className="waste-count-tag total">
                        Total Items: <strong>{task.total_waste_objects || 0}</strong>
                      </span>
                    </div>
                  )}

                  {task.water_measurements && (
                    <div className="task-tags-group" style={{ marginTop: '8px' }}>
                      <span className="task-tag-label">Water Telemetry:</span>
                      <span className="water-tag">Class: <strong>{task.predicted_water_class || 'Class C'}</strong></span>
                      {task.wqi_score && <span className="water-tag">WQI: <strong>{task.wqi_score}</strong></span>}
                    </div>
                  )}

                  {task.reviewer_notes && (
                    <div className="task-notes-callout">
                      <strong>Inspector Note:</strong> {task.reviewer_notes}
                    </div>
                  )}
                </div>

                {/* Resolution Proof Drawer if Clicked */}
                {isResolvingThis && (
                  <div className="resolution-proof-drawer">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                      <Camera size={18} color="var(--emerald-400)" />
                      <h4 style={{ fontSize: '14px', fontWeight: '700' }}>
                        File Remediation Verification Proof for #{task.id}
                      </h4>
                    </div>

                    <div className="drawer-grid">
                      <div>
                        <label className="form-label">Remediation & Disposal Notes</label>
                        <textarea
                          rows={3}
                          className="login-input"
                          value={resolutionNote}
                          onChange={(e) => setResolutionNote(e.target.value)}
                          placeholder="e.g. Cleared 15 plastic bottles, culvert unblocked, waste loaded into Truck #12 and transferred to material recovery facility."
                        />
                      </div>

                      <div>
                        <label className="form-label">Upload Cleaned Site Photo (Evidence)</label>
                        <div className="photo-evidence-dropzone">
                          {resolvingImagePreview ? (
                            <div style={{ position: 'relative', width: '100%', height: '110px' }}>
                              <img 
                                src={resolvingImagePreview} 
                                alt="Cleanup proof" 
                                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' }} 
                              />
                              <button 
                                onClick={() => setResolvingImagePreview(null)}
                                className="remove-preview-btn"
                              >
                                ×
                              </button>
                            </div>
                          ) : (
                            <label className="evidence-upload-label">
                              <Upload size={20} color="var(--emerald-400)" />
                              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                Click to upload post-cleanup photo
                              </span>
                              <input 
                                type="file" 
                                accept="image/*" 
                                onChange={handleImageUpload} 
                                style={{ display: 'none' }} 
                              />
                            </label>
                          )}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '14px' }}>
                      <button
                        onClick={() => setActiveResolvingId(null)}
                        className="btn btn-secondary"
                        style={{ fontSize: '12px' }}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleUpdateStatus(task.id, 'Resolved')}
                        disabled={actionLoading}
                        className="btn btn-primary"
                        style={{ background: 'linear-gradient(135deg, var(--emerald-500), var(--emerald-600))', fontSize: '12px' }}
                      >
                        {actionLoading ? 'Saving Proof...' : 'Submit Resolution Proof & Mark Resolved'}
                      </button>
                    </div>
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
