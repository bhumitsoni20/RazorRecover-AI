import pytest
from app.ml.recovery_model import ml_recovery_model


def test_ml_model_training_and_metrics():
    metrics = ml_recovery_model.get_metrics()
    assert "roc_auc" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert metrics["roc_auc"] > 0.70
    assert metrics["f1_score"] > 0.60
    assert "confusion_matrix" in metrics


def test_ml_prediction_high_probability_case():
    prob, expected, ver = ml_recovery_model.predict(
        amount=4999.0,
        payment_method="upi",
        failure_reason="upi_timeout",
        attempt_number=1,
        customer_success_rate=0.916,
        is_anomaly=True,
    )
    assert 0.70 <= prob <= 1.0
    assert expected == round(4999.0 * prob, 2)
    assert "logistic-regression" in ver


def test_ml_prediction_low_probability_case():
    prob, expected, ver = ml_recovery_model.predict(
        amount=38000.0,
        payment_method="card",
        failure_reason="insufficient_funds",
        attempt_number=2,
        customer_success_rate=0.40,
        is_anomaly=False,
    )
    assert prob < 0.60
