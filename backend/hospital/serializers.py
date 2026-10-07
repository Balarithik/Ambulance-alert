from rest_framework import serializers
from .models import HospitalPreparation


class HospitalPreparationSerializer(serializers.ModelSerializer):
    patient_info = serializers.SerializerMethodField()
    ambulance_info = serializers.SerializerMethodField()
    latest_prediction = serializers.SerializerMethodField()
    latest_vitals = serializers.SerializerMethodField()

    class Meta:
        model = HospitalPreparation
        fields = [
            'id', 'patient', 'ambulance', 'required_preparation',
            'status', 'acknowledged_by', 'acknowledged_at', 'notes',
            'created_at', 'updated_at',
            'patient_info', 'ambulance_info', 'latest_prediction', 'latest_vitals',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_patient_info(self, obj):
        p = obj.patient
        image_url = None
        if p.image:
            request = self.context.get('request')
            if request:
                image_url = request.build_absolute_uri(p.image.url)
            else:
                image_url = p.image.url
        return {
            'patient_id': p.patient_id,
            'name': p.name,
            'age': p.age,
            'gender': p.gender,
            'systolic_bp': p.systolic_bp,
            'diastolic_bp': p.diastolic_bp,
            'respiratory_rate': p.respiratory_rate,
            'symptoms': p.symptoms,
            'medical_history': p.medical_history,
            'allergies': p.allergies,
            'attender_observation': p.attender_observation,
            'image': image_url,
        }

    def get_ambulance_info(self, obj):
        if obj.ambulance:
            return {
                'ambulance_id': obj.ambulance.ambulance_id,
                'driver_name': obj.ambulance.driver_name,
                'contact_number': obj.ambulance.contact_number,
                'eta_minutes': obj.ambulance.eta_minutes,
                'status': obj.ambulance.status,
            }
        return None

    def get_latest_prediction(self, obj):
        pred = obj.patient.risk_predictions.order_by('-timestamp').first()
        if pred:
            return {
                'probability': pred.probability,
                'risk_level': pred.risk_level,
                'model_version': pred.model_version,
                'timestamp': pred.timestamp,
                'heart_rate': pred.heart_rate,
                'temperature': pred.temperature,
                'sbp': pred.sbp,
                'dbp': pred.dbp,
                'respiratory_rate': pred.respiratory_rate,
            }
        return None

    def get_latest_vitals(self, obj):
        reading = obj.patient.sensor_readings.order_by('-timestamp').first()
        if reading:
            return {
                'heart_rate': reading.heart_rate,
                'temperature': reading.temperature,
                'timestamp': reading.timestamp,
                'device_id': reading.device_id,
            }
        return None
