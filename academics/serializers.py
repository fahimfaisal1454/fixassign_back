from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem, TeacherAssignment
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
    # writable FKs (frontend sends IDs)
    class_name = serializers.PrimaryKeyRelatedField(queryset=ClassName.objects.all())
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), required=False, allow_null=True
    )
    classroom = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(), required=False, allow_null=True
    )

    # readable labels for UI
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

            # writable FKs
            "class_name", "section", "subject", "teacher", "classroom",

            # readable labels
            "class_name_label", "section_label", "subject_label",
            "teacher_label", "classroom_label",

            "day_of_week", "day_of_week_display",
            "period",
            "start_time", "end_time",

            # legacy text room (optional; prefer classroom FK)
            "room",

            "created_at",
        ]
        read_only_fields = ["created_at"]

    # Ensure model-level clean() runs so conflicts return as DRF errors
    def _full_clean_or_raise(self, instance):
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            # Convert Django ValidationError to DRF ValidationError (field-wise if possible)
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



class TeacherAssignmentSerializer(serializers.ModelSerializer):
    # writable FKs
    class_name = serializers.PrimaryKeyRelatedField(queryset=ClassName.objects.all())
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all())

    # readable labels for UI
    class_name_label = serializers.CharField(source="class_name.name", read_only=True)
    section_label = serializers.CharField(source="section.name", read_only=True)
    subject_label = serializers.CharField(source="subject.name", read_only=True)
    teacher_label = serializers.CharField(source="teacher.full_name", read_only=True)
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)

    def get_teacher_label(self, obj):
        full = getattr(obj.teacher, "get_full_name", lambda: "")() or ""
        if full:
            return full
        # fallback to username/email
        return getattr(obj.teacher, "username", None) or getattr(obj.teacher, "email", None) or f"User #{obj.teacher_id}"

    class Meta:
        model = TeacherAssignment
        fields = [
            "id",
            "class_name", "class_name_label",
            "section", "section_label",
            "subject", "subject_label",
            "teacher", "teacher_label",
            "day_of_week", "day_of_week_display",
            "period",
            "room",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        """
        Extra server-side checks (fast fail with readable messages).
        DB constraints still protect at the database layer.
        """
        class_name = attrs.get("class_name") or getattr(self.instance, "class_name", None)
        section = attrs.get("section") or getattr(self.instance, "section", None)
        subject = attrs.get("subject") or getattr(self.instance, "subject", None)

        if subject and class_name and getattr(subject, "class_name_id", None) != class_name.id:
            raise serializers.ValidationError({"subject": "Subject must belong to the selected class."})

        return attrs