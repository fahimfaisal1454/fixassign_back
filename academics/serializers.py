from rest_framework import serializers
from .models import *



class ClassRoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoutine
        fields = '__all__'



class ExamRoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamRoutine
        fields = '__all__'



class SyllabusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Syllabus
        fields = '__all__'



class ResultSerializer(serializers.ModelSerializer):
    className = serializers.CharField(source='class_name.name', read_only=True)

    class Meta:
        model = Result
        fields = '__all__' 


class RoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Routine
        fields = '__all__'