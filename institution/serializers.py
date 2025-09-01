from rest_framework import serializers
from .utils.image_compressor import compress_image
from .models import InstitutionInfo, PrincipalVicePrincipal, ManagingCommitteeMember, Notice


class InstitutionInfoSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'logo' in validated_data:
            validated_data['logo'] = compress_image(validated_data['logo'])
        if 'institution_image' in validated_data:
            validated_data['institution_image'] = compress_image(validated_data['institution_image'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'logo' in validated_data:
            validated_data['logo'] = compress_image(validated_data['logo'])
        if 'institution_image' in validated_data:
            validated_data['institution_image'] = compress_image(validated_data['institution_image'])
        return super().update(instance, validated_data)
    

    class Meta:
        model = InstitutionInfo
        fields = '__all__'



class PrincipalVicePrincipalSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        print("Compressing image...")
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'])
        return super().create(validated_data)
    

    def update(self, instance, validated_data):
        print("Compressing image...")
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'])
        return super().update(instance, validated_data)


    class Meta:
        model = PrincipalVicePrincipal
        fields = '__all__'

    
   

class ManagingCommitteeMemberSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'],max_size_kb=200)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = compress_image(validated_data['photo'], max_size_kb=200)
        return super().update(instance, validated_data)
    
    class Meta:
        model = ManagingCommitteeMember
        fields = '__all__' 



class NoticeSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if 'pdf_file' in validated_data:
            validated_data['pdf_file'] = compress_image(validated_data['pdf_file'])
        return super().create(validated_data)


    def update(self, instance, validated_data):
        if 'pdf_file' in validated_data:
            validated_data['pdf_file'] = compress_image(validated_data['pdf_file'])
        return super().update(instance, validated_data)

    class Meta:
        model = Notice
        fields = ['id', 'title', 'description','category', 'pdf_file', 'date']


    

