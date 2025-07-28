import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import axios from 'axios';
import AIAssistant from './components/AIAssistant';
import AnimatedParticles from './components/AnimatedParticles';
import { useDeviceMotion } from './hooks/useDeviceMotion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Audio Recording Component
const AudioRecorder = ({ onAudioRecorded }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioURL, setAudioURL] = useState('');
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {  
        audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioURL(audioUrl);
        onAudioRecorded(audioBlob, 'recorded_audio.wav');
      };

      mediaRecorder.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Please allow microphone access to record audio');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  return (
    <div className="audio-recorder">
      <div className="recorder-controls">
        {!isRecording ? (
          <button 
            onClick={startRecording}
            className="record-btn"
          >
            <div className="mic-icon">🎤</div>
            Start Recording
          </button>
        ) : (
          <button 
            onClick={stopRecording}
            className="stop-btn recording"
          >
            <div className="stop-icon">⏹️</div>
            Stop Recording
          </button>
        )}
      </div>
      
      {audioURL && (
        <div className="audio-preview">
          <audio controls src={audioURL} className="audio-player" />
        </div>
      )}
    </div>
  );
};

// File Upload Component
const FileUpload = ({ onFileSelected }) => {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      onFileSelected(file, file.name);
    }
  };

  return (
    <div className="file-upload">
      <input
        type="file"
        accept="audio/*"
        onChange={handleFileChange}
        id="audio-upload"
        className="file-input"
      />
      <label htmlFor="audio-upload" className="file-label">
        <div className="upload-icon">📁</div>
        Choose Audio File
      </label>
    </div>
  );
};

