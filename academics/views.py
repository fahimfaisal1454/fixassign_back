from django.shortcuts import render
from rest_framework import viewsets
from .models import *
from .serializers import *

# Create your views here.



class ClassRoutineViewSet(viewsets.ModelViewSet):
    queryset = ClassRoutine.objects.all()
    serializer_class = ClassRoutineSerializer



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
