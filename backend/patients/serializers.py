from rest_framework import serializers
from .models import Patient, SensorReading

class SensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = [
            'id', 'patient', 'reading_id', 'heart_rate', 'temperature',
            'timestamp', 'device_id', 'new_reading'
        ]
        read_only_fields = ['id', 'timestamp']


class PatientSerializer(serializers.ModelSerializer):
    latest_sensor_reading = serializers.SerializerMethodField()
    latest_prediction = serializers.SerializerMethodField()
    hospital_prep = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'name', 'age', 'gender',
            'systolic_bp', 'diastolic_bp', 'respiratory_rate',
            'symptoms', 'medical_history', 'allergies', 'attender_observation',
            'image', 'created_at', 'updated_at',
            'latest_sensor_reading', 'latest_prediction', 'hospital_prep'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_latest_sensor_reading(self, obj):
        reading = obj.sensor_readings.order_by('-timestamp').first()
        if reading:
            return SensorReadingSerializer(reading).data
        return None

    def get_latest_prediction(self, obj):
        prediction = obj.risk_predictions.order_by('-timestamp').first()
        if prediction:
            from ml_engine.serializers import RiskPredictionSerializer
            return RiskPredictionSerializer(prediction).data
        return None

    def get_hospital_prep(self, obj):
        prep = getattr(obj, 'hospital_preparations', None)
        if prep:
            first_prep = prep.order_by('-id').first()
            if first_prep:
                from hospital.serializers import HospitalPreparationSerializer
                return HospitalPreparationSerializer(first_prep).data
        return None
