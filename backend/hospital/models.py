from django.db import models


class HospitalPreparation(models.Model):
    """Tracks hospital preparation for an incoming ambulance patient."""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready'),
    )

    patient = models.ForeignKey(
        'patients.Patient', on_delete=models.CASCADE, related_name='hospital_preparations'
    )
    ambulance = models.ForeignKey(
        'ambulance.Ambulance', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='hospital_preparations'
    )
    required_preparation = models.TextField(
        blank=True, default="",
        help_text="Required resources/preparation notes"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING'
    )
    acknowledged_by = models.CharField(max_length=100, blank=True, default="")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hospital_preparations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prep for {self.patient.patient_id} - {self.status}"
