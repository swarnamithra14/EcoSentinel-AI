import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Layers, 
  CheckCircle2, 
  TrendingUp, 
  ShieldCheck, 
  FileText
} from 'lucide-react';

export default function AnalyticsView() {
  const [metrics, setMetrics] = useState(null);
  const [activeTab, setActiveTab] = useState('waste');

  useEffect(() => {
    fetch('/api/evaluation/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error(err));
  }, []);

  const waste = metrics?.waste || {};
  const water = metrics?.water || {};

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <BarChart3 className="text-emerald-400" size={30} color="#10b981" />
            Model Evaluation & Analytics Cards
          </h1>
          <p className="page-subtitle">
            Empirical benchmark metrics, confusion matrices, and feature importance profiles from real held-out test splits.
          </p>
        </div>

        {/* Tab Toggle */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(15, 23, 42, 0.7)', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => setActiveTab('waste')}
            style={{
              background: activeTab === 'waste' ? 'var(--emerald-600)' : 'transparent',
              color: activeTab === 'waste' ? '#ffffff' : 'var(--text-secondary)',
              border: 'none',
              padding: '6px 16px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Waste Model (YOLO11n)
          </button>
          <button
            onClick={() => setActiveTab('water')}
            style={{
              background: activeTab === 'water' ? 'var(--cyan-600)' : 'transparent',
              color: activeTab === 'water' ? '#ffffff' : 'var(--text-secondary)',
              border: 'none',
              padding: '6px 16px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Water Model (Random Forest)
          </button>
        </div>
      </div>

      {activeTab === 'waste' ? (
        <div>
          {/* Key Metrics Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon emerald"><TrendingUp size={24} /></div>
              <div>
                <div className="stat-value">46.9%</div>
                <div className="stat-label">Test mAP@0.5</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon cyan"><Layers size={24} /></div>
              <div>
                <div className="stat-value">31.9%</div>
                <div className="stat-label">Test mAP@0.5:0.95</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon amber"><BarChart3 size={24} /></div>
              <div>
                <div className="stat-value">59.6%</div>
                <div className="stat-label">Recall on Test Split</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon rose"><CheckCircle2 size={24} /></div>
              <div>
                <div className="stat-value">15 Epochs</div>
                <div className="stat-label">Fine-Tuned Checkpoint</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            <div className="glass-card">
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '14px' }}>
                Normalized Confusion Matrix
              </h3>
              <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img 
                  src="/api/evaluation/images/waste_confusion_matrix_normalized.png" 
                  alt="Waste Confusion Matrix"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '14px' }}>
                15-Epoch Training & Loss Curves
              </h3>
              <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img 
                  src="/api/evaluation/images/waste_results.png" 
                  alt="Waste Training Loss Results"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div>
          {/* Water Metrics Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon cyan"><TrendingUp size={24} /></div>
              <div>
                <div className="stat-value">99.64%</div>
                <div className="stat-label">Overall Test Accuracy</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon emerald"><CheckCircle2 size={24} /></div>
              <div>
                <div className="stat-value">0.9973</div>
                <div className="stat-label">Macro F1 Score</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon amber"><Layers size={24} /></div>
              <div>
                <div className="stat-value">150 Trees</div>
                <div className="stat-label">Balanced Forest Depth 12</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon rose"><ShieldCheck size={24} /></div>
              <div>
                <div className="stat-value">Zero Leakage</div>
                <div className="stat-label">Statutory CPCB Split</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            <div className="glass-card">
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '14px' }}>
                Random Forest Feature Importance
              </h3>
              <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img 
                  src="/api/evaluation/images/water_feature_importance.png" 
                  alt="Feature Importance"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '14px' }}>
                Multi-Class Confusion Matrix
              </h3>
              <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img 
                  src="/api/evaluation/images/water_confusion_matrix_normalized.png" 
                  alt="Water Confusion Matrix"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
