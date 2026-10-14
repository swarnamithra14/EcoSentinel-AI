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

export default function App() {
  const [role, setRole] = useState('citizen'); // 'citizen' or 'admin'
  const [currentTab, setCurrentTab] = useState('waste'); // citizen starts at report waste
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

  const handleTrackTicket = (ticketId) => {
    setTrackingTicketId(ticketId);
    setCurrentTab('track');
  };

  return (
    <div className="app-layout">
      {/* Fixed Sidebar Navigation with Role Switcher */}
      <Sidebar 
        currentTab={currentTab} 
        setTab={setCurrentTab} 
        stats={stats} 
        role={role}
        setRole={setRole}
      />

      {/* Main Content Viewport */}
      <main className="main-wrapper">
        {/* Role Notice Banner */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 18px',
          borderRadius: 'var(--radius-md)',
          background: role === 'citizen' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(14, 165, 233, 0.08)',
          border: role === 'citizen' ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid rgba(14, 165, 233, 0.25)',
          marginBottom: '24px',
          fontSize: '13px'
        }}>
          <div>
            <span style={{ fontWeight: '700', color: role === 'citizen' ? 'var(--emerald-400)' : '#38bdf8' }}>
              {role === 'citizen' ? '👤 Citizen Public Portal Mode' : '🛡️ Municipal Sanitation Command Active'}
            </span>
            <span style={{ color: 'var(--text-secondary)', marginLeft: '10px' }}>
              {role === 'citizen' 
                ? 'Spot, photograph, report litter & water contamination. Internal triage actions are restricted to authorities.' 
                : 'Operational dispatch mode: Triage prioritization, sanitation truck assignment, and lifecycle resolution unlocked.'}
            </span>
          </div>

          <button
            onClick={() => {
              const nextRole = role === 'citizen' ? 'admin' : 'citizen';
              setRole(nextRole);
              if (nextRole === 'admin') setCurrentTab('dashboard');
              else setCurrentTab('waste');
            }}
            className="btn btn-secondary"
            style={{ fontSize: '11px', padding: '4px 10px' }}
          >
            Switch to {role === 'citizen' ? 'Authority View ➔' : 'Citizen View ➔'}
          </button>
        </div>

        {/* Citizen & Shared Pages */}
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

        {/* Admin Operational Pages */}
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

        {/* Shared Guides */}
        {currentTab === 'workflow' && (
          <WorkflowGuide 
            setTab={setCurrentTab} 
          />
        )}
      </main>
    </div>
  );
}
