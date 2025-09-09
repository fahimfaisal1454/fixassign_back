from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem, TeacherAssignment, 
)
from .serializers import (
    PeriodSerializer, ClassroomSerializer, TimetableEntrySerializer,
    ExamRoutineSerializer, SyllabusSerializer, ResultSerializer, RoutineSerializer,
    GalleryItemSerializer, TeacherAssignmentSerializer,
)
from master.models import ClassName, Subject
from people.models import Student

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
      ?class_id=     (ClassName pk)
      &section_id=   (Section pk)
      &subject_id=   (Subject pk)
      &teacher_id=   (Teacher pk)
      &day=Mon|Tue|...
      &student=me    (auto filter by logged-in student's class & section)
    """
    queryset = (
        TimetableEntry.objects
        .select_related("class_name", "section", "subject", "teacher", "classroom")
        .all()
    )
    serializer_class = TimetableEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params

        class_id = q.get("class_id")
        section_id = q.get("section_id")
        subject_id = q.get("subject_id")
        teacher_id = q.get("teacher_id")
        day = q.get("day") or q.get("day_of_week")
        room_name = q.get("room")
        classroom_id = q.get("classroom_id")

        if class_id:
            qs = qs.filter(class_name_id=class_id)
        if section_id:
            qs = qs.filter(section_id=section_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)
        if day:
            # Only accept valid 3-letter codes (Mon..Sun)
            if day not in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}:
                return qs.none()
            qs = qs.filter(day_of_week=day)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        if room_name:
            qs = qs.filter(room__iexact=room_name)

        # student=me → auto filter by logged-in student's class/section
        if q.get("student") == "me":
            stu = Student.objects.filter(user=self.request.user).first()
            if not stu:
                return qs.none()
            qs = qs.filter(class_name=stu.class_name, section=stu.section)

        return qs.order_by("day_of_week", "start_time", "period")

    @action(detail=False, methods=["get"])
    def week(self, request):
        """
        Return entries grouped by day (Mon–Sun) for the given filters.
        """
        entries = self.get_queryset()
        serializer = TimetableEntrySerializer(entries, many=True)

        # prepare dict with all days to keep order
        data_by_day = {k: [] for k in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}

        for r in serializer.data:
            label = r.get("day_of_week_display") or r.get("day_of_week")
            data_by_day.setdefault(label, []).append(r)

        # sort within each day
        for k in list(data_by_day.keys()):
            data_by_day[k] = sorted(
                data_by_day[k],
                key=lambda r: ((r.get("start_time") or ""), (r.get("period") or ""))
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


class TeacherAssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for assigning teachers to class/section/subject per day/period.
    """
    permission_classes = [IsAuthenticated]  # ensures request.user is real
    queryset = TeacherAssignment.objects.select_related(
        "class_name", "section", "subject", "teacher"
    ).all()
    serializer_class = TeacherAssignmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # simple filters for list/search
        class_id = self.request.query_params.get("class_id")
        section_id = self.request.query_params.get("section_id")
        subject_id = self.request.query_params.get("subject_id")
        teacher_id = self.request.query_params.get("teacher_id")
        day = self.request.query_params.get("day_of_week")
        period = self.request.query_params.get("period")

        if class_id:
            qs = qs.filter(class_name_id=class_id)
        if section_id:
            qs = qs.filter(section_id=section_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)
        if day:
            qs = qs.filter(day_of_week=day)
        if period:
            qs = qs.filter(period=period)

        return qs.order_by("day_of_week", "period", "class_name__name", "section__name")

    @action(detail=False, methods=["get"], url_path="my-class")
    def my_class(self, request):
        """
        Return only the classes for the currently logged-in teacher.
        """
        teacher = getattr(request.user, "teacher_profile", None)  # <- linked Teacher profile
        if not teacher:
            return Response([], status=200)  # not linked yet: empty list
        qs = self.get_queryset().filter(teacher_id=teacher.id)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def week(self, request):
        """
        Grouped view by day for a given set of filters.
        """
        data = {}
        for entry in self.get_queryset():
            day = entry.get_day_of_week_display()
            data.setdefault(day, []).append(self.get_serializer(entry).data)
        return Response(data)