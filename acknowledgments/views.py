from rest_framework import viewsets, permissions, filters, parsers
from .models import Acknowledgment
from .serializers import AcknowledgmentSerializer

class AcknowledgmentViewSet(viewsets.ModelViewSet):
    queryset = Acknowledgment.objects.all()
    serializer_class = AcknowledgmentSerializer

    # If you want to limit who can write:
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Accept multipart/form-data for file uploads
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['date', 'created_at']

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def perform_update(self, serializer):
        """
        Support PATCH without requiring a new file:
        If no 'image' in request data, keep existing file.
        """
        partial = getattr(self, 'partial', False)
        if partial and 'image' not in self.request.data:
            serializer.partial = True
        serializer.save()
