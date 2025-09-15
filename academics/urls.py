from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ClassNameViewSet, 
    PeriodViewSet, ClassroomViewSet, TimetableEntryViewSet,
    ExamRoutineViewSet, SyllabusViewSet, ResultViewSet, RoutineViewSet,
    GalleryItemViewSet
)

router = DefaultRouter()

# Lookups for frontend
router.register(r"class-names", ClassNameViewSet, basename="class-name")



# Core academic endpoints
router.register(r"periods", PeriodViewSet, basename="period")
router.register(r"rooms", ClassroomViewSet, basename="room")
router.register(r"timetable", TimetableEntryViewSet, basename="timetable")
router.register(r"class-routines", TimetableEntryViewSet, basename="class-routine")

# Optional: supporting models
router.register(r"exam-routines", ExamRoutineViewSet, basename="exam-routine")
router.register(r"syllabus", SyllabusViewSet, basename="syllabus")
router.register(r"results", ResultViewSet, basename="result")
router.register(r"routines", RoutineViewSet, basename="routine")
router.register(r"gallery", GalleryItemViewSet, basename="gallery")

urlpatterns = [
    path("", include(router.urls)),
]
