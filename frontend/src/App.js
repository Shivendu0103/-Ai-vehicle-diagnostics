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

// Enhanced Diagnostic Results Component
const DiagnosticResults = ({ results, isAnalyzing }) => {
  if (isAnalyzing) {
    return (
      <motion.div 
        className="diagnostic-results analyzing"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
      >
        <div className="analyzing-animation">
          <motion.div 
            className="ai-brain"
            animate={{ 
              rotate: 360,
              scale: [1, 1.2, 1]
            }}
            transition={{ 
              rotate: { duration: 3, repeat: Infinity, ease: "linear" },
              scale: { duration: 2, repeat: Infinity }
            }}
          >
            🧠
          </motion.div>
          <motion.h3
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            AI Analyzing Audio Patterns...
          </motion.h3>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
          >
            Processing MFCC coefficients and spectral features
          </motion.p>
          
          <div className="sound-wave-analysis">
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="analysis-bar"
                animate={{ 
                  height: [10, Math.random() * 40 + 20, 10],
                  backgroundColor: ['#1976d2', '#42a5f5', '#64b5f6', '#1976d2']
                }}
                transition={{ 
                  duration: 0.8,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: "easeInOut"
                }}
              />
            ))}
          </div>
        </div>
      </motion.div>
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
      'immediate': { text: 'IMMEDIATE', color: '#ff4757', icon: '🚨' },
      'week': { text: 'THIS WEEK', color: '#ff6b81', icon: '⚠️' },
      'month': { text: 'THIS MONTH', color: '#ffa726', icon: '📅' },
      'monitoring': { text: 'MONITOR', color: '#4caf50', icon: '👁️' }
    };
    return badges[urgency] || badges['monitoring'];
  };

  return (
    <motion.div 
      className="diagnostic-results"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <motion.div 
        className="results-header"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h2>🔍 AI Diagnostic Results</h2>
        <div className="confidence-score">
          <span>Confidence: {(results.confidence_score * 100).toFixed(1)}%</span>
          <div className="confidence-bar">
            <motion.div 
              className="confidence-fill"
              initial={{ width: 0 }}
              animate={{ width: `${results.confidence_score * 100}%` }}
              transition={{ duration: 1, delay: 0.5 }}
            />
          </div>
        </div>
      </motion.div>

      <motion.div 
        className="diagnosis-card"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4, duration: 0.5 }}
        whileHover={{ y: -5, boxShadow: "0 20px 40px rgba(100, 181, 246, 0.2)" }}
      >
        <motion.div 
          className="diagnosis-header"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <motion.div 
            className="component-badge"
            whileHover={{ scale: 1.05 }}
          >
            {results.component}
          </motion.div>
          <motion.div 
            className="urgency-badge"
            style={{ backgroundColor: getUrgencyBadge(results.urgency_level).color }}
            whileHover={{ scale: 1.05 }}
            animate={{ 
              boxShadow: results.urgency_level === 'immediate' ? 
                ['0 0 0 0 rgba(255, 71, 87, 0.7)', '0 0 0 10px rgba(255, 71, 87, 0)'] : 
                'none'
            }}
            transition={{ 
              boxShadow: { duration: 1, repeat: results.urgency_level === 'immediate' ? Infinity : 0 }
            }}
          >
            {getUrgencyBadge(results.urgency_level).icon} {getUrgencyBadge(results.urgency_level).text}
          </motion.div>
        </motion.div>
        
        <motion.h3 
          className="diagnosis-title"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          {results.diagnosis}
        </motion.h3>
        
        <motion.div 
          className="severity-indicator"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1 }}
        >
          <motion.div 
            className="severity-bar"
            style={{ backgroundColor: getSeverityColor(results.severity) }}
            whileHover={{ scale: 1.02 }}
          >
            Severity: {results.severity.toUpperCase()}
          </motion.div>
        </motion.div>

        {results.estimated_cost > 0 && (
          <motion.div 
            className="cost-estimate"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.2 }}
            whileHover={{ scale: 1.02 }}
          >
            <span>💰 Estimated Cost: ${results.estimated_cost.toFixed(0)}</span>
          </motion.div>
        )}

        <motion.div 
          className="recommendations"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.4 }}
        >
          <h4>🔧 AI Recommendations:</h4>
          <ul>
            {results.recommendations.map((rec, index) => (
              <motion.li 
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.6 + index * 0.1 }}
                whileHover={{ x: 5, backgroundColor: 'rgba(255, 255, 255, 0.08)' }}
              >
                {rec}
              </motion.li>
            ))}
          </ul>
        </motion.div>
      </motion.div>
    </motion.div>
  );
};

