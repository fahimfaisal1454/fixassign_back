# academics/views.py
from rest_framework import viewsets
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
from people.serializers import StudentSerializer


class ClassRoutineViewSet(viewsets.ModelViewSet):
    queryset = ClassRoutine.objects.all()
    serializer_class = ClassRoutineSerializer
    permission_classes = [IsAuthenticated]  # require login for these endpoints

    # GET /api/class-routines/my-classes/?day=&class=&section=&subject=
    @action(detail=False, methods=['get'], url_path='my-classes')
    def my_classes(self, request):
        me = getattr(request.user, 'username', None)
        if not me:
            return Response({'detail': 'Authentication required.'}, status=401)

        qs = self.queryset.filter(Q(teacher=me) | Q(teacher__iexact=me))

        day = request.query_params.get('day')
        clazz = request.query_params.get('class')
        section = request.query_params.get('section')
        subject = request.query_params.get('subject')

        if day:
            qs = qs.filter(day_of_week__iexact=day)
        if clazz:
            qs = qs.filter(class_name=clazz)
        if section:
            qs = qs.filter(section=section)
        if subject:
            qs = qs.filter(subject__iexact=subject)

        qs = qs.order_by('day_of_week', 'start_time')
        return Response(self.get_serializer(qs, many=True).data)

    # GET /api/class-routines/my-students/?class=&section=
    @action(detail=False, methods=['get'], url_path='my-students')
    def my_students(self, request):
        me = getattr(request.user, 'username', None)
        if not me:
            return Response({'detail': 'Authentication required.'}, status=401)

        routines = self.queryset.filter(Q(teacher=me) | Q(teacher__iexact=me))

        # Optional filters to narrow
        clazz = request.query_params.get('class')
        section = request.query_params.get('section')
        if clazz:
            routines = routines.filter(class_name=clazz)
        if section:
            routines = routines.filter(section=section)

        pairs = list(routines.values_list('class_name', 'section').distinct())
        if not pairs:
            return Response([])

        # Build OR conditions for (class_name, section) pairs
        q = Q()
        for c, s in pairs:
            if s:
                q |= Q(class_name=c, section=s)
            else:
                q |= Q(class_name=c)

        students_qs = Student.objects.filter(q).order_by('class_name', 'section', 'full_name')
        return Response(StudentSerializer(students_qs, many=True).data)


class ExamRoutineViewSet(viewsets.ModelViewSet):
    queryset = ExamRoutine.objects.all()
    serializer_class = ExamRoutineSerializer
    permission_classes = [IsAuthenticated]  # optional: enforce auth here too


class SyllabusViewSet(viewsets.ModelViewSet):
    queryset = Syllabus.objects.all()
    serializer_class = SyllabusSerializer
    permission_classes = [IsAuthenticated]  # optional


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]  # optional


class RoutineViewSet(viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer
    permission_classes = [IsAuthenticated]  # optional
