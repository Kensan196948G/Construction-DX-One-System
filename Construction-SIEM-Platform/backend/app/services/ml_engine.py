import math
import time
from collections import defaultdict
from statistics import mean, stdev
from typing import Any

ANOMALY_THRESHOLD_ZSCORE = 2.5
ANOMALY_THRESHOLD_MOVING_AVG_DEVIATION = 0.3
ANOMALY_THRESHOLD_PERCENTILE_LOW = 0.01
ANOMALY_THRESHOLD_PERCENTILE_HIGH = 0.99
HISTORY_WINDOW_SIZE = 100


class MLDetector:
    """Base detector with fit/predict/explain interface."""

    def __init__(self, parameters: dict | None = None):
        self.parameters = parameters or {}
        self._fitted = False

    def fit(self, data: list[dict[str, float]]) -> dict[str, Any]:
        """Fit detector on historical data. Returns metrics."""
        raise NotImplementedError

    def predict(self, features: dict[str, float]) -> float:
        """Return anomaly score 0.0-1.0."""
        raise NotImplementedError

    def explain(self, features: dict[str, float]) -> str:
        """Return human-readable explanation of why this is anomalous."""
        raise NotImplementedError

    @property
    def fitted(self) -> bool:
        return self._fitted


class ZScoreDetector(MLDetector):
    """Anomaly detection using z-score (standard deviation from mean)."""

    def __init__(self, parameters: dict | None = None):
        super().__init__(parameters)
        self._means: dict[str, float] = {}
        self._stdevs: dict[str, float] = {}
        self._threshold = self.parameters.get("zscore_threshold", ANOMALY_THRESHOLD_ZSCORE)

    def fit(self, data: list[dict[str, float]]) -> dict[str, Any]:
        feature_groups: dict[str, list[float]] = defaultdict(list)
        for point in data:
            for key, val in point.items():
                if isinstance(val, int | float):
                    feature_groups[key].append(float(val))

        for key, vals in feature_groups.items():
            if len(vals) < 2:
                self._means[key] = float(vals[0]) if vals else 0.0
                self._stdevs[key] = 0.0
            else:
                self._means[key] = mean(vals)
                self._stdevs[key] = stdev(vals)

        self._fitted = True
        n_features = len(self._means)
        return {
            "n_features": n_features,
            "features_trained": list(self._means.keys()),
            "threshold": self._threshold,
        }

    def predict(self, features: dict[str, float]) -> float:
        if not self._fitted:
            return 0.5
        max_z = 0.0
        for key, val in features.items():
            if isinstance(val, int | float) and key in self._means:
                mu = self._means[key]
                sigma = self._stdevs[key]
                if sigma > 0:
                    z = abs((float(val) - mu) / sigma)
                    max_z = max(max_z, z)
        score = min(max_z / (self._threshold * 3), 1.0)
        if max_z <= self._threshold:
            score = max_z / (self._threshold * 3)
        return round(score, 4)

    def explain(self, features: dict[str, float]) -> str:
        if not self._fitted:
            return "Model not trained"
        parts: list[str] = []
        for key, val in features.items():
            if isinstance(val, int | float) and key in self._means:
                mu = self._means[key]
                sigma = self._stdevs[key]
                if sigma > 0:
                    z = abs((float(val) - mu) / sigma)
                    if z > self._threshold:
                        parts.append(
                            f"{key}={val} (mean={mu:.2f}, std={sigma:.2f}, z={z:.2f})"
                        )
        if parts:
            return f"Z-score anomaly detected: {', '.join(parts)}"
        return "No anomalous features detected"


