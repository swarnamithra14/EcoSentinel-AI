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
  Shield,
  Truck,
  LogOut,
  ChevronRight
} from 'lucide-react';

export default function Sidebar({ currentTab, setTab, stats, role, setRole, user, onLogout }) {
  // Navigation for Citizen
  const citizenItems = [
    { id: 'waste', label: 'Report Waste Litter', icon: Trash2 },
    { id: 'water', label: 'Check Water Safety', icon: Droplets },
    { id: 'track', label: 'Track My Incident', icon: Search },
    { id: 'workflow', label: 'Community Guide', icon: HelpCircle },
  ];

  // Navigation for Admin
  const adminItems = [
    { id: 'dashboard', label: 'Command Overview', icon: Activity },
    { id: 'hotspots', label: 'Priority Hotspots', icon: AlertTriangle, badge: stats?.critical_hotspots },
    { id: 'reports', label: 'Incident Records', icon: FileText, badge: stats?.total_reports },
    { id: 'worker-tasks', label: 'Sanitation Dispatch', icon: Truck },
    { id: 'waste', label: 'Waste Vision Studio', icon: Trash2 },
    { id: 'water', label: 'Water Analysis Lab', icon: Droplets },
    { id: 'analytics', label: 'Model Evaluation', icon: BarChart3 },
    { id: 'workflow', label: 'System Architecture', icon: HelpCircle },
  ];

  // Navigation for Sanitation Worker
  const workerItems = [
    { id: 'worker-tasks', label: 'Sanitation Orders', icon: Truck, badge: stats?.status_breakdown?.['Cleanup Assigned'] || stats?.total_reports },
    { id: 'track', label: 'Incident Lookup', icon: Search },
    { id: 'waste', label: 'Waste Vision Studio', icon: Trash2 },
    { id: 'workflow', label: 'Field Safety Guide', icon: HelpCircle },
  ];

  const getNavItems = () => {
    if (role === 'admin') return adminItems;
    if (role === 'worker') return workerItems;
    return citizenItems;
  };

  const activeNavItems = getNavItems();

  const getRoleTheme = () => {
    if (role === 'admin') return { color: '#38bdf8', label: 'Municipal Officer', icon: Shield, bg: 'rgba(14, 165, 233, 0.15)' };
    if (role === 'worker') return { color: '#fbbf24', label: 'Sanitation Worker', icon: Truck, bg: 'rgba(245, 158, 11, 0.15)' };
    return { color: 'var(--emerald-400)', label: 'Citizen Sentinel', icon: User, bg: 'rgba(16, 185, 129, 0.15)' };
  };

  const roleMeta = getRoleTheme();
  const RoleIcon = roleMeta.icon;

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="brand-header">
        <div className="brand-icon-wrapper">
          <ShieldCheck size={24} />
        </div>
        <div className="brand-text">
          <h1>EcoSentinel AI</h1>
          <span>Multi-Role Command Grid</span>
        </div>
      </div>

      {/* 3-Way Role Switcher Pill */}
      <div className="sidebar-role-pill-row">
        <button
          onClick={() => {
            setRole('citizen');
            if (['dashboard', 'hotspots', 'reports', 'analytics'].includes(currentTab)) {
              setTab('waste');
            }
          }}
          className={`role-toggle-btn ${role === 'citizen' ? 'active-citizen' : ''}`}
          title="Citizen Public Portal"
        >
          <User size={13} />
          <span>User</span>
        </button>

        <button
          onClick={() => {
            setRole('admin');
            setTab('dashboard');
          }}
          className={`role-toggle-btn ${role === 'admin' ? 'active-admin' : ''}`}
          title="Municipal Admin Portal"
        >
          <Shield size={13} />
          <span>Admin</span>
        </button>

        <button
          onClick={() => {
            setRole('worker');
            setTab('worker-tasks');
          }}
          className={`role-toggle-btn ${role === 'worker' ? 'active-worker' : ''}`}
          title="Sanitation Worker Field Portal"
        >
          <Truck size={13} />
          <span>Worker</span>
        </button>
      </div>

      {/* Role-Specific Navigation Menu */}
      <nav className="nav-links">
        <div className="nav-section-header">
          {role === 'citizen' && 'Public Resident Portal'}
          {role === 'admin' && 'Municipal Command & Triage'}
          {role === 'worker' && 'Field Crew Sanitation Orders'}
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
                <span className="nav-badge" style={{
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

      {/* User Profile Card & Sign Out */}
      <div className="sidebar-footer">
        <div className="user-profile-widget" style={{ borderColor: roleMeta.color }}>
          <div className="user-profile-left">
            <div className="user-avatar-circle" style={{ background: roleMeta.bg, color: roleMeta.color, borderColor: roleMeta.color }}>
              <RoleIcon size={18} />
            </div>
            <div className="user-profile-details">
              <div className="user-display-name">{user?.name || (role === 'admin' ? 'Officer Swarna' : role === 'worker' ? 'Ravi Kumar' : 'Surya Prakash')}</div>
              <div className="user-role-tag" style={{ color: roleMeta.color }}>
                {roleMeta.label}
              </div>
            </div>
          </div>

          {onLogout && (
            <button
              onClick={onLogout}
              className="user-logout-icon-btn"
              title="Sign Out / Switch Account"
            >
              <LogOut size={16} />
            </button>
          )}
        </div>

        {/* Live Subtitle */}
        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div className="status-dot"></div>
          <span>
            {role === 'citizen' && 'Public reporting mode'}
            {role === 'admin' && 'Full executive authority'}
            {role === 'worker' && 'Field dispatch active'}
          </span>
        </div>
      </div>
    </aside>
  );
}
