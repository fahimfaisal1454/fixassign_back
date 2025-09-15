from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem, 
)
from .serializers import (
    PeriodSerializer, ClassroomSerializer, TimetableEntrySerializer,
    ExamRoutineSerializer, SyllabusSerializer, ResultSerializer, RoutineSerializer,
    GalleryItemSerializer
)
from master.models import ClassName, Subject
from people.models import Student, Teacher

# ─────────────────────────────────────────────────────────────────────────────
# Lightweight lookups for frontend (classes & subjects)
# ─────────────────────────────────────────────────────────────────────────────

class ClassNameMiniSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()

    class Meta:
        model = ClassName
        fields = ["id", "name", "sections"]

    def get_sections(self, obj):
        # Expecting a related_name like .sections
        return [{"id": s.id, "name": s.name} for s in obj.sections.all()]


class ClassNameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClassName.objects.all().order_by("name")
    serializer_class = ClassNameMiniSerializer


class SubjectMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "class_name"]


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/subjects/?class_id=ID  (preferred)
    /api/subjects/?class=ID     (fallback)
    """
    serializer_class = SubjectMiniSerializer

    def get_queryset(self):
        qs = Subject.objects.select_related("class_name").all().order_by("name")
        class_id = self.request.query_params.get("class") or self.request.query_params.get("class_id")
        if class_id:
            qs = qs.filter(class_name_id=class_id)
        return qs


# ─────────────────────────────────────────────────────────────────────────────
# Core CRUD endpointsssssss
# ─────────────────────────────────────────────────────────────────────────────

class PeriodViewSet(viewsets.ModelViewSet):
    queryset = Period.objects.all().order_by("order")
    serializer_class = PeriodSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all().order_by("name")
    serializer_class = ClassroomSerializer


class TimetableEntryViewSet(viewsets.ModelViewSet):
    """
    /api/timetable/
      ?class_name=   (ClassName pk)
      &section=      (Section pk)
      &subject=      (Subject pk)
      &teacher_id=   (Teacher pk)
      &day_of_week=  (Mon|Tue|...)
      &classroom=    (Classroom pk)
      &student=me    (auto filter by logged-in student's class & section)
      &teacher=me    (auto filter by logged-in teacher)

    Extra endpoint:
      /api/timetable/week?[filters]
        → returns entries grouped by day (Mon–Sun)
    """
    queryset = (
        TimetableEntry.objects
        .select_related("class_name", "section", "subject", "teacher", "classroom")
        .all()
    )
    serializer_class = TimetableEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params

        # Accept both new + old param names
        class_name = q.get("class_name") or q.get("class_id")
        section = q.get("section") or q.get("section_id")
        subject_id = q.get("subject") or q.get("subject_id")
        teacher_id = q.get("teacher_id") or q.get("teacher")
        day = q.get("day_of_week") or q.get("day")
        classroom_id = q.get("classroom") or q.get("classroom_id")

        if class_name:
            qs = qs.filter(class_name_id=class_name)
        if section:
            qs = qs.filter(section_id=section)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if teacher_id:
            if teacher_id == "me":
                teacher = Teacher.objects.filter(user=self.request.user).first()
                if not teacher:
                    return qs.none()
                qs = qs.filter(teacher=teacher)
            else:
                qs = qs.filter(teacher_id=teacher_id)
        if day:
            if day not in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}:
                return qs.none()
            qs = qs.filter(day_of_week=day)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        # student=me → filter by logged-in student's class & section
        if q.get("student") == "me":
            stu = Student.objects.filter(user=self.request.user).first()
            if not stu:
                return qs.none()
            qs = qs.filter(class_name=stu.class_name, section=stu.section)

        # 🔒 Default: if no teacher filter provided but logged-in user *is* a teacher
        if not teacher_id and not q.get("student"):
            teacher = Teacher.objects.filter(user=self.request.user).first()
            if teacher:
                qs = qs.filter(teacher=teacher)

        return qs.order_by("day_of_week", "start_time", "period")

    @action(detail=False, methods=["get"])
    def week(self, request):
        """
        GET /api/timetable/week?[filters]
        Returns entries grouped by day (Mon–Sun).
        Supports same filters as list().
        """
        entries = self.get_queryset()
        serializer = TimetableEntrySerializer(entries, many=True)

        # Prepare dict with all days
        data_by_day = {k: [] for k in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}

        for r in serializer.data:
            day_code = r.get("day_of_week")  # 'Mon' etc
            if day_code in data_by_day:
                data_by_day[day_code].append(r)

        # Sort entries within each day
        for k, v in data_by_day.items():
            data_by_day[k] = sorted(
                v,
                key=lambda r: (
                    (r.get("start_time") or ""),
                    (r.get("period") or ""),
                ),
            )

        return Response(data_by_day)

    
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


