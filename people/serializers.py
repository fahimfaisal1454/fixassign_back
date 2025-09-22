# people/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Teacher, Staff, Student, PrincipalList, PresidentList
from institution.utils.image_compressor import compress_image

User = get_user_model()


class TeacherSerializer(serializers.ModelSerializer):
    # Write: pass a User id to link/unlink (null to unlink)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        required=False,
        allow_null=True,
    )
    # Read: show username if linked
    user_username = serializers.SerializerMethodField()

    def get_user_username(self, obj):
        return getattr(obj.user, "username", None)

    def create(self, validated_data):
        if "photo" in validated_data and validated_data["photo"]:
            validated_data["photo"] = compress_image(validated_data["photo"], max_size_kb=200)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "photo" in validated_data and validated_data["photo"]:
            validated_data["photo"] = compress_image(validated_data["photo"], max_size_kb=200)
        return super().update(instance, validated_data)

    class Meta:
        model = Teacher
        fields = "__all__"  # includes user_id & user_username via extra fields above



class StudentMiniSerializer(serializers.ModelSerializer):
    """Slim serializer for teacher views (attendance, student list, etc.)"""
    class_name_label = serializers.CharField(source="class_name.name", read_only=True)
    section_label    = serializers.CharField(source="section.name", read_only=True)
    # Optional: include contacts if you want them in list endpoints too
    contact_email    = serializers.EmailField(read_only=True, required=False, allow_blank=True)
    contact_phone    = serializers.CharField(read_only=True, required=False, allow_blank=True)

    class Meta:
        model = Student
        fields = [
            "id", "full_name", "roll_number",
            "class_name", "section", "photo",
            "class_name_label", "section_label",
            # optional extras:
            "contact_email", "contact_phone",
        ]



class StaffSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if "photo" in validated_data and validated_data["photo"]:
            validated_data["photo"] = compress_image(validated_data["photo"], max_size_kb=200)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "photo" in validated_data and validated_data["photo"]:
            validated_data["photo"] = compress_image(validated_data["photo"], max_size_kb=200)
        return super().update(instance, validated_data)

    class Meta:
        model = Staff
        fields = "__all__"


class StudentSerializer(serializers.ModelSerializer):
    class_name_label = serializers.CharField(source="class_name.name", read_only=True)
    section_label    = serializers.CharField(source="section.name", read_only=True)

    # ✅ make these writable and optional so PUT/PATCH works
    contact_email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Student
        fields = [
            "id", "full_name", "gender", "date_of_birth",
            "class_name", "section", "class_name_label", "section_label",
            "roll_number", "admission_no",
            "guardian_name", "guardian_phone", "address", "photo",
            "contact_email", "contact_phone",   # <-- added
            "user", "created_at",
        ]
        read_only_fields = ["created_at"]


class PrincipalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrincipalList
        fields = "__all__"


class PresidentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresidentList
        fields = "__all__"
