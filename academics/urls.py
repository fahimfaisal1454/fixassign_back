from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'class-routines', ClassRoutineViewSet)
router.register(r'exam-routines', ExamRoutineViewSet)
router.register(r'syllabus', SyllabusViewSet)
router.register(r'results', ResultViewSet)
router.register(r'routines', RoutineViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 