// Diagnostic Results Component
const DiagnosticResults = ({ results, isAnalyzing }) => {
  if (isAnalyzing) {
    return (
      <div className="diagnostic-results analyzing">
        <div className="analyzing-animation">
          <div className="sound-wave">
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
          </div>
          <h3>AI Analyzing Audio...</h3>
          <p>Processing sound patterns and extracting features</p>
        </div>
      </div>
    );
  }

  if (!results) return null;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#ff4757';
      case 'high': return '#ff6b81';
      case 'medium': return '#ffa726';
      case 'low': return '#4caf50';
      default: return '#64b5f6';
    }
  };

  const getUrgencyBadge = (urgency) => {
    const badges = {
      'immediate': { text: 'IMMEDIATE', color: '#ff4757' },
      'week': { text: 'THIS WEEK', color: '#ff6b81' },
      'month': { text: 'THIS MONTH', color: '#ffa726' },
      'monitoring': { text: 'MONITOR', color: '#4caf50' }
    };
    return badges[urgency] || badges['monitoring'];
  };

  return (
    <div className="diagnostic-results">
      <div className="results-header">
        <h2>🔍 Diagnostic Results</h2>
        <div className="confidence-score">
          <span>Confidence: {(results.confidence_score * 100).toFixed(1)}%</span>
          <div className="confidence-bar">
            <div 
              className="confidence-fill"
              style={{ width: `${results.confidence_score * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="diagnosis-card">
        <div className="diagnosis-header">
          <div className="component-badge">{results.component}</div>
          <div 
            className="urgency-badge"
            style={{ backgroundColor: getUrgencyBadge(results.urgency_level).color }}
          >
            {getUrgencyBadge(results.urgency_level).text}
          </div>
        </div>
        
        <h3 className="diagnosis-title">{results.diagnosis}</h3>
        
        <div className="severity-indicator">
          <div 
            className="severity-bar"
            style={{ backgroundColor: getSeverityColor(results.severity) }}
          >
            Severity: {results.severity.toUpperCase()}
          </div>
        </div>

        {results.estimated_cost > 0 && (
          <div className="cost-estimate">
            <span>💰 Estimated Cost: ${results.estimated_cost.toFixed(0)}</span>
          </div>
        )}

        <div className="recommendations">
          <h4>🔧 Recommendations:</h4>
          <ul>
            {results.recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

// Health Dashboard Component
const HealthDashboard = ({ healthData }) => {
  if (!healthData) return null;

  const getHealthColor = (score) => {
    if (score >= 85) return '#4caf50';
    if (score >= 70) return '#ffa726';
    return '#ff4757';
  };

  return (
    <div className="health-dashboard">
      <h2>🚗 Vehicle Health Overview</h2>
      
      <div className="health-grid">
        <div className="health-card overall">
          <div className="health-score-circle">
            <div 
              className="circle-progress"
              style={{ 
                background: `conic-gradient(${getHealthColor(healthData.health_scores.overall_score)} ${healthData.health_scores.overall_score * 3.6}deg, #2a2a2a 0deg)`
              }}
            >
              <div className="score-text">
                <span className="score">{healthData.health_scores.overall_score}</span>
                <span className="label">Overall</span>
              </div>
            </div>
          </div>
        </div>

        <div className="component-scores">
          <div className="component-card">
            <div className="component-icon">🔧</div>
            <div className="component-info">
              <span className="component-name">Engine</span>
              <div className="score-bar">
                <div 
                  className="score-fill"
                  style={{ 
                    width: `${healthData.health_scores.engine_health}%`,
                    backgroundColor: getHealthColor(healthData.health_scores.engine_health)
                  }}
                ></div>
              </div>
              <span className="score-value">{healthData.health_scores.engine_health}%</span>
            </div>
          </div>

          <div className="component-card">
            <div className="component-icon">🛑</div>
            <div className="component-info">
              <span className="component-name">Brakes</span>
              <div className="score-bar">
                <div 
                  className="score-fill"
                  style={{ 
                    width: `${healthData.health_scores.brake_health}%`,
                    backgroundColor: getHealthColor(healthData.health_scores.brake_health)
                  }}
                ></div>
              </div>
              <span className="score-value">{healthData.health_scores.brake_health}%</span>
            </div>
          </div>

          <div className="component-card">
            <div className="component-icon">⚙️</div>
            <div className="component-info">
              <span className="component-name">Transmission</span>
              <div className="score-bar">
                <div 
                  className="score-fill"
                  style={{ 
                    width: `${healthData.health_scores.transmission_health}%`,
                    backgroundColor: getHealthColor(healthData.health_scores.transmission_health)
                  }}
                ></div>
              </div>
              <span className="score-value">{healthData.health_scores.transmission_health}%</span>
            </div>
          </div>

          <div className="component-card">
            <div className="component-icon">💨</div>
            <div className="component-info">
              <span className="component-name">Exhaust</span>
              <div className="score-bar">
                <div 
                  className="score-fill"
                  style={{ 
                    width: `${healthData.health_scores.exhaust_health}%`,
                    backgroundColor: getHealthColor(healthData.health_scores.exhaust_health)
                  }}
                ></div>
              </div>
              <span className="score-value">{healthData.health_scores.exhaust_health}%</span>
            </div>
          </div>
        </div>
      </div>

      {healthData.alerts && healthData.alerts.length > 0 && (
        <div className="alert-section">
          <h3>⚠️ Active Alerts</h3>
          <div className="alerts-list">
            {healthData.alerts.map((alert, index) => (
              <div key={index} className={`alert ${alert.type}`}>
                <span className="alert-message">{alert.message}</span>
                <span className="alert-severity">{alert.severity}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [currentTab, setCurrentTab] = useState('analyze');
  const [diagnosticResults, setDiagnosticResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [healthData, setHealthData] = useState(null);

  useEffect(() => {
    fetchHealthOverview();
  }, []);

  const fetchHealthOverview = async () => {
    try {
      const response = await axios.get(`${API}/health-overview`);
      setHealthData(response.data);
    } catch (error) {
      console.error('Error fetching health overview:', error);
    }
  };

  const analyzeAudio = async (audioFile, filename) => {
    setIsAnalyzing(true);
    setDiagnosticResults(null);

    try {
      const formData = new FormData();
      formData.append('file', audioFile, filename);

      const response = await axios.post(`${API}/analyze-audio`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setTimeout(() => {
        setDiagnosticResults(response.data);
        setIsAnalyzing(false);
        fetchHealthOverview(); // Refresh health data
      }, 3000); // Simulate processing time
    } catch (error) {
      console.error('Error analyzing audio:', error);
      setIsAnalyzing(false);
      alert('Analysis failed. Please try again.');
    }
  };

  return (
    <div className="App">
      <div className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">🚗</div>
            <div className="brand-info">
              <h1>VehicleAI Whisperer</h1>
              <p>AI-Powered Vehicle Diagnostics</p>
            </div>
          </div>
          <nav className="nav-tabs">
            <button 
              className={`nav-tab ${currentTab === 'analyze' ? 'active' : ''}`}
              onClick={() => setCurrentTab('analyze')}
            >
              🎵 Sound Analysis
            </button>
            <button 
              className={`nav-tab ${currentTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentTab('dashboard')}
            >
              📊 Health Dashboard
            </button>
          </nav>
        </div>
      </div>

      <div className="app-content">
        {currentTab === 'analyze' && (
          <div className="analyze-section">
            <div className="hero-section">
              <img 
                src="https://images.pexels.com/photos/2422556/pexels-photo-2422556.jpeg" 
                alt="AI Diagnostics"
                className="hero-image"
              />
              <div className="hero-content">
                <h2>🎧 Upload Vehicle Audio for AI Analysis</h2>
                <p>Record or upload engine sounds, brake noises, or any vehicle audio for instant AI-powered diagnosis</p>
              </div>
            </div>

            <div className="input-section">
              <div className="input-methods">
                <div className="method-card">
                  <h3>🎤 Record Live Audio</h3>
                  <AudioRecorder onAudioRecorded={analyzeAudio} />
                </div>
                
                <div className="method-divider">OR</div>
                
                <div className="method-card">
                  <h3>📁 Upload Audio File</h3>
                  <FileUpload onFileSelected={analyzeAudio} />
                </div>
              </div>
            </div>

            <DiagnosticResults results={diagnosticResults} isAnalyzing={isAnalyzing} />
          </div>
        )}

        {currentTab === 'dashboard' && (
          <div className="dashboard-section">
            <HealthDashboard healthData={healthData} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;