// Enhanced Health Dashboard Component with 3D effects
const HealthDashboard = ({ healthData }) => {
  if (!healthData) return null;

  const getHealthColor = (score) => {
    if (score >= 85) return '#4caf50';
    if (score >= 70) return '#ffa726';
    return '#ff4757';
  };

  const components = [
    { name: 'Engine', icon: '🔧', health: healthData.health_scores.engine_health },
    { name: 'Brakes', icon: '🛑', health: healthData.health_scores.brake_health },
    { name: 'Transmission', icon: '⚙️', health: healthData.health_scores.transmission_health },
    { name: 'Exhaust', icon: '💨', health: healthData.health_scores.exhaust_health }
  ];

  return (
    <motion.div 
      className="health-dashboard"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        🚗 AI Vehicle Health Analysis
      </motion.h2>
      
      <div className="health-grid">
        <motion.div 
          className="health-card overall"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          whileHover={{ scale: 1.05, rotateY: 10 }}
        >
          <div className="health-score-circle">
            <motion.div 
              className="circle-progress"
              style={{ 
                background: `conic-gradient(${getHealthColor(healthData.health_scores.overall_score)} ${healthData.health_scores.overall_score * 3.6}deg, #2a2a2a 0deg)`
              }}
              initial={{ rotate: 0 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 2, delay: 0.6 }}
            >
              <div className="score-text">
                <motion.span 
                  className="score"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 1, type: "spring", stiffness: 200 }}
                >
                  {healthData.health_scores.overall_score}
                </motion.span>
                <span className="label">Overall Health</span>
              </div>
            </motion.div>
          </div>
          
          <motion.div 
            className="health-status"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
          >
            <span className={`status-text ${healthData.health_scores.overall_score >= 85 ? 'excellent' : healthData.health_scores.overall_score >= 70 ? 'good' : 'needs-attention'}`}>
              {healthData.health_scores.overall_score >= 85 ? '✨ Excellent' : 
               healthData.health_scores.overall_score >= 70 ? '👍 Good' : '⚠️ Needs Attention'}
            </span>
          </motion.div>
        </motion.div>

        <div className="component-scores">
          {components.map((component, index) => (
            <motion.div 
              key={component.name}
              className="component-card"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 + index * 0.1, duration: 0.5 }}
              whileHover={{ 
                x: 10, 
                boxShadow: "0 10px 30px rgba(100, 181, 246, 0.2)",
                backgroundColor: "rgba(255, 255, 255, 0.05)"
              }}
            >
              <motion.div 
                className="component-icon"
                whileHover={{ scale: 1.2, rotate: 5 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                {component.icon}
              </motion.div>
              <div className="component-info">
                <span className="component-name">{component.name}</span>
                <div className="score-bar">
                  <motion.div 
                    className="score-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${component.health}%` }}
                    transition={{ delay: 1 + index * 0.1, duration: 1, ease: "easeOut" }}
                    style={{ backgroundColor: getHealthColor(component.health) }}
                  />
                </div>
                <motion.span 
                  className="score-value"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.5 + index * 0.1 }}
                >
                  {component.health}%
                </motion.span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {healthData.alerts && healthData.alerts.length > 0 && (
        <motion.div 
          className="alert-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.8 }}
        >
          <h3>⚠️ Active Alerts</h3>
          <div className="alerts-list">
            {healthData.alerts.map((alert, index) => (
              <motion.div 
                key={index} 
                className={`alert ${alert.type}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 2 + index * 0.1 }}
                whileHover={{ scale: 1.02, x: 5 }}
              >
                <span className="alert-message">{alert.message}</span>
                <motion.span 
                  className="alert-severity"
                  animate={alert.severity === 'high' ? { 
                    scale: [1, 1.1, 1],
                    color: ['#f44336', '#ff6b81', '#f44336']
                  } : {}}
                  transition={{ duration: 2, repeat: alert.severity === 'high' ? Infinity : 0 }}
                >
                  {alert.severity}
                </motion.span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

# PWA Install Prompt Component
const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstall = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`User response to the install prompt: ${outcome}`);
      setDeferredPrompt(null);
      setShowPrompt(false);
    }
  };

  if (!showPrompt) return null;

  return (
    <AnimatePresence>
      <motion.div 
        className="pwa-install-prompt"
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 50 }}
        transition={{ duration: 0.5 }}
      >
        <div className="prompt-content">
          <div className="prompt-icon">📱</div>
          <div className="prompt-text">
            <h4>Install VehicleAI Whisperer</h4>
            <p>Get the full app experience with offline diagnostics</p>
          </div>
          <div className="prompt-actions">
            <motion.button 
              className="install-btn"
              onClick={handleInstall}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Install
            </motion.button>
            <motion.button 
              className="dismiss-btn"
              onClick={() => setShowPrompt(false)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Later
            </motion.button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

// Main App Component
function App() {
  const [currentTab, setCurrentTab] = useState('analyze');
  const [diagnosticResults, setDiagnosticResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [healthData, setHealthData] = useState(null);
  const [audioFeatures, setAudioFeatures] = useState(null);
  const { motion: deviceMotion, requestPermission, isSupported: motionSupported } = useDeviceMotion();

  useEffect(() => {
    fetchHealthOverview();
    registerServiceWorker();
    
    // Request device motion permission on mobile
    if (motionSupported && /Mobi|Android/i.test(navigator.userAgent)) {
      requestPermission();
    }
  }, []);

  const registerServiceWorker = async () => {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('SW registered:', registration);
      } catch (error) {
        console.log('SW registration failed:', error);
      }
    }
  };

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

      // Store audio features for AI assistant
      setAudioFeatures({
        filename: filename,
        duration: 3, // placeholder
        mfcc_features: Array.from({length: 13}, () => Math.random())
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

  const handleAIAnalysisComplete = (aiAnalysis) => {
    // Merge AI analysis with existing results
    if (diagnosticResults) {
      setDiagnosticResults({
        ...diagnosticResults,
        aiExplanation: aiAnalysis.aiExplanation,
        ...aiAnalysis
      });
    }
  };

  return (
    <div className="App">
      <PWAInstallPrompt />
      
      <motion.div 
        className="app-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="header-content">
          <motion.div 
            className="logo-section"
            whileHover={{ scale: 1.02 }}
          >
            <motion.div 
              className="logo"
              animate={{ rotate: [0, 5, -5, 0] }}
              transition={{ duration: 4, repeat: Infinity }}
            >
              🚗
            </motion.div>
            <div className="brand-info">
              <h1>VehicleAI Whisperer</h1>
              <p>AI-Powered Vehicle Diagnostics • Now with Voice Control</p>
            </div>
          </motion.div>
          <nav className="nav-tabs">
            <motion.button 
              className={`nav-tab ${currentTab === 'analyze' ? 'active' : ''}`}
              onClick={() => setCurrentTab('analyze')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              🎵 AI Sound Analysis
            </motion.button>
            <motion.button 
              className={`nav-tab ${currentTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentTab('dashboard')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              📊 Health Dashboard
            </motion.button>
          </nav>
        </div>
      </motion.div>

      <div className="app-content">
        <AnimatePresence mode="wait">
          {currentTab === 'analyze' && (
            <motion.div 
              key="analyze"
              className="analyze-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.5 }}
            >
              <motion.div 
                className="hero-section"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2, duration: 0.6 }}
              >
                <img 
                  src="https://images.pexels.com/photos/2422556/pexels-photo-2422556.jpeg" 
                  alt="AI Diagnostics"
                  className="hero-image"
                />
                <div className="hero-content">
                  <motion.h2
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                  >
                    🎧 Upload Vehicle Audio for AI Analysis
                  </motion.h2>
                  <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                  >
                    Record or upload engine sounds, brake noises, or any vehicle audio for instant AI-powered diagnosis with voice control
                  </motion.p>
                </div>
              </motion.div>

              <motion.div 
                className="input-section"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.6 }}
              >
                <div className="input-methods">
                  <div className="method-card">
                    <h3>🎤 Record Live Audio with AI</h3>
                    <AudioRecorder onAudioRecorded={analyzeAudio} />
                  </div>
                  
                  <motion.div 
                    className="method-divider"
                    animate={{ rotate: [0, 180, 360] }}
                    transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                  >
                    OR
                  </motion.div>
                  
                  <div className="method-card">
                    <h3>📁 Upload Audio File</h3>
                    <FileUpload onFileSelected={analyzeAudio} />
                  </div>
                </div>
              </motion.div>

              <AnimatePresence>
                {(isAnalyzing || diagnosticResults) && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <DiagnosticResults results={diagnosticResults} isAnalyzing={isAnalyzing} />
                    
                    {(diagnosticResults || audioFeatures) && (
                      <AIAssistant 
                        diagnosticData={audioFeatures}
                        onAnalysisComplete={handleAIAnalysisComplete}
                      />
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {currentTab === 'dashboard' && (
            <motion.div 
              key="dashboard"
              className="dashboard-section"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.5 }}
            >
              <HealthDashboard healthData={healthData} />
              
              {motionSupported && (
                <motion.div 
                  className="sensor-data"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                >
                  <h3>📱 Device Motion Sensors</h3>
                  <div className="sensor-grid">
                    <div className="sensor-card">
                      <h4>Acceleration</h4>
                      <p>X: {deviceMotion.accelerationIncludingGravity.x?.toFixed(2) || 0}</p>
                      <p>Y: {deviceMotion.accelerationIncludingGravity.y?.toFixed(2) || 0}</p>
                      <p>Z: {deviceMotion.accelerationIncludingGravity.z?.toFixed(2) || 0}</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;