import React, { useState, useEffect } from 'react';
import { 
  Trash2, 
  Upload, 
  Sparkles, 
  CheckCircle, 
  Sliders, 
  Layers, 
  FileCheck,
  AlertCircle
} from 'lucide-react';

const DEFAULT_SAMPLES = [
  { filename: 'taco_00029.jpg', url: '/samples/waste/taco_00029.jpg' },
  { filename: 'taco_00406.jpeg', url: '/samples/waste/taco_00406.jpeg' },
  { filename: 'taco_00493.jpeg', url: '/samples/waste/taco_00493.jpeg' },
  { filename: 'taco_00495.jpeg', url: '/samples/waste/taco_00495.jpeg' },
  { filename: 'taco_00705.jpg', url: '/samples/waste/taco_00705.jpg' },
  { filename: 'taco_00767.jpg', url: '/samples/waste/taco_00767.jpg' },
  { filename: 'taco_00786.jpg', url: '/samples/waste/taco_00786.jpg' },
  { filename: 'taco_01033.jpg', url: '/samples/waste/taco_01033.jpg' },
  { filename: 'taco_01150.jpg', url: '/samples/waste/taco_01150.jpg' },
  { filename: 'taco_01152.jpg', url: '/samples/waste/taco_01152.jpg' },
  { filename: 'taco_01162.jpg', url: '/samples/waste/taco_01162.jpg' },
  { filename: 'taco_01341.jpg', url: '/samples/waste/taco_01341.jpg' }
];

