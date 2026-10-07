from django.contrib import admin
from .models import RiskPrediction, ModelArtifact


@admin.register(RiskPrediction)
class RiskPredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "risk_level", "probability", "timestamp", "model_version")
    list_filter = ("risk_level", "timestamp")


@admin.register(ModelArtifact)
class ModelArtifactAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "file_path", "uploaded_at")
