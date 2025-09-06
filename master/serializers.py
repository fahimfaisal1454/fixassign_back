from rest_framework import serializers
from .models import ClassName, Subject, Section, ClassSubject


# -------- Sections --------
class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name"]


# -------- Classes --------
class ClassNameSerializer(serializers.ModelSerializer):
    # accept IDs from client
    sections = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Section.objects.all(), required=False
    )
    # nice read-only info for tables
    sections_detail = SectionSerializer(source="sections", many=True, read_only=True)

    class Meta:
        model = ClassName
        fields = ["id", "name", "sections", "sections_detail"]

    def create(self, validated_data):
        sections = validated_data.pop("sections", [])
        obj = ClassName.objects.create(**validated_data)
        if sections:
            obj.sections.set(sections)
        return obj

    def update(self, instance, validated_data):
        sections = validated_data.pop("sections", None)
        instance = super().update(instance, validated_data)
        if sections is not None:
            instance.sections.set(sections)
        return instance


# -------- Subjects --------
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "class_name", "is_theory", "is_practical"]


# -------- Assigned Subjects (ClassSubject) --------
class ClassSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSubject
        fields = [
            "id", "class_name", "section", "subject", "teacher",
            "is_compulsory", "order", "created_at"
        ]


class ClassSubjectListSerializer(serializers.ModelSerializer):
    # convenience fields for list/table
    section_name = serializers.CharField(source="section.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    is_theory = serializers.BooleanField(source="subject.is_theory", read_only=True)
    is_practical = serializers.BooleanField(source="subject.is_practical", read_only=True)

    class Meta:
        model = ClassSubject
        fields = [
            "id", "class_name", "section", "subject", "teacher",
            "is_compulsory", "order", "created_at",
            "section_name", "subject_name", "teacher_name",
            "is_theory", "is_practical",
        ]


# Payload for bulk assign endpoint
class BulkAssignPayloadSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    section_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    subject_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    teacher_id = serializers.IntegerField(required=False, allow_null=True)
