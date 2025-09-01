from django.shortcuts import render
from rest_framework import viewsets
from .models import Teacher, Staff, Student,PrincipalList
from .serializers import *
# Create your views here.

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class PrincipalListViewSet(viewsets.ModelViewSet):
    queryset = PrincipalList.objects.all()
    serializer_class = PrincipalListSerializer
    ordering = ['-to_date'] 


class PresidentListViewSet(viewsets.ModelViewSet):
    queryset = PresidentList.objects.all()
    serializer_class = PresidentListSerializer
    ordering = ['-to_date']
