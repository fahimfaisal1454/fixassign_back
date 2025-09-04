from rest_framework import serializers
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import ClassRoutine, ExamRoutine, Syllabus, Result, Routine

User = get_user_model()


class ClassRoutineSerializer(serializers.ModelSerializer):
    # Helpful read-only labels for UI
    class_label = serializers.SerializerMethodField(read_only=True)
    subject_name = serializers.SerializerMethodField(read_only=True)
    teacher_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClassRoutine
        fields = [
            "id",
            "class_name",     # FK -> master.ClassName (send ID)
            "section",        # CharField
            "subject",        # FK -> master.Subject (send ID)
            "teacher",        # FK -> authentication.User (send ID or null)
            "day_of_week",
            "period",
            "start_time",
            "end_time",
            "class_label",    # read-only (e.g., "Class 7")
            "subject_name",   # read-only (e.g., "Math")
            "teacher_name",   # read-only (e.g., "t_rumana")
        ]

    # ---------- Read-only helpers ----------
    def get_class_label(self, obj):
        return str(obj.class_name) if obj.class_name else None

    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None

    def get_teacher_name(self, obj):
        return getattr(obj.teacher, "username", None)

    # ---------- Validation with conflict checks ----------
    def validate(self, attrs):
        """
        Rules:
        - end_time must be after start_time
        - teacher (if set) must have role 'Teacher'
        - Prevent teacher double-booking on the same day/time
        - Prevent class+section double-booking on the same day/time
        - (Optional) prevent subject duplication in the same slot for the same class-section
        """
        instance = getattr(self, "instance", None)

        # gather current/new values
        class_name = attrs.get("class_name") or (instance and instance.class_name)
        section    = (attrs.get("section") or (instance and instance.section) or "").strip()
        subject    = attrs.get("subject") or (instance and instance.subject)
        teacher    = attrs.get("teacher") or (instance and instance.teacher)
        day        = attrs.get("day_of_week") or (instance and instance.day_of_week)
        start      = attrs.get("start_time") or (instance and instance.start_time)
        end        = attrs.get("end_time") or (instance and instance.end_time)

        # basic time sanity
        if start and end and start >= end:
            raise serializers.ValidationError({"time": "end_time must be after start_time."})

        # teacher must be actually a Teacher (by role) if provided
        if teacher:
            role = (getattr(teacher, "role", "") or "").lower()
            if role != "teacher":
                raise serializers.ValidationError({"teacher": "Selected user is not a Teacher."})

        # build overlap query for same day
        # Overlap if: start < other.end AND end > other.start
        overlap_q = Q(day_of_week=day, start_time__lt=end, end_time__gt=start)

        # 1) teacher conflict
        if teacher:
            qs_t = ClassRoutine.objects.filter(overlap_q, teacher=teacher)
            if instance:
                qs_t = qs_t.exclude(pk=instance.pk)
            if qs_t.exists():
                raise serializers.ValidationError({"teacher": "Teacher has another class at this time."})

        # 2) class+section conflict
        if class_name is not None:
            qs_c = ClassRoutine.objects.filter(overlap_q, class_name=class_name, section=section)
            if instance:
                qs_c = qs_c.exclude(pk=instance.pk)
            if qs_c.exists():
                raise serializers.ValidationError({"class_section": "This class-section already has a class at this time."})

        # 3) (optional) same subject in same slot for same class+section
        if class_name is not None and subject is not None:
            qs_s = ClassRoutine.objects.filter(
                overlap_q, class_name=class_name, section=section, subject=subject
            )
            if instance:
                qs_s = qs_s.exclude(pk=instance.pk)
            if qs_s.exists():
                raise serializers.ValidationError({"subject": "This subject is already scheduled for this class-section at this time."})

        return attrs


class ExamRoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamRoutine
        fields = "__all__"


class SyllabusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Syllabus
        fields = "__all__"


class ResultSerializer(serializers.ModelSerializer):
    className = serializers.CharField(source='class_name.name', read_only=True)

    class Meta:
        model = Result
        fields = "__all__"


class RoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Routine
        fields = "__all__"
