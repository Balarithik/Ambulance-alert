from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import HospitalPreparation
from .serializers import HospitalPreparationSerializer


class HospitalPreparationViewSet(viewsets.ModelViewSet):
    """Hospital preparation / incoming patient management."""
    queryset = HospitalPreparation.objects.all()
    serializer_class = HospitalPreparationSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=True, methods=['POST'])
    def acknowledge(self, request, pk=None):
        """Hospital staff acknowledges incoming patient."""
        prep = self.get_object()
        prep.status = 'ACKNOWLEDGED'
        prep.acknowledged_by = request.data.get('acknowledged_by', 'Hospital Staff')
        prep.acknowledged_at = timezone.now()
        prep.save()
        return Response(self.get_serializer(prep).data)

    @action(detail=True, methods=['POST'])
    def update_status(self, request, pk=None):
        """Update preparation status (PREPARING / READY)."""
        prep = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(HospitalPreparation.STATUS_CHOICES):
            return Response(
                {'error': f'Invalid status. Valid: {[c[0] for c in HospitalPreparation.STATUS_CHOICES]}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        prep.status = new_status
        if request.data.get('notes'):
            prep.notes = request.data['notes']
        if request.data.get('required_preparation'):
            prep.required_preparation = request.data['required_preparation']
        prep.save()
        return Response(self.get_serializer(prep).data)

    @action(detail=False, methods=['GET'])
    def active(self, request):
        """Get all active (non-READY) incoming patients."""
        active_preps = self.queryset.exclude(status='READY')
        serializer = self.get_serializer(active_preps, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def history(self, request):
        """Get all completed preparations."""
        completed = self.queryset.filter(status='READY')
        serializer = self.get_serializer(completed, many=True)
        return Response(serializer.data)
