from django.contrib import admin
from .models import Patient, SensorReading


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "name", "age", "gender", "created_at")
    search_fields = ("patient_id", "name")


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ("reading_id", "patient", "heart_rate", "temperature", "timestamp", "device_id")
    list_filter = ("device_id", "timestamp")
