"""
Competency Assessment and Calibration Engine - Core Schemas
Project: ScholarSync (J26-IT-411)
Lead / Author: Senarath S A M S (IT23284784)

Domain-Agnostic data contracts adhering strictly to the SLIIT proposal data dictionary:
- Supports arbitrary subjects, concepts, and assessment modalities.
- Maps to Bloom's Revised Taxonomy (Remember, Understand, Apply, Analyse).
- Captures observable behavioral context (attempts, duration, hint usage, error types).
- Calculates probability calibration and metacognitive calibration gap (Confidence vs. Actual Mastery).
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CognitiveLevel(str, Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYSE = "ANALYSE"


class QuestionType(str, Enum):
    MCQ = "MCQ"
    SHORT_ANSWER = "SHORT_ANSWER"
    CODE_OUTPUT = "CODE_OUTPUT"
    DEBUGGING = "DEBUGGING"
    CODING = "CODING"


class GapStatus(str, Enum):
    MASTERED = "MASTERED"
    DEVELOPING = "DEVELOPING"
    FOUNDATIONAL_GAP = "FOUNDATIONAL_GAP"
    APPLICATION_GAP = "APPLICATION_GAP"
    ANALYTICAL_GAP = "ANALYTICAL_GAP"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class MetacognitiveStatus(str, Enum):
    WELL_CALIBRATED = "WELL_CALIBRATED"
    OVERCONFIDENT = "OVERCONFIDENT"          # Illusion of Competence
    UNDERCONFIDENT = "UNDERCONFIDENT"        # Imposter Phenomenon
    UNCERTAIN = "UNCERTAIN"


# -------------------------------------------------------------
# 1. Incoming Assessment Interaction Event
# -------------------------------------------------------------
class AssessmentInteractionEvent(BaseModel):
    learner_id: str = Field(..., description="Unique pseudonymous student identifier")
    subject_id: str = Field(default="JAVA_FUNDAMENTALS", description="Subject / Domain Identifier")
    concept_id: str = Field(..., description="Target concept node (e.g., LOOPS, ARRAYS, METHODS)")
    bloom_level: CognitiveLevel = Field(..., description="Bloom's Taxonomy Cognitive Level")
    item_id: str = Field(..., description="Identifier of the question or assessment item")
    question_type: QuestionType = Field(default=QuestionType.MCQ, description="Modality of question")
    
    # Performance evidence
    is_correct: bool = Field(..., description="Binary correctness (0 or 1)")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score [0.0 - 1.0]")
    
    # Behavioral context (observable telemetry)
    duration_seconds: float = Field(..., ge=0.0, description="Time spent on the item")
    attempt_count: int = Field(default=1, ge=1, description="Number of attempts submitted")
    hints_requested: int = Field(default=0, ge=0, description="Number of hints requested")
    error_category: Optional[str] = Field(default=None, description="Syntax, Runtime, Logic, or None")
    
    # Metacognitive rating
    confidence_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Self-reported confidence (1-5)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event generation timestamp")


# -------------------------------------------------------------
# 2. Concept-Bloom Level Competency Assessment State
# -------------------------------------------------------------
class ConceptCompetencyState(BaseModel):
    concept_id: str
    bloom_level: CognitiveLevel
    evidence_count: int = Field(0, description="Total valid interactions recorded for this node")
    
    # Model probabilities
    score_baseline_probability: float = Field(0.0, description="Score-only rolling average baseline")
    bkt_mastery_probability: float = Field(0.0, description="pyBKT hidden mastery state probability")
    calibrated_mastery_probability: float = Field(0.0, description="Calibrated behaviour-informed mastery estimate [0.0-1.0]")
    
    # Uncertainty & Evidence sufficiency
    is_sufficient_evidence: bool = Field(False, description="True if evidence_count >= threshold (default 3)")
    uncertainty_score: float = Field(1.0, description="Estimation uncertainty [0.0 - 1.0]")
    
    # Metacognition
    reported_confidence_avg: Optional[float] = Field(None, description="Average self-reported confidence normalized [0.0-1.0]")
    metacognitive_gap: Optional[float] = Field(None, description="Confidence - Calibrated Mastery")
    metacognitive_status: MetacognitiveStatus = Field(default=MetacognitiveStatus.UNCERTAIN)
    
    # Categorical Diagnosis
    gap_status: GapStatus = Field(default=GapStatus.INSUFFICIENT_EVIDENCE)
    recent_trend: str = Field(default="STABLE", description="IMPROVING, DECLINING, or STABLE")


# -------------------------------------------------------------
# 3. Complete Published Learner Profile (Downstream Contract)
# -------------------------------------------------------------
class LearnerCompetencyProfile(BaseModel):
    learner_id: str
    subject_id: str
    overall_mastery_index: float = Field(0.0, ge=0.0, le=1.0)
    total_assessments_completed: int = 0
    engine_model_version: str = Field("v1.0.0-calibrated-bkt-hybrid")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Competency breakdown per Concept and Cognitive Tier
    concept_states: List[ConceptCompetencyState] = Field(default_factory=list)
    identified_knowledge_gaps: List[str] = Field(default_factory=list, description="List of concepts flagged with critical gaps")
    metacognitive_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Alerts for overconfident or struggling patterns")
