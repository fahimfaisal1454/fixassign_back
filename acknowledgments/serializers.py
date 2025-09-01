from rest_framework import serializers
from .models import Acknowledgment

class AcknowledgmentSerializer(serializers.ModelSerializer):
    image = serializers.FileField(required=False)

    class Meta:
        model = Acknowledgment
        fields = ['id', 'title', 'image', 'date', 'created_at']

    def validate_image(self, f):
        # Accept images or PDFs only; size guard optional
        content_type = getattr(f, 'content_type', '') or ''
        if not (content_type.startswith('image/') or content_type == 'application/pdf'):
            raise serializers.ValidationError('Only image or PDF files are allowed.')
        # e.g., 10 MB limit
        if f.size and f.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('File too large (max 10MB).')
        return f

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and data.get('image'):
            # ensure absolute URL for frontend
            data['image'] = request.build_absolute_uri(instance.image.url)
        return data
