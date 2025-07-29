#!/usr/bin/env python3
"""
Eniguity Backend API Testing Suite - MP3 Audio Upload Focus
Tests all backend endpoints with special focus on MP3 audio processing
"""

import requests
import json
import os
import tempfile
import wave
import numpy as np
from datetime import datetime
import time
import struct

# Get backend URL from frontend environment
BACKEND_URL = "http://127.0.0.1:8000"

class VehicleAITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if response_data and not success:
            print(f"   Response: {response_data}")
    
    def create_test_audio_file(self):
        """Create a test WAV audio file for testing"""
        try:
            # Generate a simple sine wave audio (simulating engine sound)
            duration = 2.0  # seconds
            sample_rate = 44100
            frequency = 440  # Hz (A4 note)
            
            # Generate sine wave
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t)
            
            # Add some noise to make it more realistic
            noise = np.random.normal(0, 0.1, audio_data.shape)
            audio_data = audio_data + noise
            
            # Normalize to 16-bit range
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # Create temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            with wave.open(temp_file.name, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return temp_file.name
        except Exception as e:
            self.log_test("Audio File Creation", False, f"Failed to create test audio: {str(e)}")
            return None
    
    def test_health_check(self):
        """Test basic API health check"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "VehicleAI Diagnostics API" in data.get("message", ""):
                    self.log_test("Health Check", True, "API is responding correctly", data)
                    return True
                else:
                    self.log_test("Health Check", False, "Unexpected response format", data)
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_health_overview(self):
        """Test health overview dashboard API"""
        try:
            response = self.session.get(f"{self.base_url}/health-overview")
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields
                required_fields = ['health_scores', 'recent_diagnostics', 'alerts', 'total_diagnostics']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Health Overview", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Verify health scores structure
                health_scores = data['health_scores']
                score_fields = ['overall_score', 'engine_health', 'brake_health', 'transmission_health', 'exhaust_health']
                missing_scores = [field for field in score_fields if field not in health_scores]
                
                if missing_scores:
                    self.log_test("Health Overview", False, f"Missing health score fields: {missing_scores}", data)
                    return False
                
                # Verify score ranges (should be 0-100)
                for field in score_fields:
                    score = health_scores[field]
                    if not isinstance(score, int) or score < 0 or score > 100:
                        self.log_test("Health Overview", False, f"Invalid score range for {field}: {score}", data)
                        return False
                
                self.log_test("Health Overview", True, "Health dashboard data structure is correct", {
                    'health_scores': health_scores,
                    'alerts_count': len(data['alerts']),
                    'total_diagnostics': data['total_diagnostics']
                })
                return True
            else:
                self.log_test("Health Overview", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Overview", False, f"Request error: {str(e)}")
            return False
    
    def test_audio_analysis(self):
        """Test audio upload and analysis API"""
        audio_file_path = self.create_test_audio_file()
        if not audio_file_path:
            return False
        
        try:
            # Test audio upload
            with open(audio_file_path, 'rb') as audio_file:
                files = {'file': ('test_engine_sound.wav', audio_file, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            # Clean up temp file
            os.unlink(audio_file_path)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields in response
                required_fields = [
                    'id', 'audio_filename', 'component', 'diagnosis', 
                    'confidence_score', 'severity', 'recommendations', 
                    'urgency_level', 'created_at'
                ]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Audio Analysis", False, f"Missing response fields: {missing_fields}", data)
                    return False
                
                # Verify data types and ranges
                if not isinstance(data['confidence_score'], (int, float)) or data['confidence_score'] < 0 or data['confidence_score'] > 1:
                    self.log_test("Audio Analysis", False, f"Invalid confidence score: {data['confidence_score']}", data)
                    return False
                
                if data['severity'] not in ['low', 'medium', 'high', 'critical']:
                    self.log_test("Audio Analysis", False, f"Invalid severity level: {data['severity']}", data)
                    return False
                
                if data['urgency_level'] not in ['immediate', 'week', 'month', 'monitoring']:
                    self.log_test("Audio Analysis", False, f"Invalid urgency level: {data['urgency_level']}", data)
                    return False
                
                if not isinstance(data['recommendations'], list) or len(data['recommendations']) == 0:
                    self.log_test("Audio Analysis", False, "Recommendations should be a non-empty list", data)
                    return False
                
                self.log_test("Audio Analysis", True, f"Audio analysis successful - {data['component']}: {data['diagnosis']}", {
                    'component': data['component'],
                    'diagnosis': data['diagnosis'],
                    'confidence': data['confidence_score'],
                    'severity': data['severity'],
                    'recommendations_count': len(data['recommendations'])
                })
                return True
            else:
                self.log_test("Audio Analysis", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            # Clean up temp file on error
            if audio_file_path and os.path.exists(audio_file_path):
                os.unlink(audio_file_path)
            self.log_test("Audio Analysis", False, f"Request error: {str(e)}")
            return False
    
    def test_diagnostic_history(self):
        """Test diagnostic history retrieval"""
        try:
            response = self.session.get(f"{self.base_url}/diagnostics/history")
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_test("Diagnostic History", False, "Response should be a list", data)
                    return False
                
                # If there are diagnostics, verify structure
                if len(data) > 0:
                    first_diagnostic = data[0]
                    required_fields = ['id', 'audio_filename', 'component', 'diagnosis', 'confidence_score']
                    missing_fields = [field for field in required_fields if field not in first_diagnostic]
                    
                    if missing_fields:
                        self.log_test("Diagnostic History", False, f"Missing fields in diagnostic: {missing_fields}", first_diagnostic)
                        return False
                
                self.log_test("Diagnostic History", True, f"Retrieved {len(data)} diagnostic records", {
                    'count': len(data)
                })
                return True
            else:
                self.log_test("Diagnostic History", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Diagnostic History", False, f"Request error: {str(e)}")
            return False
    
    def test_vehicle_management(self):
        """Test vehicle creation and retrieval"""
        try:
            # Test vehicle creation
            vehicle_data = {
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "mileage": 45000
            }
            
            response = self.session.post(f"{self.base_url}/vehicle", json=vehicle_data)
            if response.status_code == 200:
                created_vehicle = response.json()
                
                # Verify created vehicle structure
                required_fields = ['id', 'make', 'model', 'year', 'mileage', 'created_at']
                missing_fields = [field for field in required_fields if field not in created_vehicle]
                
                if missing_fields:
                    self.log_test("Vehicle Creation", False, f"Missing fields: {missing_fields}", created_vehicle)
                    return False
                
                # Test vehicle retrieval
                response = self.session.get(f"{self.base_url}/vehicles")
                if response.status_code == 200:
                    vehicles = response.json()
                    
                    if not isinstance(vehicles, list):
                        self.log_test("Vehicle Retrieval", False, "Vehicles response should be a list", vehicles)
                        return False
                    
                    # Check if our created vehicle is in the list
                    created_id = created_vehicle['id']
                    found_vehicle = next((v for v in vehicles if v['id'] == created_id), None)
                    
                    if found_vehicle:
                        self.log_test("Vehicle Management", True, f"Vehicle created and retrieved successfully", {
                            'created_vehicle': f"{created_vehicle['year']} {created_vehicle['make']} {created_vehicle['model']}",
                            'total_vehicles': len(vehicles)
                        })
                        return True
                    else:
                        self.log_test("Vehicle Management", False, "Created vehicle not found in retrieval", vehicles)
                        return False
                else:
                    self.log_test("Vehicle Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                    return False
            else:
                self.log_test("Vehicle Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Vehicle Management", False, f"Request error: {str(e)}")
            return False
    
    def create_mp3_test_file(self):
        """Create a simple MP3-like test file for testing MP3 upload"""
        try:
            # Create a minimal MP3 header structure
            # This creates a basic MP3 file that should be recognizable by librosa
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            
            # Write a minimal MP3 header (ID3v2 + basic MP3 frame)
            # ID3v2 header
            temp_file.write(b'ID3\x03\x00\x00\x00\x00\x00\x00')
            
            # Add some basic MP3 frame data (simplified)
            # This is a very basic MP3 structure that librosa should be able to handle
            mp3_frame = b'\xff\xfb\x90\x00' + b'\x00' * 100  # Basic MP3 frame header + padding
            temp_file.write(mp3_frame * 50)  # Repeat to make it longer
            
            temp_file.close()
            return temp_file.name
        except Exception as e:
            self.log_test("MP3 File Creation", False, f"Failed to create test MP3: {str(e)}")
            return None

    def create_realistic_engine_audio(self, format_ext='.wav'):
        """Create realistic engine sound patterns for testing"""
        try:
            duration = 3.0  # seconds
            sample_rate = 44100
            
            # Create engine-like sound with multiple harmonics
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # Base engine frequency (around 100-200 Hz for idle)
            base_freq = 150
            audio_data = np.sin(2 * np.pi * base_freq * t) * 0.5
            
            # Add harmonics for realistic engine sound
            audio_data += np.sin(2 * np.pi * base_freq * 2 * t) * 0.3
            audio_data += np.sin(2 * np.pi * base_freq * 3 * t) * 0.2
            
            # Add engine roughness (irregular firing)
            roughness = np.sin(2 * np.pi * 25 * t) * 0.1
            audio_data = audio_data * (1 + roughness)
            
            # Add some mechanical noise
            noise = np.random.normal(0, 0.05, audio_data.shape)
            audio_data = audio_data + noise
            
            # Normalize
            audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
            
            if format_ext == '.wav':
                # Create WAV file
                audio_data_int = (audio_data * 32767).astype(np.int16)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                with wave.open(temp_file.name, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data_int.tobytes())
                return temp_file.name
            else:
                # For MP3, create a basic file structure
                return self.create_mp3_test_file()
                
        except Exception as e:
            self.log_test("Engine Audio Creation", False, f"Failed to create engine audio: {str(e)}")
            return None

    def test_mp3_upload_specific(self):
        """Test MP3 file upload specifically - the main focus of this testing"""
        print("\n🎵 TESTING MP3 UPLOAD FUNCTIONALITY (User Reported Issue)")
        print("-" * 50)
        
        mp3_file_path = self.create_mp3_test_file()
        if not mp3_file_path:
            return False
        
        try:
            with open(mp3_file_path, 'rb') as mp3_file:
                files = {'file': ('engine_sound.mp3', mp3_file, 'audio/mpeg')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            # Clean up temp file
            os.unlink(mp3_file_path)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("MP3 Upload", True, f"MP3 file processed successfully - {data['component']}: {data['diagnosis']}", {
                    'filename': data['audio_filename'],
                    'confidence': data['confidence_score'],
                    'severity': data['severity']
                })
                return True
            elif response.status_code == 400:
                error_msg = response.json().get('detail', response.text)
                if 'ffmpeg' in error_msg.lower() or 'mp3' in error_msg.lower():
                    self.log_test("MP3 Upload", False, f"MP3 processing failed - likely ffmpeg issue: {error_msg}")
                else:
                    self.log_test("MP3 Upload", False, f"MP3 upload rejected: {error_msg}")
                return False
            else:
                self.log_test("MP3 Upload", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            if mp3_file_path and os.path.exists(mp3_file_path):
                os.unlink(mp3_file_path)
            self.log_test("MP3 Upload", False, f"Request error: {str(e)}")
            return False

    def test_multiple_audio_formats(self):
        """Test various audio formats as mentioned in the review request"""
        print("\n🎼 TESTING MULTIPLE AUDIO FORMATS")
        print("-" * 40)
        
        formats_to_test = [
            ('.wav', 'audio/wav', 'WAV Format'),
            ('.mp3', 'audio/mpeg', 'MP3 Format'),
            ('.m4a', 'audio/mp4', 'M4A Format'),
            ('.ogg', 'audio/ogg', 'OGG Format'),
            ('.flac', 'audio/flac', 'FLAC Format')
        ]
        
        results = []
        for ext, mime_type, format_name in formats_to_test:
            try:
                if ext == '.wav':
                    audio_file_path = self.create_realistic_engine_audio('.wav')
                else:
                    # For non-WAV formats, create basic test files
                    audio_file_path = self.create_mp3_test_file()
                    if audio_file_path:
                        # Rename to correct extension
                        new_path = audio_file_path.replace('.mp3', ext)
                        os.rename(audio_file_path, new_path)
                        audio_file_path = new_path
                
                if not audio_file_path:
                    results.append((format_name, False, "File creation failed"))
                    continue
                
                with open(audio_file_path, 'rb') as audio_file:
                    files = {'file': (f'engine_sound{ext}', audio_file, mime_type)}
                    response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
                
                os.unlink(audio_file_path)
                
                if response.status_code == 200:
                    data = response.json()
                    results.append((format_name, True, f"Processed successfully - {data['component']}"))
                else:
                    error_msg = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                    results.append((format_name, False, f"HTTP {response.status_code}: {error_msg}"))
                    
            except Exception as e:
                if 'audio_file_path' in locals() and audio_file_path and os.path.exists(audio_file_path):
                    os.unlink(audio_file_path)
                results.append((format_name, False, f"Error: {str(e)}"))
        
        # Log results
        passed_formats = [r for r in results if r[1]]
        failed_formats = [r for r in results if not r[1]]
        
        self.log_test("Multiple Audio Formats", len(failed_formats) == 0, 
                     f"Tested {len(formats_to_test)} formats - {len(passed_formats)} passed, {len(failed_formats)} failed", 
                     {'results': results})
        
        return len(failed_formats) == 0

    def test_corrupted_audio_handling(self):
        """Test handling of corrupted audio files"""
        try:
            # Create a corrupted MP3 file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.write(b'This is not valid MP3 data at all, just random bytes')
            temp_file.write(b'\x00\x01\x02\x03\x04\x05' * 100)
            temp_file.close()
            
            with open(temp_file.name, 'rb') as corrupted_file:
                files = {'file': ('corrupted_engine.mp3', corrupted_file, 'audio/mpeg')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(temp_file.name)
            
            if response.status_code == 400:
                error_msg = response.json().get('detail', '')
                self.log_test("Corrupted Audio Handling", True, f"Correctly rejected corrupted file: {error_msg}")
                return True
            else:
                self.log_test("Corrupted Audio Handling", False, f"Should reject corrupted file, got HTTP {response.status_code}")
                return False
        except Exception as e:
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            self.log_test("Corrupted Audio Handling", False, f"Request error: {str(e)}")
            return False

    def test_empty_audio_file(self):
        """Test handling of empty audio files"""
        try:
            # Create an empty MP3 file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()  # Empty file
            
            with open(temp_file.name, 'rb') as empty_file:
                files = {'file': ('empty_engine.mp3', empty_file, 'audio/mpeg')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(temp_file.name)
            
            if response.status_code == 400:
                error_msg = response.json().get('detail', '')
                self.log_test("Empty Audio File", True, f"Correctly rejected empty file: {error_msg}")
                return True
            else:
                self.log_test("Empty Audio File", False, f"Should reject empty file, got HTTP {response.status_code}")
                return False
        except Exception as e:
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            self.log_test("Empty Audio File", False, f"Request error: {str(e)}")
            return False

    def test_large_audio_file(self):
        """Test handling of large audio files"""
        try:
            # Create a larger WAV file (about 10 seconds)
            duration = 10.0
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * 440 * t)
            audio_data = (audio_data * 32767).astype(np.int16)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            with wave.open(temp_file.name, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            file_size = os.path.getsize(temp_file.name)
            
            with open(temp_file.name, 'rb') as large_file:
                files = {'file': ('large_engine_sound.wav', large_file, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(temp_file.name)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Large Audio File", True, f"Large file processed successfully ({file_size} bytes) - {data['component']}", {
                    'file_size_bytes': file_size,
                    'diagnosis': data['diagnosis']
                })
                return True
            else:
                error_msg = response.json().get('detail', response.text) if response.status_code == 400 else response.text
                self.log_test("Large Audio File", False, f"Large file processing failed: {error_msg}")
                return False
        except Exception as e:
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            self.log_test("Large Audio File", False, f"Request error: {str(e)}")
            return False
        """Test audio upload with invalid format"""
        try:
            # Create a text file instead of audio
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
            temp_file.write(b"This is not an audio file")
            temp_file.close()
            
            with open(temp_file.name, 'rb') as fake_audio:
                files = {'file': ('fake_audio.txt', fake_audio, 'text/plain')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            # Clean up
            os.unlink(temp_file.name)
            
            if response.status_code == 400:
                self.log_test("Invalid Audio Format", True, "Correctly rejected invalid audio format")
                return True
            else:
                self.log_test("Invalid Audio Format", False, f"Should reject invalid format, got HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid Audio Format", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚗 Starting VehicleAI Whisperer Backend API Tests")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_health_check():
            print("\n❌ Basic connectivity failed. Stopping tests.")
            return False
        
        # Run all tests
        tests = [
            self.test_health_overview,
            self.test_audio_analysis,
            self.test_diagnostic_history,
            self.test_vehicle_management,
            self.test_invalid_audio_format
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.5)  # Small delay between tests
        
        print("\n" + "=" * 60)
        print(f"🏁 Test Results: {passed}/{total + 1} tests passed")  # +1 for health check
        
        if passed == total:
            print("✅ All backend APIs are working correctly!")
            return True
        else:
            print("❌ Some tests failed. Check the details above.")
            return False
    
    def get_test_summary(self):
        """Get summary of all test results"""
        return {
            'total_tests': len(self.test_results),
            'passed': len([r for r in self.test_results if r['success']]),
            'failed': len([r for r in self.test_results if not r['success']]),
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = VehicleAITester()
    success = tester.run_all_tests()
    
    # Print detailed summary
    summary = tester.get_test_summary()
    print(f"\n📊 Detailed Summary:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    
    if not success:
        print("\n❌ Failed Tests:")
        for result in summary['results']:
            if not result['success']:
                print(f"   - {result['test']}: {result['message']}")