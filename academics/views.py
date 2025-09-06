from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Period, Classroom, TimetableEntry, ExamRoutine, Syllabus, Result, Routine, GalleryItem
from .serializers import (
    PeriodSerializer, ClassroomSerializer, TimetableEntrySerializer,
    ExamRoutineSerializer, SyllabusSerializer, ResultSerializer, RoutineSerializer,
    GalleryItemSerializer
)
from master.models import ClassName, Subject


# ─────────────────────────────────────────────────────────────────────────────
# Extra endpoints for ClassName & Subject (lightweight lookups for frontend)
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import serializers


class ClassNameMiniSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()

    class Meta:
        model = ClassName
        fields = ["id", "name", "sections"]

    def get_sections(self, obj):
        return [{"id": s.id, "name": s.name} for s in obj.sections.all()]


class ClassNameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClassName.objects.all().order_by("name")
    serializer_class = ClassNameMiniSerializer


class SubjectMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubjectMiniSerializer

    def get_queryset(self):
        qs = Subject.objects.select_related("class_name").all().order_by("name")
        class_id = self.request.query_params.get("class") or self.request.query_params.get("class_id")
        if class_id:
            qs = qs.filter(class_name_id=class_id)
        return qs


# ─────────────────────────────────────────────────────────────────────────────
# Core CRUD endpoints
# ─────────────────────────────────────────────────────────────────────────────

class PeriodViewSet(viewsets.ModelViewSet):
    queryset = Period.objects.all().order_by("order")
    serializer_class = PeriodSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all().order_by("name")
    serializer_class = ClassroomSerializer


class TimetableEntryViewSet(viewsets.ModelViewSet):
    queryset = TimetableEntry.objects.select_related("class_name", "section", "subject").all()
    serializer_class = TimetableEntrySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        class_id = self.request.query_params.get("class_id")
        section_id = self.request.query_params.get("section_id")
        subject_id = self.request.query_params.get("subject_id")
        day = self.request.query_params.get("day_of_week")

        if class_id:
            qs = qs.filter(class_name_id=class_id)
        if section_id:
            qs = qs.filter(section_id=section_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if day:
            qs = qs.filter(day_of_week=day)

        return qs.order_by("day_of_week", "period")

    @action(detail=False, methods=["get"])
    def week(self, request):
        """
        Return the whole week grouped by day for a given class/section/subject.
        Query params: class_id, section_id, subject_id
        """
        data = {}
        for entry in self.get_queryset():
            day = entry.get_day_of_week_display()
            data.setdefault(day, []).append(TimetableEntrySerializer(entry).data)
        return Response(data)


class ExamRoutineViewSet(viewsets.ModelViewSet):
    queryset = ExamRoutine.objects.all()
    serializer_class = ExamRoutineSerializer


class SyllabusViewSet(viewsets.ModelViewSet):
    queryset = Syllabus.objects.all()
    serializer_class = SyllabusSerializer


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class RoutineViewSet(viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer


class GalleryItemViewSet(viewsets.ModelViewSet):
    queryset = GalleryItem.objects.all().order_by("-uploaded_at")
    serializer_class = GalleryItemSerializer
