"""
ScholarSync Competency Assessment & Calibration Engine - REST API Service
Exposes endpoints for:
1. Ingesting student interaction events from any assessment sandbox or quiz module.
2. Generating and querying real-time Calibrated Learner Profiles.
3. Detecting Metacognitive Gaps (Illusion of Competence vs. Imposter Phenomenon).
4. Providing interactive OpenAPI (Swagger) documentation at /docs for supervisors.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.competency_engine.schemas import (
        AssessmentInteractionEvent,
        LearnerCompetencyProfile,
        ConceptCompetencyState,
        GapStatus,
        MetacognitiveStatus,
        CognitiveLevel
    )
    from backend.competency_engine.bkt_model import BayesianKnowledgeTracer
except ModuleNotFoundError:
    from schemas import (
        AssessmentInteractionEvent,
        LearnerCompetencyProfile,
        ConceptCompetencyState,
        GapStatus,
        MetacognitiveStatus,
        CognitiveLevel
    )
    from bkt_model import BayesianKnowledgeTracer

app = FastAPI(
    title="ScholarSync Competency & Calibration Engine API",
    description="Domain-agnostic service for Bloom-aware competency estimation, BKT mastery tracing, and metacognitive calibration.",
    version="1.0.0"
)

# Enable CORS for Next.js frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory interaction buffer & profile cache for live testing
INTERACTION_STORE: List[Dict] = []
PROFILE_CACHE: Dict[str, LearnerCompetencyProfile] = {}

# Load trained models
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(CURRENT_DIR, "models")

try:
    calibrated_clf = joblib.load(os.path.join(MODEL_DIR, "calibrated_classifier.joblib"))
    bkt_tracer: BayesianKnowledgeTracer = joblib.load(os.path.join(MODEL_DIR, "bkt_tracer.joblib"))
    print("[API] Successfully loaded ML checkpoints.")
except Exception as e:
    print(f"[API Warning] Checkpoint load failed: {e}. Engine will initialize with defaults.")
    calibrated_clf = None
    bkt_tracer = BayesianKnowledgeTracer()


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "ScholarSync Competency Calibration Engine",
        "model_version": "v1.0.0-bkt-calibrated",
        "total_interactions_logged": len(INTERACTION_STORE)
    }


@app.post("/api/v1/assessment/event", status_code=status.HTTP_201_CREATED, tags=["Events"])
def log_interaction_event(event: AssessmentInteractionEvent):
    """
    Ingests an assessment event from any subject interface (Java, Python, Web, or Theory Quiz).
    """
    event_dict = event.dict()
    INTERACTION_STORE.append(event_dict)
    
    # Invalidate cached profile to trigger re-computation
    if event.learner_id in PROFILE_CACHE:
        del PROFILE_CACHE[event.learner_id]
        
    return {
        "message": "Interaction event ingested successfully",
        "learner_id": event.learner_id,
        "concept_id": event.concept_id,
        "recorded_at": event.timestamp.isoformat()
    }


@app.get("/api/v1/profile/{learner_id}", response_model=LearnerCompetencyProfile, tags=["Profiles"])
def get_learner_profile(learner_id: str, subject_id: Optional[str] = None):
    """
    Generates and returns the full Bloom-aware, calibrated learner competency profile.
    Downstream adaptive modules (e.g. planner, recommender) consume this contract.
    """
    # Fetch student events from memory
    user_events = [e for e in INTERACTION_STORE if e["learner_id"] == learner_id]
    
    if not user_events:
        # Check if learner exists in benchmark data
        data_path = os.path.join(CURRENT_DIR, "data", "benchmark_interactions_full.csv")
        if os.path.exists(data_path):
            df_full = pd.read_csv(data_path)
            matched = df_full[df_full["learner_id"] == learner_id]
            if not matched.empty:
                user_events = matched.to_dict(orient="records")
    
    if not user_events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No interaction evidence recorded for learner ID '{learner_id}'"
        )
        
    df_user = pd.DataFrame(user_events)
    concept_states = []
    knowledge_gaps = []
    metacognitive_alerts = []
    total_mastery_sum = 0.0

    # Group by Concept and Bloom Level
    for (concept, bloom), group in df_user.groupby(["concept_id", "bloom_level"]):
        evidence_count = len(group)
        correct_count = group["is_correct"].sum()
        score_baseline = float(correct_count / evidence_count)
        
        # 1. BKT sequential mastery
        responses = group["is_correct"].astype(int).tolist()
        bkt_posteriors = bkt_tracer.predict_sequence(responses, skill=concept)
        current_bkt_prob = float(bkt_posteriors[-1]) if bkt_posteriors else 0.5
        
        # 2. Observable Behaviour Supervised Prediction
        avg_duration = group["duration_seconds"].mean()
        avg_attempts = group["attempt_count"].mean()
        avg_hints = group["hints_requested"].mean()
        bloom_level_val = {"REMEMBER": 1, "UNDERSTAND": 2, "APPLY": 3, "ANALYSE": 4}.get(bloom, 1)
        
        feature_vector = np.array([[
            score_baseline,
            np.log1p(avg_duration),
            avg_attempts,
            avg_hints,
            bloom_level_val
        ]])
        
        if calibrated_clf is not None:
            calibrated_prob = float(calibrated_clf.predict_proba(feature_vector)[0, 1])
        else:
            calibrated_prob = current_bkt_prob

        # 3. Metacognitive Calibration Analysis
        conf_series = group["confidence_rating"].dropna()
        if not conf_series.empty:
            # Normalize confidence rating 1-5 to 0.0-1.0
            avg_conf_norm = float((conf_series.mean() - 1.0) / 4.0)
            meta_gap = round(avg_conf_norm - calibrated_prob, 3)
            
            if meta_gap > 0.25:
                meta_status = MetacognitiveStatus.OVERCONFIDENT
                metacognitive_alerts.append({
                    "concept": concept,
                    "bloom_level": bloom,
                    "type": "ILLUSION_OF_COMPETENCE",
                    "detail": f"Student reports high confidence ({round(avg_conf_norm*100)}%) but demonstrates only {round(calibrated_prob*100)}% mastery."
                })
            elif meta_gap < -0.25:
                meta_status = MetacognitiveStatus.UNDERCONFIDENT
                metacognitive_alerts.append({
                    "concept": concept,
                    "bloom_level": bloom,
                    "type": "IMPOSTER_PHENOMENON",
                    "detail": f"Student exhibits high mastery ({round(calibrated_prob*100)}%) despite reporting low confidence ({round(avg_conf_norm*100)}%)."
                })
            else:
                meta_status = MetacognitiveStatus.WELL_CALIBRATED
        else:
            avg_conf_norm = None
            meta_gap = None
            meta_status = MetacognitiveStatus.UNCERTAIN

        # 4. Gap Diagnosis
        is_sufficient = evidence_count >= 3
        uncertainty = round(1.0 / (1.0 + np.log1p(evidence_count)), 3)
        
        if not is_sufficient:
            gap_status = GapStatus.INSUFFICIENT_EVIDENCE
        elif calibrated_prob >= 0.75:
            gap_status = GapStatus.MASTERED
        elif calibrated_prob >= 0.50:
            gap_status = GapStatus.DEVELOPING
        else:
            if bloom in ["REMEMBER", "UNDERSTAND"]:
                gap_status = GapStatus.FOUNDATIONAL_GAP
            elif bloom == "APPLY":
                gap_status = GapStatus.APPLICATION_GAP
            else:
                gap_status = GapStatus.ANALYTICAL_GAP
            knowledge_gaps.append(f"{concept} ({bloom})")

        concept_states.append(ConceptCompetencyState(
            concept_id=concept,
            bloom_level=CognitiveLevel(bloom),
            evidence_count=evidence_count,
            score_baseline_probability=round(score_baseline, 3),
            bkt_mastery_probability=round(current_bkt_prob, 3),
            calibrated_mastery_probability=round(calibrated_prob, 3),
            is_sufficient_evidence=is_sufficient,
            uncertainty_score=uncertainty,
            reported_confidence_avg=round(avg_conf_norm, 3) if avg_conf_norm is not None else None,
            metacognitive_gap=meta_gap,
            metacognitive_status=meta_status,
            gap_status=gap_status,
            recent_trend="IMPROVING" if calibrated_prob >= score_baseline else "DECLINING"
        ))
        total_mastery_sum += calibrated_prob

    overall_index = round(total_mastery_sum / len(concept_states), 3) if concept_states else 0.0

    profile = LearnerCompetencyProfile(
        learner_id=learner_id,
        subject_id=subject_id if subject_id else df_user["subject_id"].iloc[0],
        overall_mastery_index=overall_index,
        total_assessments_completed=len(df_user),
        engine_model_version="v1.0.0-calibrated-bkt-hybrid",
        last_updated=datetime.utcnow(),
        concept_states=concept_states,
        identified_knowledge_gaps=list(set(knowledge_gaps)),
        metacognitive_alerts=metacognitive_alerts
    )
    
    PROFILE_CACHE[learner_id] = profile
    return profile
