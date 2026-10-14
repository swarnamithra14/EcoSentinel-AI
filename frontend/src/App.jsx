import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import WasteStudio from './pages/WasteStudio';
import WaterLab from './pages/WaterLab';
import HotspotsView from './pages/HotspotsView';
import ReportsTracker from './pages/ReportsTracker';
import AnalyticsView from './pages/AnalyticsView';
import WorkflowGuide from './pages/WorkflowGuide';
import TrackTicket from './pages/TrackTicket';
import SanitationWorkerPortal from './pages/SanitationWorkerPortal';
import LoginPage from './pages/LoginPage';
import { LogOut, User, Shield, Truck, Sparkles } from 'lucide-react';

export default function App() {
  // Authentication State
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('ecosentinel_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [role, setRole] = useState(() => {
    try {
      const saved = localStorage.getItem('ecosentinel_user');
      return saved ? JSON.parse(saved).role : 'citizen';
    } catch {
      return 'citizen';
    }
  });

  // Current active navigation tab
  const [currentTab, setCurrentTab] = useState(() => {
    if (!user) return 'waste';
    if (user.role === 'admin') return 'dashboard';
    if (user.role === 'worker') return 'worker-tasks';
    return 'waste';
  });

  const [stats, setStats] = useState(null);
  const [trackingTicketId, setTrackingTicketId] = useState('');

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch telemetry stats:", err);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setRole(userData.role);
    localStorage.setItem('ecosentinel_user', JSON.stringify(userData));

    // Open respective landing page
    if (userData.role === 'admin') {
      setCurrentTab('dashboard');
    } else if (userData.role === 'worker') {
      setCurrentTab('worker-tasks');
    } else {
      setCurrentTab('waste');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('ecosentinel_user');
    setUser(null);
    setRole('citizen');
    setCurrentTab('waste');
  };

  const handleRoleChange = (newRole) => {
    setRole(newRole);
    if (user) {
      const updatedUser = { ...user, role: newRole };
      setUser(updatedUser);
      localStorage.setItem('ecosentinel_user', JSON.stringify(updatedUser));
    }
    // Route to respective primary page on role change
    if (newRole === 'admin') setCurrentTab('dashboard');
    else if (newRole === 'worker') setCurrentTab('worker-tasks');
    else setCurrentTab('waste');
  };

  const handleTrackTicket = (ticketId) => {
    setTrackingTicketId(ticketId);
    setCurrentTab('track');
  };

  // If not logged in, display the beautiful modern LoginPage
  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // Role Theme configurations
  const roleThemeMeta = {
    citizen: {
      title: '👤 Citizen Public Reporting Portal',
      desc: 'Spot, photograph, report litter & test water contamination. Internal triage actions are restricted to authorities.',
      bg: 'rgba(16, 185, 129, 0.08)',
      border: '1px solid rgba(16, 185, 129, 0.25)',
      color: 'var(--emerald-400)',
      icon: User
    },
    admin: {
      title: '🛡️ Municipal Sanitation Command Grid Active',
      desc: 'Operational dispatch mode: Citywide hotspot risk prioritization, sanitation truck assignment, and lifecycle resolution unlocked.',
      bg: 'rgba(14, 165, 233, 0.08)',
      border: '1px solid rgba(14, 165, 233, 0.25)',
      color: '#38bdf8',
      icon: Shield
    },
    worker: {
      title: '🚛 Sanitation Field Operations & Route Dispatch',
      desc: 'Active cleanup crew mode: Real-time work orders, GPS waypoint routing, safety protocols, and post-cleanup photo evidence verification.',
      bg: 'rgba(245, 158, 11, 0.08)',
      border: '1px solid rgba(245, 158, 11, 0.25)',
      color: '#fbbf24',
      icon: Truck
    }
  };

  const currentTheme = roleThemeMeta[role] || roleThemeMeta.citizen;
  const RoleIcon = currentTheme.icon;

  return (
    <div className="app-layout">
      {/* Fixed Sidebar Navigation */}
      <Sidebar 
        currentTab={currentTab} 
        setTab={setCurrentTab} 
        stats={stats} 
        role={role}
        setRole={handleRoleChange}
        user={user}
        onLogout={handleLogout}
      />

      {/* Main Content Viewport */}
      <main className="main-wrapper">
        
        {/* Role Notification Banner */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 20px',
          borderRadius: 'var(--radius-md)',
          background: currentTheme.bg,
          border: currentTheme.border,
          marginBottom: '24px',
          fontSize: '13px',
          backdropFilter: 'blur(10px)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: currentTheme.bg,
              border: currentTheme.border,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: currentTheme.color
            }}>
              <RoleIcon size={16} />
            </div>

            <div>
              <div style={{ fontWeight: '700', color: currentTheme.color, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>{currentTheme.title}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '400' }}>
                  ({user.name} • {user.badge_id || 'ID#101'})
                </span>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
                {currentTheme.desc}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {/* Quick Switch Dropdown or Button */}
            <button
              onClick={() => {
                const nextRole = role === 'citizen' ? 'admin' : role === 'admin' ? 'worker' : 'citizen';
                handleRoleChange(nextRole);
              }}
              className="btn btn-secondary"
              style={{ fontSize: '11px', padding: '6px 12px' }}
              title="Quickly test another role"
            >
              Switch Role ➔ {role === 'citizen' ? 'Admin' : role === 'admin' ? 'Worker' : 'Citizen'}
            </button>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ fontSize: '11px', padding: '6px 12px', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#fca5a5' }}
              title="Log out and return to Login Page"
            >
              <LogOut size={13} style={{ marginRight: '4px' }} /> Sign Out
            </button>
          </div>
        </div>

        {/* ============================================================== */}
        {/* ROLE-SPECIFIC & SHARED VIEWS                                   */}
        {/* ============================================================== */}

        {/* 1. Sanitation Worker Dedicated Field Portal */}
        {currentTab === 'worker-tasks' && (
          <SanitationWorkerPortal 
            user={user} 
            onRefreshStats={fetchStats} 
          />
        )}

        {/* 2. Citizen & Shared Pages */}
        {currentTab === 'waste' && (
          <WasteStudio 
            onReportCreated={fetchStats} 
            onTrackTicket={handleTrackTicket}
          />
        )}

        {currentTab === 'water' && (
          <WaterLab 
            onReportCreated={fetchStats} 
            onTrackTicket={handleTrackTicket}
          />
        )}

        {currentTab === 'track' && (
          <TrackTicket 
            initialTicketId={trackingTicketId}
            setTab={setCurrentTab}
          />
        )}

        {/* 3. Admin Operational Command Pages */}
        {currentTab === 'dashboard' && role === 'admin' && (
          <Dashboard 
            stats={stats} 
            setTab={setCurrentTab} 
          />
        )}

        {currentTab === 'hotspots' && role === 'admin' && (
          <HotspotsView 
            onRefreshNeeded={fetchStats} 
          />
        )}

        {currentTab === 'reports' && role === 'admin' && (
          <ReportsTracker 
            onRefreshNeeded={fetchStats} 
          />
        )}

        {currentTab === 'analytics' && role === 'admin' && (
          <AnalyticsView />
        )}

        {/* 4. Workflow & Technical Architecture Guide */}
        {currentTab === 'workflow' && (
          <WorkflowGuide 
            setTab={setCurrentTab} 
          />
        )}

      </main>
    </div>
  );
}
