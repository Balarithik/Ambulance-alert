from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Patient, SensorReading
from .serializers import PatientSerializer, SensorReadingSerializer

class PatientViewSet(viewsets.ModelViewSet):
    """API endpoints for managing Patients and Vitals."""
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'patient_id'

    def get_object(self):
        """Allow lookup by patient_id or database pk."""
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_field
        val = self.kwargs[lookup_url_kwarg]
        
        # Try finding by patient_id first
        patient = queryset.filter(patient_id=val).first()
        if patient:
            return patient
        
        # If numeric, try by pk
        if str(val).isdigit():
            patient = queryset.filter(pk=val).first()
            if patient:
                return patient
                
        return super().get_object()

    @action(detail=True, methods=['GET'])
    def history(self, request, patient_id=None):
        """Retrieve historical vitals and predictions for patient."""
        patient = self.get_object()
        readings = patient.sensor_readings.all()
        predictions = patient.risk_predictions.all()
        
        from ml_engine.serializers import RiskPredictionSerializer
        return Response({
            'patient_id': patient.patient_id,
            'readings': SensorReadingSerializer(readings, many=True).data,
            'predictions': RiskPredictionSerializer(predictions, many=True).data,
        })


class SensorReadingViewSet(viewsets.ModelViewSet):
    """API endpoints for sensor readings."""
    queryset = SensorReading.objects.all()
    serializer_class = SensorReadingSerializer
