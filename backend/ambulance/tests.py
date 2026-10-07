from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Ambulance


class AmbulanceAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.amb_data = {
            "ambulance_id": "AMB-01",
            "driver_name": "Alice Smith",
            "contact_number": "+1234567890",
            "esp32_ip": "192.168.1.100",
            "location": "Sector 5",
            "eta_minutes": 15,
            "status": "EN_ROUTE",
        }

    def test_ambulance_crud(self):
        response = self.client.post("/api/ambulance/", self.amb_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["ambulance_id"], "AMB-01")

        response = self.client.get("/api/ambulance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_demo_data_generation(self):
        response = self.client.post("/api/ambulance/demo/generate/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("is_demo"))
        self.assertIn("heart_rate", response.data)
        self.assertIn("temperature", response.data)
