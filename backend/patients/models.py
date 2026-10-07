from django.db import models

class Patient(models.Model):
    """Patient record in LifeSyncAI system."""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('Other', 'Other'),
    )

    patient_id = models.CharField(max_length=50, unique=True, help_text="Unique Patient identifier")
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    
    # Manual vital sign inputs
    systolic_bp = models.PositiveIntegerField(default=120, help_text="Systolic Blood Pressure (mmHg)")
    diastolic_bp = models.PositiveIntegerField(default=80, help_text="Diastolic Blood Pressure (mmHg)")
    respiratory_rate = models.PositiveIntegerField(default=18, help_text="Respiratory Rate (breaths/min)")
    
    # Clinical history & notes
    symptoms = models.TextField(blank=True, default="", help_text="Presenting symptoms")
    medical_history = models.TextField(blank=True, default="", help_text="Pre-existing conditions")
    allergies = models.TextField(blank=True, default="", help_text="Known allergies")
    attender_observation = models.TextField(blank=True, default="", help_text="Ambulance attender observation notes")
    
    # Patient photo
    image = models.ImageField(upload_to="patients/images/", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patients"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient_id} - {self.name} ({self.age}y/o {self.gender})"


class SensorReading(models.Model):
    """Telemetry reading captured from ESP32 sensor hardware."""
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="sensor_readings", null=True, blank=True
    )
    reading_id = models.BigIntegerField(null=True, blank=True)
    heart_rate = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    device_id = models.CharField(max_length=100, default="LifeSyncAI-Ambulance-ESP32")
    new_reading = models.BooleanField(default=True)

    class Meta:
        db_table = "sensor_readings"
        ordering = ["-timestamp"]

    def __str__(self):
        patient_str = self.patient.patient_id if self.patient else "Unassigned"
        return f"Reading #{self.reading_id or self.id} ({patient_str}) - HR: {self.heart_rate}, Temp: {self.temperature}°C"
