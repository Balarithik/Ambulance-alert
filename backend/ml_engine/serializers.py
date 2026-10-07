from rest_framework import serializers
from .models import RiskPrediction, ModelArtifact


class PredictionSerializer(serializers.Serializer):
    heart_rate = serializers.FloatField()
    temperature = serializers.FloatField(required=False, allow_null=True)
    sbp = serializers.FloatField()
    dbp = serializers.FloatField()
    respiratory_rate = serializers.FloatField()
    patient_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class PredictionResultSerializer(serializers.Serializer):
    risk_probability = serializers.FloatField()
    risk_level = serializers.CharField()
    prediction = serializers.IntegerField()
    factors = serializers.ListField(child=serializers.DictField(), required=False)


class HealthCheckSerializer(serializers.Serializer):
    model_loaded = serializers.BooleanField()
    risk_thresholds = serializers.DictField()


class RiskPredictionSerializer(serializers.ModelSerializer):
    """Serializer for ML risk predictions."""
    
    class Meta:
        model = RiskPrediction
        fields = [
            "id", "patient", "timestamp", "probability", "risk_level",
            "model_version", "heart_rate", "temperature", "sbp", "dbp",
            "respiratory_rate"
        ]
        read_only_fields = ["id", "timestamp"]


class ModelArtifactSerializer(serializers.ModelSerializer):
    """Serializer for ML model artifacts."""
    
    class Meta:
        model = ModelArtifact
        fields = ["id", "name", "version", "file_path", "uploaded_at", "description"]
