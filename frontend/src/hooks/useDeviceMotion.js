import { useState, useEffect, useCallback } from 'react';

// Custom hook for device motion and orientation sensors
export const useDeviceMotion = () => {
  const [motion, setMotion] = useState({
    acceleration: { x: 0, y: 0, z: 0 },
    accelerationIncludingGravity: { x: 0, y: 0, z: 0 },
    rotationRate: { alpha: 0, beta: 0, gamma: 0 },
    interval: 0
  });
  
  const [orientation, setOrientation] = useState({
    alpha: 0, // Z axis
    beta: 0,  // X axis  
    gamma: 0  // Y axis
  });
  
  const [isSupported, setIsSupported] = useState(false);
  const [isPermissionGranted, setIsPermissionGranted] = useState(false);

  // Request permission for iOS devices
  const requestPermission = useCallback(async () => {
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        const permission = await DeviceOrientationEvent.requestPermission();
        setIsPermissionGranted(permission === 'granted');
        return permission === 'granted';
      } catch (error) {
        console.error('Error requesting device motion permission:', error);
        return false;
      }
    } else {
      // Non-iOS devices
      setIsPermissionGranted(true);
      return true;
    }
  }, []);

  useEffect(() => {
    // Check if device motion APIs are supported
    const supported = 'DeviceMotionEvent' in window && 'DeviceOrientationEvent' in window;
    setIsSupported(supported);

    if (!supported) return;

    const handleDeviceMotion = (event) => {
      setMotion({
        acceleration: event.acceleration || { x: 0, y: 0, z: 0 },
        accelerationIncludingGravity: event.accelerationIncludingGravity || { x: 0, y: 0, z: 0 },
        rotationRate: event.rotationRate || { alpha: 0, beta: 0, gamma: 0 },
        interval: event.interval || 0
      });
    };

    const handleDeviceOrientation = (event) => {
      setOrientation({
        alpha: event.alpha || 0,
        beta: event.beta || 0,
        gamma: event.gamma || 0
      });
    };

    if (isPermissionGranted) {
      window.addEventListener('devicemotion', handleDeviceMotion);
      window.addEventListener('deviceorientation', handleDeviceOrientation);
    }

    return () => {
      window.removeEventListener('devicemotion', handleDeviceMotion);
      window.removeEventListener('deviceorientation', handleDeviceOrientation);
    };
  }, [isPermissionGranted]);

  // Calculate movement intensity for diagnostic purposes
  const getMovementIntensity = useCallback(() => {
    const { accelerationIncludingGravity } = motion;
    return Math.sqrt(
      Math.pow(accelerationIncludingGravity.x, 2) +
      Math.pow(accelerationIncludingGravity.y, 2) +
      Math.pow(accelerationIncludingGravity.z, 2)
    );
  }, [motion]);

  // Detect significant vehicle events (sudden stops, hard turns, etc.)
  const detectVehicleEvents = useCallback(() => {
    const intensity = getMovementIntensity();
    const { rotationRate } = motion;
    
    // Thresholds for different events
    const HARD_BRAKE_THRESHOLD = 15;
    const SHARP_TURN_THRESHOLD = 200;
    
    const events = [];
    
    if (intensity > HARD_BRAKE_THRESHOLD) {
      events.push({ type: 'hard_brake', intensity, timestamp: Date.now() });
    }
    
    if (Math.abs(rotationRate.alpha) > SHARP_TURN_THRESHOLD) {
      events.push({ type: 'sharp_turn', rotation: rotationRate.alpha, timestamp: Date.now() });
    }
    
    return events;
  }, [motion, getMovementIntensity]);

  return {
    motion,
    orientation,
    isSupported,
    isPermissionGranted,
    requestPermission,
    getMovementIntensity,
    detectVehicleEvents
  };
};