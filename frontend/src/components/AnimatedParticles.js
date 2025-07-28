import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

// Animated particles component for sound visualization
const AnimatedParticles = ({ isActive, audioData }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef();
  const particlesRef = useRef([]);

  // Particle class
  class Particle {
    constructor(canvas) {
      this.canvas = canvas;
      this.reset();
      this.life = Math.random() * 60 + 60;
      this.maxLife = this.life;
    }

    reset() {
      this.x = Math.random() * this.canvas.width;
      this.y = Math.random() * this.canvas.height;
      this.vx = (Math.random() - 0.5) * 2;
      this.vy = (Math.random() - 0.5) * 2;
      this.radius = Math.random() * 3 + 1;
      this.opacity = Math.random() * 0.5 + 0.5;
      this.color = `hsla(${Math.random() * 360}, 70%, 60%, ${this.opacity})`;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.life--;

      // Fade out over time
      this.opacity = (this.life / this.maxLife) * 0.8;

      // Reset if dead or out of bounds
      if (this.life <= 0 || this.x < 0 || this.x > this.canvas.width || 
          this.y < 0 || this.y > this.canvas.height) {
        this.reset();
        this.life = this.maxLife;
      }
    }

    draw(ctx) {
      ctx.save();
      ctx.globalAlpha = this.opacity;
      ctx.fillStyle = this.color;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  // Initialize particles
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const particleCount = 50;

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create particles
    particlesRef.current = Array.from({ length: particleCount }, () => new Particle(canvas));

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let audioIntensity = 0;

    const animate = () => {
      // Clear canvas with fade effect
      ctx.fillStyle = 'rgba(15, 20, 25, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Update audio intensity from audio data
      if (audioData && audioData.length > 0) {
        audioIntensity = audioData.reduce((sum, val) => sum + Math.abs(val), 0) / audioData.length;
      } else {
        audioIntensity *= 0.95; // Fade out when no audio
      }

      // Update and draw particles
      particlesRef.current.forEach((particle, index) => {
        if (isActive) {
          // Make particles more active when sound is being analyzed
          particle.vx += (Math.random() - 0.5) * 0.2 * audioIntensity;
          particle.vy += (Math.random() - 0.5) * 0.2 * audioIntensity;
          particle.radius = Math.max(1, particle.radius + audioIntensity * 0.5);
        }
        
        particle.update();
        particle.draw(ctx);
      });

      // Draw audio waveform if available
      if (audioData && audioData.length > 0 && isActive) {
        ctx.strokeStyle = 'rgba(100, 181, 246, 0.6)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        const barWidth = canvas.width / audioData.length;
        audioData.forEach((amplitude, i) => {
          const barHeight = (amplitude * canvas.height) / 2;
          const x = i * barWidth;
          const y = canvas.height / 2;
          
          if (i === 0) {
            ctx.moveTo(x, y + barHeight);
          } else {
            ctx.lineTo(x, y + barHeight);
          }
        });
        
        ctx.stroke();
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    if (isActive) {
      animate();
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, audioData]);

  return (
    <motion.div 
      className="particle-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: isActive ? 1 : 0.3 }}
      transition={{ duration: 0.5 }}
    >
      <canvas
        ref={canvasRef}
        className="particles-canvas"
        style={{
          width: '100%',
          height: '200px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.1), rgba(66, 165, 245, 0.05))'
        }}
      />
      
      {isActive && (
        <motion.div 
          className="sound-indicator"
          animate={{ 
            scale: [1, 1.2, 1],
            opacity: [0.5, 1, 0.5]
          }}
          transition={{ 
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="sound-waves">
            <motion.div 
              className="wave"
              animate={{ scaleY: [1, 2, 1] }}
              transition={{ duration: 0.5, repeat: Infinity, delay: 0 }}
            />
            <motion.div 
              className="wave"
              animate={{ scaleY: [1, 1.5, 1] }}
              transition={{ duration: 0.5, repeat: Infinity, delay: 0.1 }}
            />
            <motion.div 
              className="wave"
              animate={{ scaleY: [1, 2.5, 1] }}
              transition={{ duration: 0.5, repeat: Infinity, delay: 0.2 }}
            />
            <motion.div 
              className="wave"
              animate={{ scaleY: [1, 1.8, 1] }}
              transition={{ duration: 0.5, repeat: Infinity, delay: 0.3 }}
            />
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default AnimatedParticles;