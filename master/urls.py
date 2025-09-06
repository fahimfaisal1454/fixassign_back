from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassNameViewSet, SubjectViewSet,
    SectionViewSet, ClassSubjectViewSet
)

router = DefaultRouter()
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'classes', ClassNameViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'class-subjects', ClassSubjectViewSet, basename='class-subject')

urlpatterns = [
    path('', include(router.urls)),
]