class MovingAverageDetector(MLDetector):
    """Anomaly detection using moving average deviation."""

    def __init__(self, parameters: dict | None = None):
        super().__init__(parameters)
        self._window = self.parameters.get("window_size", 20)
        self._baseline: dict[str, list[float]] = defaultdict(list)
        self._averages: dict[str, float] = {}
        self._threshold = self.parameters.get(
            "deviation_threshold", ANOMALY_THRESHOLD_MOVING_AVG_DEVIATION
        )

    def fit(self, data: list[dict[str, float]]) -> dict[str, Any]:
        for point in data:
            for key, val in point.items():
                if isinstance(val, int | float):
                    self._baseline[key].append(float(val))

        for key, vals in self._baseline.items():
            if vals:
                self._averages[key] = mean(vals[-self._window:])

        self._fitted = True
        return {
            "window": self._window,
            "features_trained": list(self._averages.keys()),
            "n_samples": min(len(v) for v in self._baseline.values()) if self._baseline else 0,
        }

    def predict(self, features: dict[str, float]) -> float:
        if not self._fitted or not self._averages:
            return 0.5
        max_dev = 0.0
        for key, val in features.items():
            if isinstance(val, int | float) and key in self._averages:
                baseline = self._averages[key]
                if baseline != 0:
                    dev = abs((float(val) - baseline) / baseline)
                elif float(val) != 0:
                    dev = 1.0
                else:
                    dev = 0.0
                max_dev = max(max_dev, dev)
        score = min(max_dev / (self._threshold * 3), 1.0)
        return round(score, 4)

    def explain(self, features: dict[str, float]) -> str:
        if not self._fitted:
            return "Model not trained"
        parts: list[str] = []
        for key, val in features.items():
            if isinstance(val, int | float) and key in self._averages:
                baseline = self._averages[key]
                if baseline != 0:
                    dev = abs((float(val) - baseline) / baseline)
                    if dev > self._threshold:
                        parts.append(
                            f"{key}={val} (baseline={baseline:.2f}, deviation={dev:.2%})"
                        )
                elif float(val) != 0 and self._threshold < 1.0:
                    parts.append(f"{key}={val} (baseline={baseline:.2f}, unexpected non-zero)")
        if parts:
            return f"Moving-average anomaly detected: {', '.join(parts)}"
        return "No anomalous features detected"


class PercentileDetector(MLDetector):
    """Anomaly detection using percentile-based thresholds."""

    def __init__(self, parameters: dict | None = None):
        super().__init__(parameters)
        self._low_percentile = self.parameters.get("low_percentile", ANOMALY_THRESHOLD_PERCENTILE_LOW)
        self._high_percentile = self.parameters.get(
            "high_percentile", ANOMALY_THRESHOLD_PERCENTILE_HIGH
        )
        self._percentiles: dict[str, tuple[float, float]] = {}
        self._data: dict[str, list[float]] = defaultdict(list)

    @staticmethod
    def _percentile(sorted_vals: list[float], p: float) -> float:
        if not sorted_vals:
            return 0.0
        k = (len(sorted_vals) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)

    def fit(self, data: list[dict[str, float]]) -> dict[str, Any]:
        for point in data:
            for key, val in point.items():
                if isinstance(val, int | float):
                    self._data[key].append(float(val))

        for key, vals in self._data.items():
            if len(vals) >= 2:
                sorted_vals = sorted(vals)
                low = self._percentile(sorted_vals, self._low_percentile)
                high = self._percentile(sorted_vals, self._high_percentile)
                self._percentiles[key] = (low, high)

        self._fitted = True
        return {
            "features_trained": list(self._percentiles.keys()),
            "n_samples": min(len(v) for v in self._data.values()) if self._data else 0,
        }

    def predict(self, features: dict[str, float]) -> float:
        if not self._fitted or not self._percentiles:
            return 0.5
        max_violation = 0.0
        for key, val in features.items():
            if isinstance(val, int | float) and key in self._percentiles:
                low, high = self._percentiles[key]
                v = float(val)
                if v < low:
                    violation = (low - v) / (abs(low) + 1)
                    max_violation = max(max_violation, violation)
                elif v > high:
                    violation = (v - high) / (abs(high) + 1)
                    max_violation = max(max_violation, violation)
        score = min(max_violation, 1.0)
        return round(score, 4)

    def explain(self, features: dict[str, float]) -> str:
        if not self._fitted:
            return "Model not trained"
        parts: list[str] = []
        for key, val in features.items():
            if isinstance(val, int | float) and key in self._percentiles:
                low, high = self._percentiles[key]
                v = float(val)
                if v < low:
                    parts.append(f"{key}={val} (below P{self._low_percentile:.0%}={low:.2f})")
                elif v > high:
                    parts.append(f"{key}={val} (above P{self._high_percentile:.0%}={high:.2f})")
        if parts:
            return f"Percentile anomaly detected: {', '.join(parts)}"
        return "No anomalous features detected"


