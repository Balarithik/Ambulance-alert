from django.db import models


class RiskPrediction(models.Model):
    """ML risk prediction records."""
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="risk_predictions"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    probability = models.FloatField(
        help_text="Risk probability (0-1)"
    )
    risk_level = models.CharField(
        max_length=20,
        help_text="LOW, MODERATE, HIGH, or CRITICAL"
    )
    model_version = models.CharField(
        max_length=50, blank=True,
        help_text="Version of the ML model used"
    )
    
    # Features used for prediction
    heart_rate = models.PositiveIntegerField(blank=True, null=True)
    temperature = models.FloatField(blank=True, null=True)
    sbp = models.PositiveIntegerField(blank=True, null=True)
    dbp = models.PositiveIntegerField(blank=True, null=True)
    respiratory_rate = models.PositiveIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = "risk_predictions"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Risk {self.risk_level} for patient {self.patient.patient_id} (prob: {self.probability:.2f})"


class ModelArtifact(models.Model):
    """Track ML model artifacts."""
    name = models.CharField(max_length=100, unique=True)
    file_path = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default="1.0")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = "model_artifacts"

    def __str__(self):
        return f"{self.name} v{self.version}"