export default function WasteStudio({ onReportCreated, onTrackTicket }) {
  const [samples, setSamples] = useState(DEFAULT_SAMPLES);
  const [selectedSample, setSelectedSample] = useState(DEFAULT_SAMPLES[0].filename);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(DEFAULT_SAMPLES[0].url);
  const [confThreshold, setConfThreshold] = useState(0.15);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [lastTicketId, setLastTicketId] = useState(null);

  // Ticket form state
  const [locationName, setLocationName] = useState('Campus Waterway Berm / Zone B');
  const [latitude, setLatitude] = useState(13.0827);
  const [longitude, setLongitude] = useState(80.2707);
  const [severity, setSeverity] = useState('Medium');
  const [ticketSuccess, setTicketSuccess] = useState('');

  // Fetch sample images on mount
  useEffect(() => {
    fetch('/api/samples/waste')
      .then(res => res.json())
      .then(data => {
        if (data.samples && data.samples.length > 0) {
          setSamples(data.samples);
          if (!selectedSample) {
            setSelectedSample(data.samples[0].filename);
            setPreviewUrl(data.samples[0].url || `/samples/waste/${data.samples[0].filename}`);
          }
        }
      })
      .catch(err => {
        console.warn("Using offline benchmark images. Ensure 'python api.py' is running on port 5000 for AI inference:", err);
      });
  }, []);

  const handleSampleChange = (filename) => {
    setSelectedSample(filename);
    setUploadedFile(null);
    setPreviewUrl(`/samples/waste/${filename}`);
    setResults(null);
    setTicketSuccess('');
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
      setSelectedSample('');
      setPreviewUrl(URL.createObjectURL(file));
      setResults(null);
      setTicketSuccess('');
    }
  };

  const runDetection = async () => {
    setLoading(true);
    setError('');
    setTicketSuccess('');

    const formData = new FormData();
    formData.append('conf_threshold', confThreshold.toString());

    if (uploadedFile) {
      formData.append('image', uploadedFile);
    } else if (selectedSample) {
      formData.append('sample_name', selectedSample);
    } else {
      setError('Please select or upload an image.');
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/predict/waste', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setResults(data);
        if (data.total_detections >= 5) setSeverity('High');
        else if (data.total_detections > 0) setSeverity('Medium');
        else setSeverity('Low');
      } else {
        setError(data.message || 'Detection failed.');
      }
    } catch (err) {
      setError(`Cannot connect to AI backend (${err.message}). Please ensure 'python api.py' is running on port 5000.`);
    } finally {
      setLoading(false);
    }
  };

  const [submitting, setSubmitting] = useState(false);
  const [ticketError, setTicketError] = useState('');

  const submitIncidentReport = async (e) => {
    e.preventDefault();
    if (!results) return;

    setSubmitting(true);
    setTicketError('');
    setTicketSuccess('');

    try {
      const payload = {
        report_type: 'waste',
        location_name: locationName,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        image_path: results.filename || 'uploaded_image.jpg',
        waste_counts: results.counts || {},
        total_waste_objects: results.total_detections || 0,
        severity_level: severity,
        reviewer_notes: `Detected ${results.total_detections} litter objects via YOLO11n.`
      };

      const res = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setLastTicketId(data.report_id);
        setTicketSuccess(`✅ Acknowledged! Incident Ticket #${data.report_id} filed successfully in SQLite database.`);
        if (onReportCreated) onReportCreated();
      } else {
        setTicketError(data.message || 'Failed to file ticket.');
      }
    } catch (err) {
      setTicketError(`Network error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Trash2 className="text-emerald-400" size={30} color="#10b981" />
            Waste Intelligence Studio
          </h1>
          <p className="page-subtitle">
            Autonomous visible litter object detection, spatial bounding boxes, and object tallying powered by Ultralytics YOLO11n.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.25fr', gap: '28px' }}>
        {/* Left Column: Image Selector & Config */}
        <div>
          <div className="glass-card" style={{ marginBottom: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '14px' }}>
              1. Input Source
            </h3>

            {/* Test Sample Selector */}
            <div className="form-group">
              <label className="form-label">Select Verified Test Benchmark Image:</label>
              <select 
                className="form-select"
                value={selectedSample}
                onChange={(e) => handleSampleChange(e.target.value)}
              >
                {samples.map((s) => (
                  <option key={s.filename} value={s.filename}>
                    {s.filename}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ textAlign: 'center', margin: '14px 0', color: 'var(--text-muted)', fontSize: '12px' }}>
              — OR UPLOAD NEW IMAGE —
            </div>

            {/* Upload Dropzone */}
            <label className="dropzone" style={{ display: 'block' }}>
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileUpload} 
                style={{ display: 'none' }} 
              />
              <Upload size={28} color="#10b981" style={{ margin: '0 auto 8px' }} />
              <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                {uploadedFile ? uploadedFile.name : 'Click to Upload Image (JPG/PNG)'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                Field inspection photo or drone snapshot
              </div>
            </label>

            {/* Confidence Slider */}
            <div style={{ marginTop: '20px' }}>
              <div className="slider-header">
                <span className="slider-name">Detection Confidence Threshold:</span>
                <span className="slider-val">{(confThreshold * 100).toFixed(0)}%</span>
              </div>
              <input 
                type="range" 
                min="0.05" 
                max="0.50" 
                step="0.01" 
                value={confThreshold}
                onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
              />
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                Lower thresholds capture faint litter in challenging outdoor conditions.
              </div>
            </div>

            {/* Run Button */}
            <button 
              onClick={runDetection} 
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '20px' }}
            >
              {loading ? (
                <>Analyzing with YOLO11n...</>
              ) : (
                <>
                  <Sparkles size={16} /> Run YOLO11n Detection
                </>
              )}
            </button>

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
        </div>

        {/* Right Column: Visualizer & Breakdown */}
        <div>
          <div className="glass-card">
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '17px', fontWeight: '700', marginBottom: '14px' }}>
              2. Visualizer & Detections
            </h3>

            {/* Image Preview / Annotated Result */}
            <div style={{
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              background: '#020617',
              border: '1px solid var(--border-subtle)',
              position: 'relative',
              minHeight: '260px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px'
            }}>
              {results?.annotated_image_b64 ? (
                <img 
                  src={results.annotated_image_b64} 
                  alt="YOLO11n Detections"
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              ) : previewUrl ? (
                <img 
                  src={previewUrl} 
                  alt="Source"
                  style={{ width: '100%', maxHeight: '400px', objectFit: 'contain', display: 'block' }}
                />
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                  No image selected
                </div>
              )}
            </div>

            {/* Metrics Breakdown if results present */}
            {results && (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '18px' }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      {results.total_detections}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Objects Detected
                    </div>
                  </div>

                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--emerald-400)' }}>
                      {Object.keys(results.counts || {}).length}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Categories
                    </div>
                  </div>

                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--cyan-400)' }}>
                      {Object.keys(results.counts || {}).length > 0 ? Object.keys(results.counts)[0] : 'None'}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Primary Class
                    </div>
                  </div>
                </div>

                {/* Classification Table */}
                <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '10px' }}>
                  Classification Inventory:
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
                  {Object.entries(results.counts || {}).map(([cls, count]) => {
                    const pct = Math.round((count / (results.total_detections || 1)) * 100);
                    return (
                      <div key={cls} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        background: 'rgba(15, 23, 42, 0.5)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '13px'
                      }}>
                        <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{cls}</span>
                        <span style={{ fontWeight: '700', color: 'var(--emerald-400)' }}>{count} ({pct}%)</span>
                      </div>
                    );
                  })}
                </div>

                {/* File Ticket Form */}
                <div style={{
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '20px'
                }}>
                  <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileCheck size={18} color="#10b981" />
                    File Incident Ticket to Database
                  </h4>

                  <form onSubmit={submitIncidentReport}>
                    <div className="form-group">
                      <label className="form-label">Incident Location / Landmark:</label>
                      <input 
                        className="form-input"
                        value={locationName}
                        onChange={(e) => setLocationName(e.target.value)}
                        required
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                      <div>
                        <label className="form-label">Severity Level:</label>
                        <select 
                          className="form-select"
                          value={severity}
                          onChange={(e) => setSeverity(e.target.value)}
                        >
                          <option value="Low">Low</option>
                          <option value="Medium">Medium</option>
                          <option value="High">High</option>
                          <option value="Critical">Critical</option>
                        </select>
                      </div>
                      <div>
                        <label className="form-label">Latitude / Longitude:</label>
                        <input 
                          className="form-input"
                          value={`${latitude}, ${longitude}`}
                          readOnly
                          style={{ color: 'var(--text-muted)' }}
                        />
                      </div>
                    </div>

                    <button 
                      type="submit" 
                      disabled={submitting} 
                      className="btn btn-primary" 
                      style={{ width: '100%', opacity: submitting ? 0.7 : 1 }}
                    >
                      {submitting ? 'Submitting to Triage Queue...' : 'Submit Incident to Triage Queue'}
                    </button>
                  </form>

                  {ticketSuccess && (
                    <div style={{
                      marginTop: '16px',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-md)',
                      background: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: '#86efac',
                      fontSize: '13px',
                      fontWeight: '600',
                      boxShadow: '0 0 15px rgba(16, 185, 129, 0.2)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: onTrackTicket && lastTicketId ? '10px' : '0' }}>
                        <CheckCircle size={18} /> {ticketSuccess}
                      </div>
                      {onTrackTicket && lastTicketId && (
                        <button
                          type="button"
                          onClick={() => onTrackTicket(lastTicketId)}
                          className="btn btn-secondary"
                          style={{
                            fontSize: '12px',
                            padding: '6px 12px',
                            background: 'rgba(15, 23, 42, 0.8)',
                            color: '#34d399',
                            borderColor: 'rgba(16, 185, 129, 0.4)'
                          }}
                        >
                          🔍 Track This Incident Resolution Status →
                        </button>
                      )}
                    </div>
                  )}

                  {ticketError && (
                    <div style={{
                      marginTop: '16px',
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-md)',
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid rgba(239, 68, 68, 0.4)',
                      color: '#fca5a5',
                      fontSize: '13px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px'
                    }}>
                      <AlertCircle size={18} /> {ticketError}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
