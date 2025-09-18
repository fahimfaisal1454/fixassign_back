from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem, AttendanceRecord
)
from master.models import ClassName, Section, Subject

# If your Teacher model lives elsewhere, update the dotted path below.
from people.models import Teacher



User = get_user_model()
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
    # labels for UI
    class_name_label = serializers.CharField(source="class_name.name", read_only=True)
    section_label = serializers.CharField(source="section.name", read_only=True)
    subject_label = serializers.CharField(source="subject.name", read_only=True)
    teacher_label = serializers.CharField(source="teacher.__str__", read_only=True)
    classroom_label = serializers.CharField(source="classroom.name", read_only=True)
    day_of_week_display = serializers.CharField(
        source="get_day_of_week_display", read_only=True
    )

    class Meta:
        model = TimetableEntry
        fields = [
            "id",
            "class_name", "class_name_label",
            "section", "section_label",
            "subject", "subject_label",
            "teacher", "teacher_label",
            "classroom", "classroom_label",
            "day_of_week", "day_of_week_display",
            "period",
            "start_time", "end_time",
        ]

    def _full_clean_or_raise(self, instance):
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict or e.messages)

    def create(self, validated_data):
        instance = TimetableEntry(**validated_data)
        self._full_clean_or_raise(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        self._full_clean_or_raise(instance)
        instance.save()
        return instance


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



class AttendanceRecordSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="timetable.class_name.name", read_only=True)
    section = serializers.CharField(source="timetable.section.name", read_only=True)
    subject = serializers.CharField(source="timetable.subject.name", read_only=True)
    
    class_id = serializers.IntegerField(source="timetable.class_name_id", read_only=True)
    section_id = serializers.IntegerField(source="timetable.section_id", read_only=True)
    subject_id = serializers.IntegerField(source="timetable.subject_id", read_only=True)
    
    teacher = serializers.CharField(source="timetable.teacher.__str__", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
            model = AttendanceRecord
            fields = [
                "id", "date", "status", "remarks",
                "timetable",
                "class_id", "class_name",
                "section_id", "section",
                "subject_id", "subject",
                "teacher",
                "student", "student_name",
                "marked_by", "marked_at",
            ]
            read_only_fields = [
                "marked_by", "marked_at",
                "class_id", "class_name",
                "section_id", "section",
                "subject_id", "subject",
                "teacher", "student_name",
            ]


    def validate(self, attrs):
        request = self.context["request"]
        # handle create vs update safely
        timetable = attrs.get("timetable") or (self.instance.timetable if getattr(self, "instance", None) else None)

        if not request.user.is_superuser:
            teacher = getattr(timetable, "teacher", None) if timetable else None
            if not teacher or teacher.user_id != request.user.id:
                raise serializers.ValidationError("You are not allowed to mark attendance for this class.")
        return attrs

    def create(self, validated_data):
        validated_data["marked_by"] = self.context["request"].user
        return super().create(validated_data)