class RuleBasedBaselineDetector(MLDetector):
    """Combined detector using multiple statistical methods."""

    def __init__(self, parameters: dict | None = None):
        super().__init__(parameters)
        self._detectors: dict[str, MLDetector] = {
            "zscore": ZScoreDetector(parameters),
            "moving_avg": MovingAverageDetector(parameters),
            "percentile": PercentileDetector(parameters),
        }
        self._weights = self.parameters.get(
            "detector_weights", {"zscore": 0.5, "moving_avg": 0.3, "percentile": 0.2}
        )

    def fit(self, data: list[dict[str, float]]) -> dict[str, Any]:
        all_metrics: dict[str, Any] = {}
        total_time = 0.0
        for name, detector in self._detectors.items():
            start = time.monotonic()
            metrics = detector.fit(data)
            elapsed = time.monotonic() - start
            total_time += elapsed
            all_metrics[name] = {**metrics, "training_time": round(elapsed, 4)}
        all_metrics["total_training_time"] = round(total_time, 4)
        self._fitted = True
        return all_metrics

    def predict(self, features: dict[str, float]) -> float:
        weighted_score = 0.0
        for name, detector in self._detectors.items():
            if detector.fitted:
                score = detector.predict(features)
                weight = self._weights.get(name, 0.25)
                weighted_score += score * weight
        return round(weighted_score, 4)

    def explain(self, features: dict[str, float]) -> str:
        explanations: list[str] = []
        for name, detector in self._detectors.items():
            if detector.fitted:
                explanations.append(f"[{name}] {detector.explain(features)}")
        return " | ".join(explanations)


class AnomalyHistoryTracker:
    """Tracks anomaly history per entity."""

    def __init__(self, window: int = HISTORY_WINDOW_SIZE):
        self._window = window
        self._history: dict[str, list[float]] = defaultdict(list)
        self._baselines: dict[str, dict[str, float]] = defaultdict(dict)

    def record(self, entity_id: str, score: float) -> None:
        self._history[entity_id].append(score)
        if len(self._history[entity_id]) > self._window:
            self._history[entity_id] = self._history[entity_id][-self._window:]

    def get_recent_scores(self, entity_id: str, n: int = 10) -> list[float]:
        return self._history.get(entity_id, [])[-n:]

    def get_baseline(self, entity_id: str) -> dict[str, float]:
        scores = self._history.get(entity_id, [])
        if len(scores) < 2:
            return {"mean": 0.0, "std": 0.0, "n": 0}
        return {
            "mean": mean(scores),
            "std": stdev(scores) if len(scores) > 1 else 0.0,
            "n": len(scores),
        }

    def is_escalating(self, entity_id: str, n: int = 5) -> bool:
        recent = self._history.get(entity_id, [])[-n:]
        if len(recent) < n:
            return False
        return all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1))

    def summary(self) -> dict[str, Any]:
        return {
            "total_entities": len(self._history),
            "entity_ids": list(self._history.keys()),
        }


class MLDetectionEngine:
    """Orchestrates the detection pipeline."""

    def __init__(self, model_type: str = "ueba", parameters: dict | None = None):
        self.model_type = model_type
        self.parameters = parameters or {}
        self.tracker = AnomalyHistoryTracker()
        self.detector = self._create_detector()

    def _create_detector(self) -> MLDetector:
        algorithm = self.parameters.get("algorithm", "")
        if algorithm == "isolation_forest" or self.model_type == "ueba":
            return RuleBasedBaselineDetector(self.parameters)
        if algorithm == "autoencoder" or self.model_type == "netflow_anomaly":
            return MovingAverageDetector(self.parameters)
        if algorithm == "one_class_svm" or self.model_type == "iot_anomaly":
            return ZScoreDetector(self.parameters)
        return RuleBasedBaselineDetector(self.parameters)

    def train(self, data: list[dict[str, float]]) -> dict[str, Any]:
        start = time.monotonic()
        metrics = self.detector.fit(data)
        elapsed = time.monotonic() - start
        return {**metrics, "training_time_seconds": round(elapsed, 4), "success": True}

    def detect(self, features: dict[str, float], entity_id: str) -> tuple[float, bool, str]:
        score = self.detector.predict(features)
        baseline = self.tracker.get_baseline(entity_id)
        adaptive_threshold = 0.7
        if baseline["std"] > 0:
            adaptive_threshold = min(0.9, baseline["mean"] + 2 * baseline["std"])

        is_anomaly = score > adaptive_threshold or score > 0.8
        explanation = self.detector.explain(features) if is_anomaly else "Normal pattern"

        self.tracker.record(entity_id, score)
        return score, is_anomaly, explanation
