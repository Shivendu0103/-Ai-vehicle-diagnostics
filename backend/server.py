from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import aiofiles
import librosa
import numpy as np
import random
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Eniguity Diagnostics API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class VehicleInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    make: str
    model: str
    year: int
    mileage: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DiagnosticResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: Optional[str] = None
    audio_filename: str
    component: str
    diagnosis: str
    confidence_score: float
    severity: str  # low, medium, high, critical
    recommendations: List[str]
    estimated_cost: Optional[float] = None
    urgency_level: str  # immediate, week, month, monitoring
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HealthScore(BaseModel):
    overall_score: int
    engine_health: int
    brake_health: int
    transmission_health: int
    exhaust_health: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Mock AI Analysis Functions
def extract_audio_features(audio_data, sr):
    """Extract MFCC and other audio features"""
    try:
        # Extract MFCC features
        mfcc = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        
        # Extract spectral features
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sr))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sr))
        
        # Zero crossing rate
        zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data))
        
        return {
            'mfcc_features': mfcc_mean.tolist(),
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'zero_crossing_rate': zcr,
            'duration': len(audio_data) / sr
        }
    except Exception as e:
        logging.error(f"Feature extraction error: {e}")
        return None

def generate_mock_diagnosis(features):
    """Generate realistic mock automotive diagnosis based on audio features"""
    
    diagnoses_db = [
        {
            'component': 'Engine',
            'diagnosis': 'Timing Belt Wear Detected',
            'confidence': random.uniform(0.75, 0.95),
            'severity': 'high',
            'recommendations': [
                'Schedule timing belt replacement within 2 weeks',
                'Check water pump condition during replacement',
                'Inspect tensioner and idler pulleys'
            ],
            'estimated_cost': random.uniform(800, 1200),
            'urgency': 'week'
        },
        {
            'component': 'Engine',
            'diagnosis': 'Healthy Engine Operation',
            'confidence': random.uniform(0.85, 0.98),
            'severity': 'low',
            'recommendations': [
                'Continue regular maintenance schedule',
                'Monitor oil levels monthly',
                'Next service in 3 months'
            ],
            'estimated_cost': 0,
            'urgency': 'monitoring'
        },
        {
            'component': 'Brakes',
            'diagnosis': 'Brake Pad Wear - Front Axle',
            'confidence': random.uniform(0.80, 0.94),
            'severity': 'medium',
            'recommendations': [
                'Replace brake pads within 1 month',
                'Inspect brake rotors for scoring',
                'Check brake fluid level'
            ],
            'estimated_cost': random.uniform(300, 500),
            'urgency': 'month'
        },
        {
            'component': 'Engine',
            'diagnosis': 'Bearing Wear - Connecting Rod',
            'confidence': random.uniform(0.70, 0.88),
            'severity': 'critical',
            'recommendations': [
                'IMMEDIATE ENGINE SHUTDOWN RECOMMENDED',
                'Tow to certified mechanic',
                'Complete engine inspection required'
            ],
            'estimated_cost': random.uniform(2000, 4000),
            'urgency': 'immediate'
        },
        {
            'component': 'Exhaust',
            'diagnosis': 'Exhaust Leak - Mid-Pipe Section',
            'confidence': random.uniform(0.65, 0.82),
            'severity': 'medium',
            'recommendations': [
                'Repair exhaust leak within 2 weeks',
                'Check emissions compliance',
                'Inspect catalytic converter'
            ],
            'estimated_cost': random.uniform(200, 400),
            'urgency': 'week'
        }
    ]
    
    # Simulate intelligent selection based on features
    if features and features.get('spectral_centroid', 0) > 2000:
        # High frequency suggests brake squeal
        return [d for d in diagnoses_db if d['component'] == 'Brakes'][0]
    elif features and features.get('zero_crossing_rate', 0) > 0.1:
        # High ZCR might suggest engine issues
        return random.choice([d for d in diagnoses_db if d['component'] == 'Engine'])
    else:
        return random.choice(diagnoses_db)

