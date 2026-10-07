from django.contrib import admin
from .models import HospitalPreparation


@admin.register(HospitalPreparation)
class HospitalPreparationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "ambulance", "status", "created_at", "acknowledged_by")
    list_filter = ("status", "created_at")
