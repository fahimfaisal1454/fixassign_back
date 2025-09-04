# academics/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import ClassRoutine, ExamRoutine, Syllabus, Result, Routine
from .serializers import (
    ClassRoutineSerializer,
    ExamRoutineSerializer,
    SyllabusSerializer,
    ResultSerializer,
    RoutineSerializer,
)

from people.models import Student
from people.serializers import StudentMiniSerializer  # use slim serializer for teacher views

# Reuse your IsAdmin permission from authentication app
try:
    from authentication.views import IsAdmin  # preferred if available
except Exception:
    from rest_framework.permissions import BasePermission
    class IsAdmin(BasePermission):
        def has_permission(self, request, view):
            return bool(
                request.user
                and request.user.is_authenticated
                and getattr(request.user, "role", "").lower() == "admin"
            )


class ClassRoutineViewSet(viewsets.ModelViewSet):
    """
    CRUD for class routines.
    - Admin can create/update/delete/assign-teacher
    - Authenticated users can read
    """
    queryset = ClassRoutine.objects.select_related("class_name", "subject", "teacher").all()
    serializer_class = ClassRoutineSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Admin can mutate data; others read-only
        if self.action in ["create", "update", "partial_update", "destroy", "assign_teacher"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    # -------------------------
    # Admin: assign a teacher
    # -------------------------
    @action(detail=True, methods=["patch"], url_path="assign-teacher")
    def assign_teacher(self, request, pk=None):
        """
        PATCH /api/class-routines/<id>/assign-teacher/
        body: { "teacher": <user_id or null> }
        """
        routine = self.get_object()
        teacher_id = request.data.get("teacher", None)
        data = {"teacher": teacher_id}  # DRF handles PK or null
        ser = self.get_serializer(routine, data=data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_200_OK)

    # -------------------------
    # Teacher: my timetable
    # -------------------------
    @action(detail=False, methods=["get"], url_path="my-classes")
    def my_classes(self, request):
        """
        GET /api/class-routines/my-classes/?day=Mon&class=Class 7&class_id=3&section=A&subject=Math&subject_id=5
        """
        me = request.user
        if not me or not me.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        qs = self.queryset.filter(teacher=me)

        day = request.query_params.get("day")
        class_name = request.query_params.get("class")
        class_id = request.query_params.get("class_id")
        section = request.query_params.get("section")
        subject = request.query_params.get("subject")
        subject_id = request.query_params.get("subject_id")

        if day:
            qs = qs.filter(day_of_week__iexact=day)
        if class_id:
            qs = qs.filter(class_name_id=class_id)
        elif class_name:
            qs = qs.filter(class_name__name=class_name)
        if section:
            qs = qs.filter(section__iexact=section)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        elif subject:
            qs = qs.filter(subject__name__iexact=subject)

        qs = qs.order_by("day_of_week", "start_time")
        data = self.get_serializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    # -------------------------
    # Teacher: my students
    # -------------------------
    @action(detail=False, methods=["get"], url_path="my-students")
    def my_students(self, request):
        """
        GET /api/class-routines/my-students/?class=Class 7&class_id=3&section=A&subject=Math&subject_id=5&day=Mon

        Returns students for all class-sections this teacher teaches,
        optionally narrowed by the provided filters.

        Note: Student.class_name is CharField, so we match against
        ClassRoutine.class_name.name (string), not the FK id.
        """
        me = request.user
        if not me or not me.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        qs = self.queryset.filter(teacher=me)

        class_name = request.query_params.get("class")
        class_id = request.query_params.get("class_id")
        section = request.query_params.get("section")
        subject = request.query_params.get("subject")
        subject_id = request.query_params.get("subject_id")
        day = request.query_params.get("day")

        if day:
            qs = qs.filter(day_of_week__iexact=day)
        if class_id:
            qs = qs.filter(class_name_id=class_id)
        elif class_name:
            qs = qs.filter(class_name__name=class_name)
        if section:
            qs = qs.filter(section__iexact=section)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        elif subject:
            qs = qs.filter(subject__name__iexact=subject)

        # Distinct (class_name string, section) pairs for this teacher
        pairs = qs.values_list("class_name__name", "section").distinct()
        if not pairs:
            return Response([], status=status.HTTP_200_OK)

        # Build OR filter for Students in those (class_name string, section) pairs
        student_q = Q()
        for class_name_str, sec in pairs:
            if sec:
                student_q |= Q(class_name__iexact=class_name_str, section__iexact=sec)
            else:
                student_q |= Q(class_name__iexact=class_name_str)

        students_qs = Student.objects.filter(student_q)
        # Nice ordering
        if hasattr(Student, "full_name"):
            students_qs = students_qs.order_by("class_name", "section", "full_name")
        else:
            students_qs = students_qs.order_by("class_name", "section", "id")

        return Response(StudentMiniSerializer(students_qs, many=True).data, status=status.HTTP_200_OK)


class ExamRoutineViewSet(viewsets.ModelViewSet):
    queryset = ExamRoutine.objects.all()
    serializer_class = ExamRoutineSerializer
    permission_classes = [IsAuthenticated]


class SyllabusViewSet(viewsets.ModelViewSet):
    queryset = Syllabus.objects.all()
    serializer_class = SyllabusSerializer
    permission_classes = [IsAuthenticated]


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]


class RoutineViewSet(viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer
    permission_classes = [IsAuthenticated]
