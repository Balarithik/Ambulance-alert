from rest_framework import serializers
from .models import RiskPrediction, ModelArtifact


class PredictionSerializer(serializers.Serializer):
    patient_id = serializers.CharField(required=True, allow_blank=False)
    age = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=120)
    gender = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    heart_rate = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=300)
    temperature = serializers.FloatField(required=False, allow_null=True, min_value=20, max_value=50)
    sbp = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=350)
    dbp = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=250)
    respiratory_rate = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    map_value = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=300)

    def validate(self, attrs):
        # At least one core vital must be present in a reading. Missing individual
        # channels remain null and are handled by the training-fitted imputer.
        vital_keys = ("heart_rate", "temperature", "sbp", "dbp", "respiratory_rate", "map_value")
        if not any(attrs.get(key) is not None for key in vital_keys):
            raise serializers.ValidationError("At least one measured vital sign is required.")
        return attrs


class PredictionResultSerializer(serializers.Serializer):
    risk_probability = serializers.FloatField()
    risk_level = serializers.ChoiceField(choices=["LOW", "MODERATE", "HIGH", "CRITICAL"])
    prediction = serializers.IntegerField()
    prediction_id = serializers.IntegerField(required=False)
    model_name = serializers.CharField(required=False)
    history_points = serializers.IntegerField(required=False)
    clinical_decision_support_only = serializers.BooleanField(required=False)
    clinical_validation = serializers.BooleanField(required=False)


class HealthCheckSerializer(serializers.Serializer):
    model_loaded = serializers.BooleanField()
    schema_version = serializers.CharField(allow_null=True, required=False)
    selected_model = serializers.CharField(allow_null=True, required=False)
    feature_count = serializers.IntegerField(required=False)
    error = serializers.CharField(allow_null=True, required=False)
    clinical_validation = serializers.BooleanField(required=False)


class RiskPredictionSerializer(serializers.ModelSerializer):
    """Serializer for persisted risk-prediction records."""

    class Meta:
        model = RiskPrediction
        fields = [
            "id", "patient", "timestamp", "probability", "risk_level",
            "model_version", "heart_rate", "temperature", "sbp", "dbp",
            "respiratory_rate",
        ]
        read_only_fields = ["id", "timestamp"]


class ModelArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelArtifact
        fields = ["id", "name", "version", "file_path", "uploaded_at", "description"]
