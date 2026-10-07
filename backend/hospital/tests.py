from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from patients.models import Patient
from ambulance.models import Ambulance
from hospital.models import HospitalPreparation


class HospitalAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = Patient.objects.create(
            patient_id="P202",
            name="Jane Doe",
            age=60,
            gender="F",
            systolic_bp=130,
            diastolic_bp=85,
            respiratory_rate=20,
        )
        self.ambulance = Ambulance.objects.create(
            ambulance_id="AMB-02",
            driver_name="Bob Wilson",
            status="EN_ROUTE",
        )
        self.prep = HospitalPreparation.objects.create(
            patient=self.patient,
            ambulance=self.ambulance,
            required_preparation="ICU Bed, Ventilator",
            status="PENDING",
        )

    def test_hospital_prep_list(self):
        response = self.client.get("/api/hospital/preparations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_acknowledge_prep(self):
        response = self.client.post(
            f"/api/hospital/preparations/{self.prep.id}/acknowledge/",
            {"acknowledged_by": "Dr. Sarah Adams", "notes": "Bed reserved"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ACKNOWLEDGED")
        self.assertEqual(response.data["acknowledged_by"], "Dr. Sarah Adams")

    def test_update_status(self):
        response = self.client.post(
            f"/api/hospital/preparations/{self.prep.id}/update_status/",
            {"status": "READY"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "READY")
