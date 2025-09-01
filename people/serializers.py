from rest_framework import serializers
from .models import Teacher, Staff, Student,PrincipalList, PresidentList
from institution.utils.image_compressor import compress_image



class TeacherSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'], max_size_kb=200)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'], max_size_kb=200)
        return super().update(instance, validated_data)
    
    class Meta:
        model = Teacher
        fields = '__all__'



class StaffSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'], max_size_kb=200)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'], max_size_kb=200)
        return super().update(instance, validated_data)
    
    class Meta:
        model = Staff
        fields = '__all__'



class StudentSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'], max_size_kb=200)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'], max_size_kb=200)
        return super().update(instance, validated_data)
    
    class Meta:
        model = Student
        fields = '__all__' 





class PrincipalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrincipalList
        fields = '__all__'



class PresidentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresidentList
        fields = '__all__'