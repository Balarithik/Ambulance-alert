from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .ml_predictor import ModelNotReadyError, load_predictor
from .serializers import (
    PredictionSerializer, PredictionResultSerializer, HealthCheckSerializer,
    RiskPredictionSerializer,
)
from .models import RiskPrediction


class MLEngineViewSet(viewsets.ViewSet):
    """ML API endpoints. Predictions are research decision support, not diagnoses."""

    @action(methods=["POST"], detail=False)
    def predict(self, request):
        serializer = PredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        patient_id = data.get("patient_id")
        if not patient_id:
            return Response(
                {"error": "patient_id is required so live readings remain isolated per patient."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        age = data.get("age")
        gender = data.get("gender")
        patient = None
        from patients.models import Patient
        try:
            patient = Patient.objects.get(patient_id=patient_id)
            if age is None:
                age = patient.age
            if gender is None:
                gender = patient.gender
        except Patient.DoesNotExist:
            if age is None or gender is None:
                return Response(
                    {"error": "Provide age and gender, or create the patient record first."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        predictor = load_predictor()
        if not predictor.is_ready:
            return Response(
                {
                    "error": "ML model is not ready. Retrain using the current ambulance feature schema.",
                    "model_status": predictor.health(),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            result = predictor.add_vital_signs(
                patient_key=patient_id,
                heart_rate=data.get("heart_rate"),
                temperature=data.get("temperature"),
                sbp=data.get("sbp"),
                dbp=data.get("dbp"),
                respiratory_rate=data.get("respiratory_rate"),
                age=age,
                gender=gender,
                map_value=data.get("map_value"),
            )
        except ModelNotReadyError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            # Never fabricate a LOW-risk result when inference fails.
            return Response(
                {"error": "Prediction failed. No risk result is available."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if patient is not None:
            saved = RiskPrediction.objects.create(
                patient=patient,
                probability=result["risk_probability"],
                risk_level=result["risk_level"],
                model_version=result.get("model_name") or "unknown",
                heart_rate=data.get("heart_rate"),
                temperature=data.get("temperature"),
                sbp=data.get("sbp"),
                dbp=data.get("dbp"),
                respiratory_rate=data.get("respiratory_rate"),
            )
            result["prediction_id"] = saved.id

        return Response(result, status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=False)
    def reset(self, request):
        patient_id = request.data.get("patient_id")
        predictor = load_predictor()
        predictor.reset_history(patient_id if patient_id else None)
        return Response({
            "status": "history_reset",
            "scope": "patient" if patient_id else "all in-memory patient histories",
        })

    @action(methods=["GET"], detail=False)
    def health(self, request):
        predictor = load_predictor()
        payload = predictor.health()
        http_status = status.HTTP_200_OK if payload["model_loaded"] else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http_status)

    @action(methods=["POST"], detail=False)
    def record_risk(self, request):
        from patients.models import Patient
        patient_id = request.data.get("patient_id")
        if not patient_id:
            return Response({"error": "patient_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = Patient.objects.get(patient_id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = RiskPredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        saved = serializer.save(patient=patient)
        return Response(RiskPredictionSerializer(saved).data, status=status.HTTP_201_CREATED)
