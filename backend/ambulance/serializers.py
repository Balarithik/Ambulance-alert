from rest_framework import serializers
from .models import Ambulance

class AmbulanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambulance
        fields = [
            'id', 'ambulance_id', 'driver_name', 'contact_number',
            'esp32_ip', 'location_lat', 'location_lng',
            'destination_hospital', 'eta_minutes', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
