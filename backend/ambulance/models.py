from django.db import models

class Ambulance(models.Model):
    """Ambulance unit information & telemetry."""
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('EN_ROUTE', 'En Route to Hospital'),
        ('ARRIVED', 'Arrived at Hospital'),
        ('INACTIVE', 'Inactive'),
    )

    ambulance_id = models.CharField(max_length=50, unique=True, default="AMB-101")
    driver_name = models.CharField(max_length=100, default="Paramedic Team A")
    contact_number = models.CharField(max_length=20, default="+1-800-555-AMB1")
    esp32_ip = models.CharField(max_length=45, default="10.194.207.47", help_text="ESP32 Device IP Address")
    
    # Navigation & Dispatch
    location_lat = models.FloatField(default=12.9716, help_text="Current Latitude")
    location_lng = models.FloatField(default=77.5946, help_text="Current Longitude")
    destination_hospital = models.CharField(max_length=150, default="City Emergency Trauma Center")
    eta_minutes = models.PositiveIntegerField(default=10, help_text="Estimated Time of Arrival in minutes")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='EN_ROUTE')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ambulances"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.ambulance_id} ({self.status}) - ETA: {self.eta_minutes} mins"
