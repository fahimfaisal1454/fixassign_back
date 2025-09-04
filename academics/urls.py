from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ClassRoutineViewSet,
    ExamRoutineViewSet,
    SyllabusViewSet,
    ResultViewSet,
    RoutineViewSet,
)

router = DefaultRouter()
router.register(r'class-routines', ClassRoutineViewSet, basename='class-routine')
router.register(r'exam-routines', ExamRoutineViewSet, basename='exam-routine')
router.register(r'syllabus', SyllabusViewSet, basename='syllabus')
router.register(r'results', ResultViewSet, basename='result')
router.register(r'routines', RoutineViewSet, basename='routine')

urlpatterns = [
    path('', include(router.urls)),
]
