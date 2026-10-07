from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .ml_predictor import load_predictor, predict_patient_standalone, reset_predictor
from .serializers import PredictionSerializer, PredictionResultSerializer, HealthCheckSerializer, RiskPredictionSerializer
from .models import RiskPrediction


class MLEngineViewSet(viewsets.ViewSet):
    """ML engine API endpoints."""
    
    @action(methods=["POST"], detail=False)
    def predict(self, request):
        """Run ML prediction on vital signs."""
        serializer = PredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        predictor = load_predictor()
        
        result = predict_patient_standalone(
            heart_rate=data["heart_rate"],
            temperature=data.get("temperature"),
            sbp=data["sbp"],
            dbp=data["dbp"],
            respiratory_rate=data["respiratory_rate"],
        )
        
        # Save prediction to database
        from patients.models import Patient
        patient_id = data.get("patient_id")
        if patient_id:
            try:
                patient = Patient.objects.get(patient_id=patient_id)
                from .models import RiskPrediction
                risk_pred = RiskPrediction.objects.create(
                    patient=patient,
                    probability=result["risk_probability"],
                    risk_level=result["risk_level"],
                    model_version="1.0",
                    heart_rate=data["heart_rate"],
                    temperature=data.get("temperature"),
                    sbp=data["sbp"],
                    dbp=data["dbp"],
                    respiratory_rate=data["respiratory_rate"],
                )
                result["prediction_id"] = risk_pred.id
            except Patient.DoesNotExist:
                pass
        
        return Response(result)
    
    @action(methods=["POST"], detail=False)
    def reset(self, request):
        """Reset patient history for new patient."""
        reset_predictor()
        return Response({"status": "history_reset"})
    
    @action(methods=["GET"], detail=False)
    def health(self, request):
        """ML system health check."""
        predictor = load_predictor()
        return Response({
            "model_loaded": predictor is not None and predictor.model is not None,
            "risk_thresholds": predictor.risk_thresholds if predictor else {},
        })
    
    @action(methods=["POST"], detail=False)
    def record_risk(self, request):
        """Record a risk prediction."""
        from patients.models import Patient
        patient_id = request.data.get("patient_id")
        if patient_id:
            try:
                patient = Patient.objects.get(patient_id=patient_id)
                from .models import RiskPrediction
                serializer = RiskPredictionSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(patient=patient)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Patient.DoesNotExist:
                pass
        return Response(
            {"error": "Patient not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
