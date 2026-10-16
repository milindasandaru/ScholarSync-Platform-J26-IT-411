"""
Competency Assessment and Calibration Engine - Core Tracing Models
Implements the 3 comparative models defined in the SLIIT proposal:
1. Baseline Model: Score-Only Moving Average.
2. Bayesian Knowledge Tracing (BKT): Sequential mastery estimation using HMM.
3. Behaviour-Informed Supervised Calibrated Classifier: Logistic Regression with Platt / Isotonic Calibration.
4. Metacognitive Gap Engine: Computes Expected Calibration Error (ECE) and Illusion of Competence.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

# Robust Corbett & Anderson BKT engine
from bkt_model import BayesianKnowledgeTracer


def calculate_expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE):
    Weighted average difference between predicted confidence probability and empirical accuracy.
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    
    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i + 1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper) if i < n_bins - 1 else (y_prob >= bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
            
    return float(ece)


class CompetencyCalibrationEngine:
    def __init__(self):
        self.bkt_tracer = BayesianKnowledgeTracer()
        self.supervised_model = None
        self.calibrated_model = None
        self.bloom_encoding = {"REMEMBER": 1, "UNDERSTAND": 2, "APPLY": 3, "ANALYSE": 4}

    def _extract_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts observable telemetry features:
        - Prior correctness / score
        - Normalized duration on task (log scaled)
        - Attempt count
        - Hints requested
        - Encoded Bloom cognitive depth
        """
        duration_log = np.log1p(df["duration_seconds"].values)
        attempts = df["attempt_count"].values
        hints = df["hints_requested"].values
        bloom_num = df["bloom_level"].map(self.bloom_encoding).fillna(1).values
        
        # Historical running score per student
        df["prior_score_avg"] = df.groupby("learner_id")["score"].transform(lambda x: x.shift().expanding().mean()).fillna(0.5)
        prior_score = df["prior_score_avg"].values
        
        X = np.column_stack([
            prior_score,
            duration_log,
            attempts,
            hints,
            bloom_num
        ])
        y = df["is_correct"].values
        return X, y

    def train_models(self, train_df: pd.DataFrame, val_df: pd.DataFrame):
        """
        Fits BKT, Supervised Model, and Calibration Layer on training data.
        """
        print("[Engine] Fitting Bayesian Knowledge Tracing (BKT) parameters...")
        self.bkt_tracer.fit(train_df, skill_col="concept_id", correct_col="is_correct")
        print("[Engine] BKT parameter fitting completed successfully.")

        # Train Supervised Behaviour-Informed Classifier
        print("[Engine] Training Supervised Classifier...")
        X_train, y_train = self._extract_features(train_df)
        base_clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=200)
        base_clf.fit(X_train, y_train)
        self.supervised_model = base_clf

        # Calibrate using Isotonic / Platt Scaling
        print("[Engine] Calibrating probabilities via CalibratedClassifierCV...")
        X_val, y_val = self._extract_features(val_df)
        calibrated_clf = CalibratedClassifierCV(estimator=base_clf, method="isotonic", cv="prefit")
        calibrated_clf.fit(X_val, y_val)
        self.calibrated_model = calibrated_clf
        print("[Engine] Calibration layer trained.")

    def evaluate(self, test_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Runs tri-model evaluation on unseen test learners:
        Computes AUC-ROC, Brier Score, and Expected Calibration Error (ECE).
        """
        X_test, y_test = self._extract_features(test_df)
        
        # 1. Baseline: Prior score average
        baseline_probs = test_df["prior_score_avg"].values
        baseline_auc = roc_auc_score(y_test, baseline_probs)
        baseline_brier = brier_score_loss(y_test, baseline_probs)
        baseline_ece = calculate_expected_calibration_error(y_test, baseline_probs)

        # 2. Uncalibrated Supervised Classifier
        raw_probs = self.supervised_model.predict_proba(X_test)[:, 1]
        raw_auc = roc_auc_score(y_test, raw_probs)
        raw_brier = brier_score_loss(y_test, raw_probs)
        raw_ece = calculate_expected_calibration_error(y_test, raw_probs)

        # 3. Calibrated Behaviour-Informed Model
        calib_probs = self.calibrated_model.predict_proba(X_test)[:, 1]
        calib_auc = roc_auc_score(y_test, calib_probs)
        calib_brier = brier_score_loss(y_test, calib_probs)
        calib_ece = calculate_expected_calibration_error(y_test, calib_probs)

        return {
            "Score_Only_Baseline": {
                "AUC_ROC": round(float(baseline_auc), 4),
                "Brier_Score": round(float(baseline_brier), 4),
                "ECE": round(float(baseline_ece), 4)
            },
            "Raw_Supervised_Model": {
                "AUC_ROC": round(float(raw_auc), 4),
                "Brier_Score": round(float(raw_brier), 4),
                "ECE": round(float(raw_ece), 4)
            },
            "Calibrated_Behaviour_Model": {
                "AUC_ROC": round(float(calib_auc), 4),
                "Brier_Score": round(float(calib_brier), 4),
                "ECE": round(float(calib_ece), 4)
            }
        }

    def compute_metacognitive_gap(self, reported_confidence: float, mastery_prob: float) -> Tuple[float, str]:
        """
        Metacognitive Gap = Confidence (normalized 0-1) - Model Mastery Probability
        """
        gap = round(reported_confidence - mastery_prob, 3)
        if gap > 0.25:
            status = "OVERCONFIDENT" # Illusion of Competence
        elif gap < -0.25:
            status = "UNDERCONFIDENT" # Imposter Phenomenon
        else:
            status = "WELL_CALIBRATED"
        return gap, status

    def save_checkpoints(self, model_dir: str):
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(self.calibrated_model, os.path.join(model_dir, "calibrated_classifier.joblib"))
        joblib.dump(self.supervised_model, os.path.join(model_dir, "base_classifier.joblib"))
        joblib.dump(self.bkt_tracer, os.path.join(model_dir, "bkt_tracer.joblib"))
        print(f"[Engine] Models saved to {model_dir}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    train_df = pd.read_csv(os.path.join(data_dir, "train_interactions.csv"))
    val_df = pd.read_csv(os.path.join(data_dir, "val_interactions.csv"))
    test_df = pd.read_csv(os.path.join(data_dir, "test_interactions.csv"))

    engine = CompetencyCalibrationEngine()
    engine.train_models(train_df, val_df)
    results = engine.evaluate(test_df)
    
    print("\n" + "=" * 55)
    print("SLIIT MID-REVIEW EVALUATION BENCHMARK RESULTS")
    print("=" * 55)
    for model_name, metrics in results.items():
        print(f"\n[{model_name}]")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
    print("=" * 55)

    # Save trained checkpoints
    model_dir = os.path.join(current_dir, "models")
    engine.save_checkpoints(model_dir)
