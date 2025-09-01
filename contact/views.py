from django.shortcuts import render
from rest_framework import viewsets
from .models import ContactInfo, Allegation
from .serializers import ContactInfoSerializer, AllegationSerializer

# Create your views here.

class ContactInfoViewSet(viewsets.ModelViewSet):
    queryset = ContactInfo.objects.all()
    serializer_class = ContactInfoSerializer

class AllegationViewSet(viewsets.ModelViewSet):
    queryset = Allegation.objects.all()
    serializer_class = AllegationSerializer
