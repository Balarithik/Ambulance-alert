from django.contrib import admin
from .models import Ambulance


@admin.register(Ambulance)
class AmbulanceAdmin(admin.ModelAdmin):
    list_display = ("ambulance_id", "driver_name", "contact_number", "status", "esp32_ip", "eta_minutes")
    list_filter = ("status",)