def generate_health_scores():
    """Generate realistic vehicle health scores"""
    return HealthScore(
        overall_score=random.randint(65, 95),
        engine_health=random.randint(70, 98),
        brake_health=random.randint(60, 90),
        transmission_health=random.randint(75, 95),
        exhaust_health=random.randint(65, 88)
    )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Eniguity Diagnostics API v1.0"}

@api_router.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    """Analyze uploaded audio file for vehicle diagnostics"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg')):
            raise HTTPException(status_code=400, detail="Unsupported audio format. Please upload WAV, MP3, M4A, or OGG files.")
        
        # Read and process audio file
        contents = await file.read()
        
        # Save temporarily for processing
        temp_path = f"/tmp/{uuid.uuid4()}.wav"
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(contents)
        
        try:
            # Load audio with librosa
            audio_data, sample_rate = librosa.load(temp_path, sr=None)
            
            # Extract features
            features = extract_audio_features(audio_data, sample_rate)
            
            # Generate mock diagnosis
            diagnosis_data = generate_mock_diagnosis(features)
            
            # Create diagnostic result
            result = DiagnosticResult(
                audio_filename=file.filename,
                component=diagnosis_data['component'],
                diagnosis=diagnosis_data['diagnosis'],
                confidence_score=diagnosis_data['confidence'],
                severity=diagnosis_data['severity'],
                recommendations=diagnosis_data['recommendations'],
                estimated_cost=diagnosis_data['estimated_cost'],
                urgency_level=diagnosis_data['urgency']
            )
            
            # Store in database
            result_dict = result.dict()
            await db.diagnostic_results.insert_one(result_dict)
            
            # Clean up temp file
            os.remove(temp_path)
            
            return result
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=400, detail=f"Audio processing failed. Please ensure you uploaded a valid audio file: {str(e)}")
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.get("/health-overview")
async def get_health_overview():
    """Get overall vehicle health dashboard data"""
    health_scores = generate_health_scores()
    
    # Get recent diagnostics
    recent_diagnostics = await db.diagnostic_results.find().sort("created_at", -1).limit(5).to_list(5)
    # Clean up MongoDB ObjectIds
    for diagnostic in recent_diagnostics:
        if '_id' in diagnostic:
            del diagnostic['_id']
    
    # Generate alerts based on health scores
    alerts = []
    if health_scores.brake_health < 70:
        alerts.append({
            'type': 'warning',
            'message': 'Brake system requires attention',
            'severity': 'medium'
        })
    if health_scores.engine_health < 75:
        alerts.append({
            'type': 'error',
            'message': 'Engine diagnostics show concerns',
            'severity': 'high'
        })
    
    return {
        'health_scores': health_scores,
        'recent_diagnostics': recent_diagnostics,
        'alerts': alerts,
        'total_diagnostics': await db.diagnostic_results.count_documents({})
    }

@api_router.get("/diagnostics/history")
async def get_diagnostic_history():
    """Get diagnostic history"""
    diagnostics = await db.diagnostic_results.find().sort("created_at", -1).limit(20).to_list(20)
    # Convert MongoDB documents to JSON-serializable format
    for diagnostic in diagnostics:
        if '_id' in diagnostic:
            del diagnostic['_id']  # Remove MongoDB ObjectId
    return diagnostics

@api_router.post("/vehicle", response_model=VehicleInfo)
async def create_vehicle(vehicle_data: dict):
    """Create new vehicle profile"""
    vehicle = VehicleInfo(**vehicle_data)
    await db.vehicles.insert_one(vehicle.dict())
    return vehicle

@api_router.get("/vehicles", response_model=List[VehicleInfo])
async def get_vehicles():
    """Get all vehicles"""
    vehicles = await db.vehicles.find().to_list(100)
    # Clean up MongoDB ObjectIds
    for vehicle in vehicles:
        if '_id' in vehicle:
            del vehicle['_id']
    return [VehicleInfo(**vehicle) for vehicle in vehicles]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()