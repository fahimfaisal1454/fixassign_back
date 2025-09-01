from rest_framework import serializers
from .models import ContactInfo, Allegation

class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = '__all__'

class AllegationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allegation
        fields = '__all__' 