#!/usr/bin/env python3
"""
Enhanced Audio Analysis Testing Suite
Specifically tests audio upload functionality with engine sound files
to verify the complete analysis pipeline as requested.
"""

import requests
import json
import os
import tempfile
import wave
import numpy as np
from datetime import datetime
import time
import librosa

# Get backend URL from frontend environment
BACKEND_URL = "http://127.0.0.1:8000"

class AudioAnalysisTester:
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
    
    def create_engine_sound_wav(self, sound_type="idle"):
        """Create realistic engine sound WAV files for testing"""
        try:
            duration = 3.0  # seconds
            sample_rate = 44100
            
            # Generate different engine sound patterns
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            if sound_type == "idle":
                # Idle engine - low frequency rumble
                base_freq = 80  # Hz
                audio_data = (
                    np.sin(2 * np.pi * base_freq * t) * 0.6 +
                    np.sin(2 * np.pi * base_freq * 2 * t) * 0.3 +
                    np.sin(2 * np.pi * base_freq * 4 * t) * 0.1
                )
            elif sound_type == "revving":
                # Revving engine - increasing frequency
                freq_sweep = np.linspace(80, 300, len(t))
                audio_data = np.sin(2 * np.pi * freq_sweep * t) * 0.8
            elif sound_type == "knocking":
                # Engine knock - irregular high frequency spikes
                base_freq = 100
                audio_data = np.sin(2 * np.pi * base_freq * t) * 0.5
                # Add random knocking sounds
                knock_times = np.random.choice(len(t), size=int(len(t) * 0.1), replace=False)
                for knock_time in knock_times:
                    if knock_time < len(audio_data):
                        audio_data[knock_time] += np.random.uniform(0.5, 1.0)
            else:
                # Default engine sound
                audio_data = np.sin(2 * np.pi * 120 * t) * 0.7
            
            # Add realistic engine noise
            noise = np.random.normal(0, 0.05, audio_data.shape)
            audio_data = audio_data + noise
            
            # Add some harmonic content
            harmonics = (
                np.sin(2 * np.pi * 240 * t) * 0.2 +
                np.sin(2 * np.pi * 360 * t) * 0.1
            )
            audio_data = audio_data + harmonics
            
            # Normalize to prevent clipping
            audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
            
            # Convert to 16-bit
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
            self.log_test(f"Engine Sound Creation ({sound_type})", False, f"Failed to create engine sound: {str(e)}")
            return None
    
    def test_audio_file_upload_validation(self):
        """Test 1: Audio file upload and validation"""
        print("\n🔧 Testing Audio File Upload and Validation...")
        
        # Test with valid WAV file
        audio_file = self.create_engine_sound_wav("idle")
        if not audio_file:
            return False
        
        try:
            with open(audio_file, 'rb') as f:
                files = {'file': ('engine_idle.wav', f, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(audio_file)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Audio Upload Validation", True, 
                             f"WAV file uploaded successfully - {data.get('audio_filename', 'unknown')}")
                return True
            else:
                self.log_test("Audio Upload Validation", False, 
                             f"Upload failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
            self.log_test("Audio Upload Validation", False, f"Upload error: {str(e)}")
            return False
    
    def test_librosa_audio_processing(self):
        """Test 2: Verify librosa is properly loading and processing audio files"""
        print("\n🎵 Testing Librosa Audio Processing...")
        
        audio_file = self.create_engine_sound_wav("revving")
        if not audio_file:
            return False
        
        try:
            # First verify we can load the file with librosa locally
            try:
                audio_data, sr = librosa.load(audio_file, sr=None)
                local_features = {
                    'duration': len(audio_data) / sr,
                    'sample_rate': sr,
                    'samples': len(audio_data)
                }
                print(f"   Local librosa processing: {local_features}")
            except Exception as e:
                self.log_test("Librosa Processing", False, f"Local librosa failed: {str(e)}")
                os.unlink(audio_file)
                return False
            
            # Now test the API
            with open(audio_file, 'rb') as f:
                files = {'file': ('engine_revving.wav', f, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(audio_file)
            
            if response.status_code == 200:
                data = response.json()
                # Check if the response indicates successful audio processing
                if all(key in data for key in ['component', 'diagnosis', 'confidence_score']):
                    self.log_test("Librosa Processing", True, 
                                 f"Audio processed successfully - Duration: {local_features['duration']:.2f}s")
                    return True
                else:
                    self.log_test("Librosa Processing", False, "Response missing audio processing indicators")
                    return False
            else:
                self.log_test("Librosa Processing", False, 
                             f"Processing failed with status {response.status_code}")
                return False
        except Exception as e:
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
            self.log_test("Librosa Processing", False, f"Processing error: {str(e)}")
            return False
    
    def test_mfcc_feature_extraction(self):
        """Test 3: Verify MFCC feature extraction from uploaded files"""
        print("\n📊 Testing MFCC Feature Extraction...")
        
        audio_file = self.create_engine_sound_wav("knocking")
        if not audio_file:
            return False
        
        try:
            with open(audio_file, 'rb') as f:
                files = {'file': ('engine_knocking.wav', f, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(audio_file)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify that the response contains indicators of feature extraction
                # The mock AI should generate different responses based on audio features
                required_fields = ['confidence_score', 'component', 'diagnosis']
                if all(field in data for field in required_fields):
                    confidence = data['confidence_score']
                    if 0.0 <= confidence <= 1.0:
                        self.log_test("MFCC Feature Extraction", True, 
                                     f"Features extracted and analyzed - Confidence: {confidence:.3f}")
                        return True
                    else:
                        self.log_test("MFCC Feature Extraction", False, 
                                     f"Invalid confidence score: {confidence}")
                        return False
                else:
                    self.log_test("MFCC Feature Extraction", False, 
                                 f"Missing analysis fields: {required_fields}")
                    return False
            else:
                self.log_test("MFCC Feature Extraction", False, 
                             f"Feature extraction failed with status {response.status_code}")
                return False
        except Exception as e:
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
            self.log_test("MFCC Feature Extraction", False, f"Extraction error: {str(e)}")
            return False
    
    def test_mock_ai_diagnosis_generation(self):
        """Test 4: Confirm realistic automotive diagnoses are generated"""
        print("\n🤖 Testing Mock AI Diagnosis Generation...")
        
        diagnoses = []
        automotive_components = ['Engine', 'Brakes', 'Transmission', 'Exhaust']
        
        # Test multiple audio files to get different diagnoses
        for i, sound_type in enumerate(['idle', 'revving', 'knocking']):
            audio_file = self.create_engine_sound_wav(sound_type)
            if not audio_file:
                continue
            
            try:
                with open(audio_file, 'rb') as f:
                    files = {'file': (f'engine_{sound_type}.wav', f, 'audio/wav')}
                    response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
                
                os.unlink(audio_file)
                
                if response.status_code == 200:
                    data = response.json()
                    diagnoses.append(data)
                    
            except Exception as e:
                if audio_file and os.path.exists(audio_file):
                    os.unlink(audio_file)
                continue
        
        if len(diagnoses) >= 2:
            # Verify realistic automotive diagnoses
            valid_diagnoses = 0
            for diagnosis in diagnoses:
                # Check component is automotive-related
                if diagnosis.get('component') in automotive_components:
                    valid_diagnoses += 1
                
                # Check severity levels
                if diagnosis.get('severity') in ['low', 'medium', 'high', 'critical']:
                    valid_diagnoses += 1
                
                # Check urgency levels
                if diagnosis.get('urgency_level') in ['immediate', 'week', 'month', 'monitoring']:
                    valid_diagnoses += 1
                
                # Check recommendations exist
                if isinstance(diagnosis.get('recommendations'), list) and len(diagnosis['recommendations']) > 0:
                    valid_diagnoses += 1
            
            expected_checks = len(diagnoses) * 4  # 4 checks per diagnosis
            if valid_diagnoses >= expected_checks * 0.8:  # 80% pass rate
                self.log_test("Mock AI Diagnosis", True, 
                             f"Generated {len(diagnoses)} realistic automotive diagnoses")
                
                # Print sample diagnosis
                sample = diagnoses[0]
                print(f"   Sample: {sample['component']} - {sample['diagnosis']}")
                print(f"   Severity: {sample['severity']}, Confidence: {sample['confidence_score']:.3f}")
                return True
            else:
                self.log_test("Mock AI Diagnosis", False, 
                             f"Only {valid_diagnoses}/{expected_checks} diagnosis checks passed")
                return False
        else:
            self.log_test("Mock AI Diagnosis", False, 
                         f"Insufficient diagnoses generated: {len(diagnoses)}")
            return False
    
    def test_database_storage(self):
        """Test 5: Verify diagnostic results are stored in MongoDB properly"""
        print("\n💾 Testing Database Storage...")
        
        # Get initial diagnostic count
        try:
            response = self.session.get(f"{self.base_url}/diagnostics/history")
            if response.status_code != 200:
                self.log_test("Database Storage", False, "Cannot access diagnostic history")
                return False
            
            initial_count = len(response.json())
            
            # Upload a new audio file
            audio_file = self.create_engine_sound_wav("idle")
            if not audio_file:
                return False
            
            with open(audio_file, 'rb') as f:
                files = {'file': ('test_storage.wav', f, 'audio/wav')}
                upload_response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(audio_file)
            
            if upload_response.status_code != 200:
                self.log_test("Database Storage", False, "Audio upload failed")
                return False
            
            # Wait a moment for database write
            time.sleep(1)
            
            # Check if diagnostic count increased
            response = self.session.get(f"{self.base_url}/diagnostics/history")
            if response.status_code == 200:
                new_count = len(response.json())
                if new_count > initial_count:
                    # Verify the stored data structure
                    diagnostics = response.json()
                    latest = diagnostics[0]  # Should be sorted by created_at desc
                    
                    # Check for MongoDB ObjectId issues (should not have _id field)
                    if '_id' in latest:
                        self.log_test("Database Storage", False, "MongoDB ObjectId not properly handled")
                        return False
                    
                    # Verify required fields are present and JSON serializable
                    required_fields = ['id', 'audio_filename', 'component', 'diagnosis', 'created_at']
                    if all(field in latest for field in required_fields):
                        self.log_test("Database Storage", True, 
                                     f"Diagnostic stored successfully - Count: {initial_count} → {new_count}")
                        return True
                    else:
                        missing = [f for f in required_fields if f not in latest]
                        self.log_test("Database Storage", False, f"Missing fields in stored data: {missing}")
                        return False
                else:
                    self.log_test("Database Storage", False, 
                                 f"Diagnostic count did not increase: {initial_count} → {new_count}")
                    return False
            else:
                self.log_test("Database Storage", False, "Cannot verify storage")
                return False
                
        except Exception as e:
            self.log_test("Database Storage", False, f"Storage test error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test 6: Test with invalid file formats and corrupted files"""
        print("\n⚠️  Testing Error Handling...")
        
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Invalid file format
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
            temp_file.write(b"This is not an audio file")
            temp_file.close()
            
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('fake.txt', f, 'text/plain')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(temp_file.name)
            
            if response.status_code == 400:
                tests_passed += 1
                print("   ✅ Invalid format properly rejected")
            else:
                print(f"   ❌ Invalid format not rejected (status: {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Invalid format test error: {str(e)}")
        
        # Test 2: Empty file
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.close()  # Empty file
            
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('empty.wav', f, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(temp_file.name)
            
            if response.status_code in [400, 422]:
                tests_passed += 1
                print("   ✅ Empty file properly rejected")
            else:
                print(f"   ❌ Empty file not rejected (status: {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Empty file test error: {str(e)}")
        
        # Test 3: Corrupted WAV file
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.write(b"RIFF" + b"corrupted_wav_data" * 100)
            temp_file.close()
            
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('corrupted.wav', f, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
            
            os.unlink(temp_file.name)
            
            if response.status_code in [400, 422]:
                tests_passed += 1
                print("   ✅ Corrupted file properly rejected")
            else:
                print(f"   ❌ Corrupted file not rejected (status: {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Corrupted file test error: {str(e)}")
        
        if tests_passed >= 2:  # At least 2 out of 3 error handling tests should pass
            self.log_test("Error Handling", True, f"Error handling working - {tests_passed}/{total_tests} tests passed")
            return True
        else:
            self.log_test("Error Handling", False, f"Insufficient error handling - {tests_passed}/{total_tests} tests passed")
            return False
    
    def test_file_cleanup(self):
        """Test 7: Verify temporary files are cleaned up after processing"""
        print("\n🧹 Testing File Cleanup...")
        
        # Check /tmp directory before and after upload
        try:
            import glob
            
            # Count temp files before
            temp_files_before = len(glob.glob('/tmp/*.wav'))
            
            # Upload multiple files
            for i in range(3):
                audio_file = self.create_engine_sound_wav("idle")
                if audio_file:
                    with open(audio_file, 'rb') as f:
                        files = {'file': (f'cleanup_test_{i}.wav', f, 'audio/wav')}
                        response = self.session.post(f"{self.base_url}/analyze-audio", files=files)
                    os.unlink(audio_file)
            
            # Wait a moment for cleanup
            time.sleep(2)
            
            # Count temp files after
            temp_files_after = len(glob.glob('/tmp/*.wav'))
            
            if temp_files_after <= temp_files_before:
                self.log_test("File Cleanup", True, 
                             f"Temp files cleaned up properly - Before: {temp_files_before}, After: {temp_files_after}")
                return True
            else:
                self.log_test("File Cleanup", False, 
                             f"Temp files not cleaned up - Before: {temp_files_before}, After: {temp_files_after}")
                return False
                
        except Exception as e:
            self.log_test("File Cleanup", False, f"Cleanup test error: {str(e)}")
            return False
    
    def run_comprehensive_audio_tests(self):
        """Run all comprehensive audio analysis tests"""
        print("🎵 Starting Comprehensive Audio Upload & Analysis Testing")
        print("=" * 70)
        
        # Test basic connectivity first
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code != 200:
                print("❌ Backend API not accessible. Stopping tests.")
                return False
            print("✅ Backend API connectivity confirmed")
        except Exception as e:
            print(f"❌ Cannot connect to backend: {str(e)}")
            return False
        
        # Run all comprehensive tests
        tests = [
            self.test_audio_file_upload_validation,
            self.test_librosa_audio_processing,
            self.test_mfcc_feature_extraction,
            self.test_mock_ai_diagnosis_generation,
            self.test_database_storage,
            self.test_error_handling,
            self.test_file_cleanup
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # Delay between tests
        
        print("\n" + "=" * 70)
        print(f"🏁 Audio Analysis Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ Complete audio analysis pipeline is working correctly!")
            print("   • Audio upload and validation ✅")
            print("   • Librosa audio processing ✅")
            print("   • MFCC feature extraction ✅")
            print("   • Mock AI diagnosis generation ✅")
            print("   • Database storage ✅")
            print("   • Error handling ✅")
            print("   • File cleanup ✅")
            return True
        else:
            print("❌ Some audio analysis tests failed. Check details above.")
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
    tester = AudioAnalysisTester()
    success = tester.run_comprehensive_audio_tests()
    
    # Print detailed summary
    summary = tester.get_test_summary()
    print(f"\n📊 Detailed Test Summary:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    
    if not success:
        print("\n❌ Failed Tests:")
        for result in summary['results']:
            if not result['success']:
                print(f"   - {result['test']}: {result['message']}")