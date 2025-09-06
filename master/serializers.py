from rest_framework import serializers
from .models import ClassName, Subject, GalleryItem, Banner, Section
from institution.utils.image_compressor import compress_image

# ---------- NEW ----------
class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name"]
# -------------------------

class ClassNameSerializer(serializers.ModelSerializer):
    # Accept IDs from the client
    sections = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Section.objects.all(), required=False
    )
    # Nice read-only detail for table
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

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"

class GalleryItemSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'image' in validated_data:
            validated_data['image'] = compress_image(validated_data['image'], max_size_kb=100)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            validated_data['image'] = compress_image(validated_data['image'], max_size_kb=100)
        return super().update(instance, validated_data)

    class Meta:
        model = GalleryItem
        fields = "__all__"

class BannerItemSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'image' in validated_data:
            validated_data['image'] = compress_image(validated_data['image'], max_size_kb=800)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            validated_data['image'] = compress_image(validated_data['image'], max_size_kb=800)
        return super().update(instance, validated_data)

    class Meta:
        model = Banner
        fields = "__all__"
