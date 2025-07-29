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

class EniguityTester:
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
    
    def test_health_check(self):
        """Test basic API health check"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "Eniguity Diagnostics API" in data.get("message", ""):
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

    def create_mp3_test_file(self):
        """Create a proper MP3 test file using ffmpeg"""
        try:
            import subprocess
            
            # Create a temporary MP3 file using ffmpeg
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            
            # Generate a 3-second sine wave MP3 file using ffmpeg
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=150:duration=3',
                '-acodec', 'mp3', '-ar', '44100', temp_file.name, '-y'
            ]
            
            # Run ffmpeg with suppressed output
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return temp_file.name
            else:
                self.log_test("MP3 File Creation", False, f"ffmpeg failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.log_test("MP3 File Creation", False, f"Failed to create test MP3: {str(e)}")
            return None

    def create_realistic_engine_audio(self, format_ext='.wav'):
        """Create realistic engine sound patterns for testing"""
        try:
            if format_ext == '.wav':
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
                # For MP3 and other formats, use ffmpeg to create proper files
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

    def create_audio_file_by_format(self, format_ext):
        """Create proper audio files for different formats using ffmpeg"""
        try:
            import subprocess
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=format_ext)
            temp_file.close()
            
            if format_ext == '.wav':
                # Use our existing WAV creation method
                return self.create_realistic_engine_audio('.wav')
            else:
                # Use ffmpeg for other formats
                codec_map = {
                    '.mp3': 'mp3',
                    '.m4a': 'aac',
                    '.ogg': 'libvorbis',
                    '.flac': 'flac'
                }
                
                codec = codec_map.get(format_ext, 'mp3')
                
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=150:duration=3',
                    '-acodec', codec, '-ar', '44100', temp_file.name, '-y'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return temp_file.name
                else:
                    self.log_test(f"{format_ext.upper()} File Creation", False, f"ffmpeg failed: {result.stderr}")
                    return None
                    
        except Exception as e:
            self.log_test(f"{format_ext.upper()} File Creation", False, f"Failed to create {format_ext} file: {str(e)}")
            return None

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
                audio_file_path = self.create_audio_file_by_format(ext)
                
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
                
                self.log_test("Health Overview", True, "Health dashboard data structure is correct", {
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

    def run_mp3_focused_tests(self):
        """Run MP3-focused tests based on user's reported issue"""
        print("🚗 Starting Eniguity Backend API Tests - MP3 Focus")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_health_check():
            print("\n❌ Basic connectivity failed. Stopping tests.")
            return False
        
        # Run MP3-focused tests first (user reported issue)
        mp3_tests = [
            self.test_mp3_upload_specific,
            self.test_multiple_audio_formats,
            self.test_corrupted_audio_handling,
            self.test_empty_audio_file,
            self.test_large_audio_file
        ]
        
        # Run basic health test
        standard_tests = [
            self.test_health_overview
        ]
        
        all_tests = mp3_tests + standard_tests
        passed = 0
        total = len(all_tests)
        
        print("\n🎵 MP3 & AUDIO FORMAT TESTS (Priority)")
        print("-" * 40)
        for test in mp3_tests:
            if test():
                passed += 1
            time.sleep(0.5)
        
        print("\n🔧 BASIC API TESTS")
        print("-" * 20)
        for test in standard_tests:
            if test():
                passed += 1
            time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print(f"🏁 Test Results: {passed}/{total + 1} tests passed")  # +1 for health check
        
        if passed == total:
            print("✅ All backend APIs are working correctly!")
            print("🎵 MP3 upload functionality is working as expected!")
            return True
        else:
            print("❌ Some tests failed. Check the details above.")
            # Check specifically for MP3 issues
            mp3_failed = sum(1 for result in self.test_results if 'MP3' in result['test'] and not result['success'])
            if mp3_failed > 0:
                print(f"⚠️  {mp3_failed} MP3-related tests failed - this addresses the user's reported issue")
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
    tester = EniguityTester()
    success = tester.run_mp3_focused_tests()
    
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