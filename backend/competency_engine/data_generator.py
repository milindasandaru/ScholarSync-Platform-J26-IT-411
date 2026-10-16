"""
Synthetic and Benchmark Interaction Dataset Generator
Generates realistic educational interaction event logs adhering to the ScholarSync Competency Engine Schema.
Includes:
- Multiple learners with diverse latent abilities (High, Medium, Low/Struggling, Overconfident).
- Multiple concept topics with Bloom cognitive levels.
- Realistic observable behavioral signals (duration, attempt counts, hints, and confidence ratings).
- Learner-level train/test separation to guarantee zero data-leakage during evaluation.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, List, Dict

# Standard concepts for our benchmark (e.g. Java Fundamentals)
DEFAULT_CONCEPTS = [
    "VARIABLES_DATA_TYPES",
    "OPERATORS_EXPRESSIONS",
    "CONTROL_FLOW_CONDITIONALS",
    "LOOPS_ITERATION",
    "METHODS_FUNCTIONS",
    "ARRAYS_COLLECTIONS",
    "OBJECT_ORIENTED_BASICS"
]

BLOOM_LEVELS = ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYSE"]
QUESTION_TYPES = ["MCQ", "SHORT_ANSWER", "CODE_OUTPUT", "DEBUGGING", "CODING"]


def generate_benchmark_events(
    num_learners: int = 120,
    interactions_per_learner: int = 40,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic student interaction event log for benchmarking.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    events = []
    base_time = datetime(2026, 9, 1, 9, 0, 0)
    
    # 4 distinct learner persona types:
    # 1. Mastered/High: High skill, realistic confidence, low attempts, few hints.
    # 2. Average/Developing: Moderate skill, moderate duration, occasional hints.
    # 3. Struggling: Low skill, high duration, multiple attempts, frequent hints.
    # 4. Overconfident ("Illusion of Competence"): Low/moderate skill but high self-confidence.
    
    persona_distribution = ["HIGH"] * 30 + ["DEVELOPING"] * 45 + ["STRUGGLING"] * 30 + ["OVERCONFIDENT"] * 15
    random.shuffle(persona_distribution)
    
    for idx in range(num_learners):
        learner_id = f"STU_{idx+1:04d}"
        persona = persona_distribution[idx % len(persona_distribution)]
        
        # Latent true mastery ability per learner
        if persona == "HIGH":
            base_ability = random.uniform(0.75, 0.95)
        elif persona == "DEVELOPING":
            base_ability = random.uniform(0.50, 0.74)
        elif persona == "STRUGGLING":
            base_ability = random.uniform(0.20, 0.45)
        else: # OVERCONFIDENT
            base_ability = random.uniform(0.30, 0.50)
            
        cur_time = base_time + timedelta(hours=random.randint(0, 100))
        
        for step in range(interactions_per_learner):
            cur_time += timedelta(minutes=random.randint(3, 20))
            concept = random.choice(DEFAULT_CONCEPTS)
            bloom = random.choice(BLOOM_LEVELS)
            q_type = random.choice(QUESTION_TYPES)
            item_id = f"Q_{concept}_{bloom[:3]}_{random.randint(1, 10)}"
            
            # Difficulty modifier based on Bloom level
            bloom_penalty = {
                "REMEMBER": 0.0,
                "UNDERSTAND": 0.08,
                "APPLY": 0.18,
                "ANALYSE": 0.28
            }[bloom]
            
            # Probability of success
            p_success = max(0.05, min(0.98, base_ability - bloom_penalty + (step * 0.003)))
            is_correct = 1 if random.random() < p_success else 0
            score = float(is_correct)
            
            # Behavioral telemetry features
            if is_correct:
                duration = max(10.0, np.random.normal(loc=45 - (base_ability * 15), scale=12))
                attempts = 1 if random.random() > 0.15 else 2
                hints = 0 if random.random() > 0.10 else 1
                error_category = None
            else:
                duration = max(20.0, np.random.normal(loc=95 - (base_ability * 20), scale=25))
                attempts = random.choice([2, 3, 4])
                hints = random.choice([1, 2, 3])
                error_category = random.choice(["SYNTAX_ERROR", "LOGIC_ERROR", "RUNTIME_EXCEPTION", "WRONG_OUTPUT"])
            
            # Self-reported confidence rating (1 to 5)
            if persona == "OVERCONFIDENT":
                # Consistently high confidence regardless of correctness!
                conf_rating = random.choices([4, 5], weights=[0.4, 0.6])[0]
            elif is_correct:
                conf_rating = random.choices([3, 4, 5], weights=[0.2, 0.5, 0.3])[0]
            else:
                conf_rating = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
                
            events.append({
                "learner_id": learner_id,
                "subject_id": "JAVA_FUNDAMENTALS",
                "concept_id": concept,
                "bloom_level": bloom,
                "item_id": item_id,
                "question_type": q_type,
                "is_correct": is_correct,
                "score": score,
                "duration_seconds": round(duration, 2),
                "attempt_count": attempts,
                "hints_requested": hints,
                "error_category": error_category if error_category else "NONE",
                "confidence_rating": conf_rating,
                "timestamp": cur_time.isoformat()
            })
            
    df = pd.DataFrame(events)
    return df


def split_by_learner(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prevents data leakage by splitting at the learner ID level.
    """
    learners = df["learner_id"].unique().tolist()
    random.seed(random_seed)
    random.shuffle(learners)
    
    n_total = len(learners)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    
    train_learners = set(learners[:n_train])
    val_learners = set(learners[n_train:n_train + n_val])
    test_learners = set(learners[n_train + n_val:])
    
    train_df = df[df["learner_id"].isin(train_learners)].copy()
    val_df = df[df["learner_id"].isin(val_learners)].copy()
    test_df = df[df["learner_id"].isin(test_learners)].copy()
    
    return train_df, val_df, test_df


if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    print("Generating Benchmark Interaction Dataset...")
    dataset = generate_benchmark_events(num_learners=100, interactions_per_learner=45)
    train_df, val_df, test_df = split_by_learner(dataset)
    
    dataset_path = os.path.join(data_dir, "benchmark_interactions_full.csv")
    train_path = os.path.join(data_dir, "train_interactions.csv")
    val_path = os.path.join(data_dir, "val_interactions.csv")
    test_path = os.path.join(data_dir, "test_interactions.csv")
    
    dataset.to_csv(dataset_path, index=False)
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"Generated {len(dataset)} total interaction records across {dataset['learner_id'].nunique()} learners.")
    print(f"Train split: {len(train_df)} rows | Val split: {len(val_df)} rows | Test split: {len(test_df)} rows.")
    print(f"Saved dataset artifacts to: {data_dir}")
