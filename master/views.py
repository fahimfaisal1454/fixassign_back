from rest_framework import viewsets
from .models import ClassName, Subject, GalleryItem, Banner, Section
from .serializers import (
    ClassNameSerializer, SubjectSerializer,
    GalleryItemSerializer, BannerItemSerializer,
    SectionSerializer
)

# ---------- NEW ----------
class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all().order_by("name")
    serializer_class = SectionSerializer
# -------------------------

class ClassNameViewSet(viewsets.ModelViewSet):
    queryset = ClassName.objects.all().order_by("name")
    serializer_class = ClassNameSerializer

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class GalleryItemViewSet(viewsets.ModelViewSet):
    queryset = GalleryItem.objects.all().order_by('-created_at')
    serializer_class = GalleryItemSerializer

class BannerItemViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all().order_by('-created_at')[:4]
    serializer_class = BannerItemSerializer
