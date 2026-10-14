import React from 'react';
import { 
  Activity, 
  Trash2, 
  Droplets, 
  AlertTriangle, 
  FileText, 
  BarChart3, 
  HelpCircle,
  ShieldCheck,
  Search,
  User,
  Shield
} from 'lucide-react';

export default function Sidebar({ currentTab, setTab, stats, role, setRole }) {
  // Navigation for Citizen vs Admin
  const citizenItems = [
    { id: 'waste', label: 'Report Waste Litter', icon: Trash2 },
    { id: 'water', label: 'Check Water Safety', icon: Droplets },
    { id: 'track', label: 'Track My Incident', icon: Search },
    { id: 'workflow', label: 'How It Works', icon: HelpCircle },
  ];

  const adminItems = [
    { id: 'dashboard', label: 'Command Overview', icon: Activity },
    { id: 'hotspots', label: 'Priority Hotspots', icon: AlertTriangle, badge: stats?.critical_hotspots },
    { id: 'reports', label: 'Incident Records', icon: FileText, badge: stats?.total_reports },
    { id: 'waste', label: 'Waste Vision Studio', icon: Trash2 },
    { id: 'water', label: 'Water Analysis Lab', icon: Droplets },
    { id: 'analytics', label: 'Model Evaluation', icon: BarChart3 },
    { id: 'workflow', label: 'System Architecture', icon: HelpCircle },
  ];

  const activeNavItems = role === 'citizen' ? citizenItems : adminItems;

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="brand-header">
        <div className="brand-icon-wrapper">
          <ShieldCheck size={24} />
        </div>
        <div className="brand-text">
          <h1>EcoSentinel AI</h1>
          <span>Dual Intelligence Grid</span>
        </div>
      </div>

      {/* Role Switcher Pill */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.8)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '4px',
        display: 'flex',
        gap: '4px',
        marginBottom: '20px'
      }}>
        <button
          onClick={() => {
            setRole('citizen');
            if (['dashboard', 'hotspots', 'reports', 'analytics'].includes(currentTab)) {
              setTab('waste');
            }
          }}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '8px 10px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background: role === 'citizen' ? 'linear-gradient(135deg, var(--emerald-500), var(--emerald-600))' : 'transparent',
            color: role === 'citizen' ? '#ffffff' : 'var(--text-secondary)'
          }}
        >
          <User size={14} /> Citizen
        </button>

        <button
          onClick={() => {
            setRole('admin');
            if (currentTab === 'track') {
              setTab('dashboard');
            }
          }}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '8px 10px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background: role === 'admin' ? 'linear-gradient(135deg, #0ea5e9, #0284c7)' : 'transparent',
            color: role === 'admin' ? '#ffffff' : 'var(--text-secondary)'
          }}
        >
          <Shield size={14} /> Authority
        </button>
      </div>

      {/* Role-Specific Navigation Menu */}
      <nav className="nav-links">
        <div style={{
          fontSize: '11px',
          fontWeight: '700',
          textTransform: 'uppercase',
          letterSpacing: '1px',
          color: 'var(--text-muted)',
          paddingLeft: '12px',
          marginBottom: '8px'
        }}>
          {role === 'citizen' ? 'Citizen Reporting Portal' : 'Sanitation Authority Grid'}
        </div>

        {activeNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setTab(item.id)}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} className="nav-icon" />
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  padding: '2px 7px',
                  borderRadius: '10px',
                  background: item.id === 'hotspots' ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.2)',
                  color: item.id === 'hotspots' ? '#fca5a5' : '#86efac',
                  border: item.id === 'hotspots' ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)'
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Status Badge */}
      <div className="sidebar-footer">
        <div className="system-badge">
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span>
              {role === 'citizen' ? 'Citizen Mode Active' : 'Authority Command Grid'}
            </span>
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '11px', lineHeight: '1.4' }}>
            {role === 'citizen' ? (
              <div>Public reporting & tracking enabled. Internal triage hidden.</div>
            ) : (
              <div>Operational dispatch & prioritization unlocked.</div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
