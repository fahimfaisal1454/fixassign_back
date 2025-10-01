from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ClassNameViewSet, 
    PeriodViewSet, ClassroomViewSet, TimetableEntryViewSet,
    ExamRoutineViewSet, SyllabusViewSet, ResultViewSet, RoutineViewSet,
    GalleryItemViewSet, AttendanceViewSet, GradeScaleViewSet, GradeBandViewSet, ExamViewSet, ExamMarkViewSet,AssignmentViewSet
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
router.register(r"attendance", AttendanceViewSet, basename="attendance")
router.register("assignments", AssignmentViewSet, basename="assignments")


#exam
router.register(r"grade-scales", GradeScaleViewSet, basename="grade-scale")
router.register(r"grade-bands",  GradeBandViewSet,  basename="grade-band")
router.register(r"exams",        ExamViewSet,       basename="exam")
router.register(r"exam-marks",   ExamMarkViewSet,   basename="exam-mark")

urlpatterns = [
    path("", include(router.urls)),
]
