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
    class Meta:
        model = Student
        fields = ["id", "full_name", "roll_number", "class_name", "section", "photo"]


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
    def create(self, validated_data):
        if "photo" in validated_data and validated_data["photo"]:
            validated_data["photo"] = compress_image(validated_data["photo"], max_size_kb=200)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "photo" in validated_data and validated_data["photo"]:
            validated_data["photo"] = compress_image(validated_data["photo"], max_size_kb=200)
        return super().update(instance, validated_data)

    class Meta:
        model = Student
        fields = "__all__"


class PrincipalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrincipalList
        fields = "__all__"


class PresidentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresidentList
        fields = "__all__"
