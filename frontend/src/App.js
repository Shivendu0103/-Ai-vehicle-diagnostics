import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import axios from 'axios';
import AIAssistant from './components/AIAssistant';
import AnimatedParticles from './components/AnimatedParticles';
import { useDeviceMotion } from './hooks/useDeviceMotion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Audio Recording Component with enhanced animations
const AudioRecorder = ({ onAudioRecorded }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioURL, setAudioURL] = useState('');
  const [audioData, setAudioData] = useState([]);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const audioContext = useRef(null);
  const analyser = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Set up audio analysis
      audioContext.current = new (window.AudioContext || window.webkitAudioContext)();
      analyser.current = audioContext.current.createAnalyser();
      const source = audioContext.current.createMediaStreamSource(stream);
      source.connect(analyser.current);
      analyser.current.fftSize = 256;
      
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
        
        // Clean up
        if (audioContext.current) {
          audioContext.current.close();
        }
      };

      // Start real-time audio visualization
      const updateAudioData = () => {
        if (analyser.current && isRecording) {
          const bufferLength = analyser.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          analyser.current.getByteFrequencyData(dataArray);
          setAudioData(Array.from(dataArray).map(val => val / 255));
          requestAnimationFrame(updateAudioData);
        }
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      updateAudioData();
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Please allow microphone access to record audio');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      setAudioData([]);
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  return (
    <motion.div 
      className="audio-recorder"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <AnimatedParticles isActive={isRecording} audioData={audioData} />
      
      <div className="recorder-controls">
        <AnimatePresence>
          {!isRecording ? (
            <motion.button 
              onClick={startRecording}
              className="record-btn"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div 
                className="mic-icon"
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                🎤
              </motion.div>
              Start Recording
            </motion.button>
          ) : (
            <motion.button 
              onClick={stopRecording}
              className="stop-btn recording"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div 
                className="stop-icon"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                ⏹️
              </motion.div>
              Stop Recording
            </motion.button>
          )}
        </AnimatePresence>
      </div>
      
      {audioURL && (
        <motion.div 
          className="audio-preview"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.5 }}
        >
          <audio controls src={audioURL} className="audio-player" />
        </motion.div>
      )}
    </motion.div>
  );
};

// File Upload Component with drag and drop animations
const FileUpload = ({ onFileSelected }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      onFileSelected(file, file.name);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelected(files[0], files[0].name);
    }
  };

  return (
    <motion.div 
      className="file-upload"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <motion.div
        className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        whileHover={{ scale: 1.02 }}
        animate={{
          borderColor: isDragOver ? '#42a5f5' : '#rgba(255,255,255,0.1)',
          backgroundColor: isDragOver ? 'rgba(66, 165, 245, 0.1)' : 'transparent'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={handleFileChange}
          id="audio-upload"
          className="file-input"
        />
        
        <label htmlFor="audio-upload" className="file-label">
          <motion.div 
            className="upload-icon"
            animate={{ y: isDragOver ? [-5, 5, -5] : 0 }}
            transition={{ duration: 0.5, repeat: isDragOver ? Infinity : 0 }}
          >
            📁
          </motion.div>
          <div className="upload-text">
            <p className="primary-text">Choose Audio File</p>
            <p className="secondary-text">or drag and drop here</p>
            <p className="format-text">Supports WAV, MP3, M4A, OGG</p>
          </div>
        </label>
      </motion.div>
    </motion.div>
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