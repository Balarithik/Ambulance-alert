import requests
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Ambulance
from .serializers import AmbulanceSerializer
from patients.models import SensorReading

logger = logging.getLogger(__name__)


class AmbulanceViewSet(viewsets.ModelViewSet):
    """API endpoints for ambulance management."""
    queryset = Ambulance.objects.all()
    serializer_class = AmbulanceSerializer
    lookup_field = 'ambulance_id'
    lookup_value_regex = '[^/]+'

    @action(detail=True, methods=['POST'])
    def fetch_esp32(self, request, ambulance_id=None):
        """Fetch latest reading from ESP32 sensor via Django backend proxy.
        
        Flow: Frontend → Django → ESP32 → Django → Frontend
        The browser never talks directly to the ESP32.
        """
        esp32_ip = request.data.get('esp32_ip')
        
        # Get or auto-create ambulance record
        try:
            ambulance, _ = Ambulance.objects.get_or_create(
                ambulance_id=ambulance_id,
                defaults={
                    'driver_name': f'Paramedic Unit ({ambulance_id})',
                    'esp32_ip': esp32_ip or '10.232.175.180',
                    'status': 'EN_ROUTE',
                }
            )
        except Exception as e:
            ambulance = None

        if not esp32_ip:
            esp32_ip = ambulance.esp32_ip if ambulance else '10.232.175.180'

        url = f"http://{esp32_ip}/api/data"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            # Store reading in database
            reading_kwargs = {
                'reading_id': data.get('reading_id', 0),
                'heart_rate': data.get('heart_rate'),
                'temperature': data.get('temperature'),
                'device_id': data.get('device', 'LifeSyncAI-Ambulance-ESP32'),
                'new_reading': data.get('new_reading', True),
            }

            patient_id_for_reading = request.data.get('patient_id', None)
            if patient_id_for_reading:
                from patients.models import Patient
                try:
                    patient = Patient.objects.get(patient_id=patient_id_for_reading)
                    reading_kwargs['patient'] = patient
                except Patient.DoesNotExist:
                    pass

            reading = SensorReading.objects.create(**reading_kwargs)

            return Response({
                'esp32_data': data,
                'stored_reading_id': reading.id,
                'status': 'ok',
            })
        except requests.ConnectionError:
            logger.error(f"ESP32 unreachable at {esp32_ip}")
            return Response(
                {'error': f'ESP32 unreachable at {esp32_ip}. Check device connection.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except requests.Timeout:
            logger.error(f"ESP32 timeout at {esp32_ip}")
            return Response(
                {'error': f'ESP32 request timed out at {esp32_ip}.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            logger.error(f"ESP32 fetch error: {e}")
            return Response(
                {'error': f'Failed to fetch ESP32 data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['GET'])
    def esp32_status(self, request, ambulance_id=None):
        """Check ESP32 health/status."""
        esp32_ip = request.query_params.get('esp32_ip')
        if not esp32_ip:
            try:
                ambulance = Ambulance.objects.get(ambulance_id=ambulance_id)
                esp32_ip = ambulance.esp32_ip
            except Ambulance.DoesNotExist:
                esp32_ip = '10.232.175.180'

        try:
            resp = requests.get(f"http://{esp32_ip}/api/status", timeout=3)
            resp.raise_for_status()
            return Response({'esp32_status': resp.json(), 'connected': True})
        except Exception as e:
            return Response({'connected': False, 'error': str(e)})


class DemoDataViewSet(viewsets.ViewSet):
    """Generate simulated sensor data for demo mode."""

    @action(detail=False, methods=['POST'])
    def generate(self, request):
        """Generate a simulated sensor reading for demo mode."""
        import random
        scenario = request.data.get('scenario', 'stable')

        if scenario == 'stable':
            hr = random.randint(65, 85)
            temp = round(random.uniform(36.2, 37.0), 1)
        elif scenario == 'increasing_risk':
            hr = random.randint(90, 110)
            temp = round(random.uniform(37.5, 38.5), 1)
        elif scenario == 'high_risk':
            hr = random.randint(110, 130)
            temp = round(random.uniform(38.5, 39.5), 1)
        elif scenario == 'critical':
            hr = random.randint(130, 160)
            temp = round(random.uniform(39.5, 41.0), 1)
        else:
            hr = random.randint(65, 85)
            temp = round(random.uniform(36.2, 37.0), 1)

        data = {
            'device': 'DEMO-SIMULATED',
            'reading_id': random.randint(1000, 9999),
            'new_reading': True,
            'heart_rate': hr,
            'temperature': temp,
            'timestamp_ms': 0,
            'heart_rate_sensor': 'simulated',
            'temperature_sensor': 'simulated',
            'is_demo': True,
            'scenario': scenario,
        }

        patient_id = request.data.get('patient_id')
        if patient_id:
            from patients.models import Patient
            try:
                patient = Patient.objects.get(patient_id=patient_id)
                SensorReading.objects.create(
                    patient=patient,
                    reading_id=data['reading_id'],
                    heart_rate=hr,
                    temperature=temp,
                    device_id='DEMO-SIMULATED',
                    new_reading=True,
                )
            except Patient.DoesNotExist:
                pass

        return Response(data)
