from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem, AttendanceRecord,
    GradeScale, GradeBand, Exam, ExamMark, Assignment,
)
from master.models import ClassName, Section, Subject

# If your Teacher model lives elsewhere, update the dotted path below.
from people.models import Teacher,Student 



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
    # labels for UI (unchanged)
    class_name_label    = serializers.CharField(source="class_name.name", read_only=True)
    section_label       = serializers.CharField(source="section.name", read_only=True)
    subject_label       = serializers.CharField(source="subject.name", read_only=True)
    teacher_label       = serializers.CharField(source="teacher.__str__", read_only=True)
    classroom_label     = serializers.CharField(source="classroom.name", read_only=True)
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)

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

    # ✅ NEW: capacity enforcement
    def validate(self, attrs):
        """
        Block save if classroom capacity < class size.
        (capacity None/0/negative = unlimited)
        Works for POST and PATCH.
        """
        instance   = getattr(self, "instance", None)
        class_name = attrs.get("class_name") or getattr(instance, "class_name", None)
        section    = attrs.get("section")    or getattr(instance, "section", None)
        classroom  = attrs.get("classroom")  or getattr(instance, "classroom", None)

        if class_name and section and classroom:
            cap = getattr(classroom, "capacity", None)
            if cap and cap > 0:
                size = Student.objects.filter(class_name=class_name, section=section).count()
                if size > cap:
                    raise serializers.ValidationError({
                        "classroom": (
                            f"Room capacity ({cap}) is less than class size ({size}). "
                            f"Select a larger room or split the section."
                        )
                    })
        return attrs

    # unchanged
    def _full_clean_or_raise(self, instance):
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict or e.messages)

    # unchanged
    def create(self, validated_data):
        instance = TimetableEntry(**validated_data)
        self._full_clean_or_raise(instance)
        instance.save()
        return instance

    # unchanged
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
    


class GradeBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeBand
        fields = "__all__"


class GradeScaleSerializer(serializers.ModelSerializer):
    bands = GradeBandSerializer(many=True, read_only=True)

    class Meta:
        model = GradeScale
        fields = ["id", "name", "is_active", "bands"]


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = "__all__"


class ExamMarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    exam_name = serializers.CharField(source="exam.name", read_only=True)

    class Meta:
        model = ExamMark
        fields = [
            "id",
            "exam", "exam_name",
            "student", "student_name",
            "subject", "subject_name",
            "score", "gpa", "letter",
        ]
        read_only_fields = ["gpa", "letter"]

    def validate(self, attrs):
        """
        Restrict teachers to enter marks only for subjects/classes they teach.
        Admin/staff can bypass.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        exam = attrs.get("exam") or getattr(self.instance, "exam", None)
        subject = attrs.get("subject") or getattr(self.instance, "subject", None)

        if not (exam and subject) or not user:
            return attrs

        if not (user.is_superuser or user.is_staff):
            teacher = Teacher.objects.filter(user=user).first()
            if teacher:
                ok = TimetableEntry.objects.filter(
                    teacher=teacher,
                    class_name=exam.class_name,
                    section=exam.section,
                    subject=subject,
                ).exists()
                if not ok:
                    raise serializers.ValidationError(
                        "You can only enter marks for your assigned subject/class/section."
                    )
        return attrs  
    
#_─────────────────────────────────────────────────────────────────────────────
class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = "__all__"
        read_only_fields = ("teacher", "created_at")

    # accept either numeric id or a name like "A" / "Bangla"
    def _coerce_fk(self, Model, value, name_fields=("name","title","code","subject_name","section_name","class_name")):
        if value in (None, ""):
            raise serializers.ValidationError(f"Missing {Model.__name__}")
        # try pk
        try:
            return Model.objects.get(pk=int(value))
        except (ValueError, TypeError, Model.DoesNotExist):
            pass
        # try by name-ish fields
        for f in name_fields:
            try:
                return Model.objects.get(**{f: value})
            except Model.DoesNotExist:
                continue
        raise serializers.ValidationError(f"{Model.__name__} not found for '{value}'")

    def create(self, validated_data):
        req = self.context["request"]
        data = req.data  # raw incoming values

        # coerce FKs from id OR label
        validated_data["class_name"] = self._coerce_fk(ClassName, data.get("class_name"))
        validated_data["section"]    = self._coerce_fk(Section,   data.get("section"))
        validated_data["subject"]    = self._coerce_fk(Subject,   data.get("subject"))

        # attach teacher automatically
        validated_data["teacher"] = req.user.teacher
        return super().create(validated_data)