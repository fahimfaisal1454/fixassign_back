from rest_framework import serializers
from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem
)
from master.models import ClassName, Section, Subject


# ── Core ─────────────────────────────────────────────────────────────────────

class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ["id", "name", "order", "start_time", "end_time"]


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ["id", "name", "capacity"]


class TimetableEntrySerializer(serializers.ModelSerializer):
    # writable FKs (frontend will send IDs directly)
    class_name = serializers.PrimaryKeyRelatedField(queryset=ClassName.objects.all())
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())

    # readable labels for UI
    class_name_label = serializers.CharField(source="class_name.name", read_only=True)
    section_label = serializers.CharField(source="section.name", read_only=True)
    subject_label = serializers.CharField(source="subject.name", read_only=True)

    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = TimetableEntry
        fields = [
            "id",
            "class_name", "class_name_label",
            "section", "section_label",
            "subject", "subject_label",
            "day_of_week", "day_of_week_display",
            "period",
            "start_time", "end_time",
            "created_at",
        ]
        read_only_fields = ["created_at"]


# ── Simple models ────────────────────────────────────────────────────────────

class ExamRoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamRoutine
        fields = "__all__"


class SyllabusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Syllabus
        fields = "__all__"


class ResultSerializer(serializers.ModelSerializer):
    className = serializers.CharField(source="class_name.name", read_only=True)

    class Meta:
        model = Result
        fields = "__all__"


class RoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Routine
        fields = "__all__"


class GalleryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryItem
        fields = ["id", "image", "caption", "uploaded_at"]
