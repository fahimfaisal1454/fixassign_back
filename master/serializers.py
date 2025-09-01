from rest_framework import serializers
from .models import ClassName, Subject, GalleryItem, Banner
from institution.utils.image_compressor import compress_image


class ClassNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassName
        fields = '__all__'




class SubjectSerializer(serializers.ModelSerializer):
    serializers.PrimaryKeyRelatedField(queryset=ClassName.objects.all())

    class Meta:
        model = Subject
        fields = '__all__'



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
        fields = '__all__'




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
        fields = '__all__'
