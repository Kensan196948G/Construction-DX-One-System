
from app.services.ml_engine import (
    AnomalyHistoryTracker,
    MovingAverageDetector,
    PercentileDetector,
    RuleBasedBaselineDetector,
    ZScoreDetector,
)


def test_zscore_detection():
    detector = ZScoreDetector({"zscore_threshold": 2.0})
    normal_data = [{"value": float(i)} for i in range(50, 150)]
    detector.fit(normal_data)
    normal_score = detector.predict({"value": 100.0})
    anomaly_score = detector.predict({"value": 500.0})
    assert normal_score < anomaly_score
    assert anomaly_score > 0.5


def test_zscore_extreme_value():
    detector = ZScoreDetector({"zscore_threshold": 2.0})
    normal_data = [{"cpu": float(i % 50 + 20)} for i in range(100)]
    detector.fit(normal_data)
    extreme_score = detector.predict({"cpu": 9999.0})
    assert extreme_score > 0.8


def test_moving_average():
    detector = MovingAverageDetector({"window_size": 10, "deviation_threshold": 0.3})
    steady_data = [{"throughput": 100.0 + (i % 5) * 2} for i in range(50)]
    detector.fit(steady_data)
    normal_score = detector.predict({"throughput": 105.0})
    anomaly_score = detector.predict({"throughput": 500.0})
    assert normal_score < anomaly_score
    assert anomaly_score > normal_score


def test_percentile_detection():
    detector = PercentileDetector({"low_percentile": 0.05, "high_percentile": 0.95})
    data = [{"latency": float(i)} for i in range(1, 101)]
    detector.fit(data)
    normal_score = detector.predict({"latency": 50.0})
    anomaly_score = detector.predict({"latency": 200.0})
    assert normal_score < anomaly_score
    assert anomaly_score > normal_score


def test_rule_based_baseline():
    detector = RuleBasedBaselineDetector()
    data = [{"cpu": float(i % 30 + 10), "mem": float(i % 20 + 40)} for i in range(100)]
    detector.fit(data)
    normal_score = detector.predict({"cpu": 25.0, "mem": 50.0})
    assert normal_score < 0.6
    anomaly_score = detector.predict({"cpu": 999.0, "mem": 999.0})
    assert anomaly_score > normal_score


def test_anomaly_history_tracking():
    tracker = AnomalyHistoryTracker(window=10)
    for i in range(10):
        tracker.record("entity-1", 0.1 * i)
    recent = tracker.get_recent_scores("entity-1", 5)
    assert len(recent) == 5
    baseline = tracker.get_baseline("entity-1")
    assert baseline["n"] == 10
    assert baseline["mean"] > 0
    assert baseline["std"] > 0


def test_anomaly_escalating_detection():
    tracker = AnomalyHistoryTracker(window=20)
    for i in range(10):
        tracker.record("entity-1", 0.1 + i * 0.08)
    assert tracker.is_escalating("entity-1", 5) is True
    tracker.record("entity-1", 0.1)
    assert tracker.is_escalating("entity-1", 5) is False


def test_normal_pattern():
    detector = RuleBasedBaselineDetector()
    normal_data = [{"cpu": float(i % 20 + 40), "mem": float(i % 10 + 50)} for i in range(100)]
    detector.fit(normal_data)
    score = detector.predict({"cpu": 45.0, "mem": 55.0})
    assert 0.0 <= score <= 0.6


def test_extreme_value():
    detector = RuleBasedBaselineDetector()
    normal_data = [{"cpu": float(i % 20 + 40), "mem": float(i % 10 + 50)} for i in range(100)]
    detector.fit(normal_data)
    score = detector.predict({"cpu": 9999.0, "mem": 0.0})
    assert score > 0.5


def test_zscore_explain():
    detector = ZScoreDetector({"zscore_threshold": 1.0})
    detector.fit([{"a": 10.0}, {"a": 12.0}, {"a": 11.0}])
    explanation = detector.explain({"a": 100.0})
    assert "Z-score" in explanation or "anomaly" in explanation


def test_history_summary():
    tracker = AnomalyHistoryTracker()
    tracker.record("e1", 0.1)
    tracker.record("e2", 0.2)
    summary = tracker.summary()
    assert summary["total_entities"] == 2
    assert "e1" in summary["entity_ids"]
