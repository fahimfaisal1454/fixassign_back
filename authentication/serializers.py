from rest_framework import serializers
from .models import*
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import password_validation
import json
from django.contrib.auth import get_user_model




class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = get_user_model()
        fields = ('username', 'profile_picture', 'email', 'password', 'confirm_password', 'phone')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Password doesn't match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        User = get_user_model()
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            phone=validated_data.get('phone')  # Assign phone field
        )
        if 'profile_picture' in validated_data:
            user.profile_picture = validated_data['profile_picture']
        user.is_approved = False
        user.save()
        return user





class StaffApproveSerializer(serializers.ModelSerializer):
    """
    Used by admin to view/update users.
    We use `is_active` as the approval toggle.
    """
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active", "phone", "profile_picture"]
        read_only_fields = ["id", "username", "email"]  # adjust if you want these editable

    def update(self, instance, validated_data):
        # Nothing special needed; DRF will set is_active/role/etc.
        return super().update(instance, validated_data)




class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # If you want to block unapproved accounts, uncomment:
        # if hasattr(user, "is_approved") and not user.is_approved:
        #     raise AuthenticationFailed("User not approved by admin.")
        data["role"] = getattr(user, "role", None)
        data["username"] = user.username
        return data




class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context['request'].user  # Get the logged-in user
        print(f"Stored password hash: {user.password}")  # Log the stored password hash

        print(f"User: {user.username}, Current Password: {data['current_password']}")
        if isinstance(data, str):
                data = json.loads(data)  
        # Ensure the user is authenticated before checking password
        if not user.is_authenticated:
                    raise serializers.ValidationError({"detail": "Authentication is required to change the password."})

                # Check if current password is correct
        if not user.check_password(data['current_password']):
                    raise serializers.ValidationError({"current_password": "Current password is incorrect."})

                # Ensure the new password is at least 6 characters long
        if len(data['new_password']) < 6:
                    raise serializers.ValidationError({"new_password": "New password must be at least 6 characters long."})

                # Ensure the new password is not the same as the current password
        if data['current_password'] == data['new_password']:
                    raise serializers.ValidationError({"new_password": "New password cannot be the same as the current password."})

        return data

    def save(self):
                user = self.context['request'].user  # Get the logged-in user
                user.set_password(self.validated_data['new_password'])  # Set the new password
                user.save()  # Save the user with the new password
                


           
                
        
class UserProfileSerializer(serializers.ModelSerializer):
    teacher_id = serializers.IntegerField(source="teacher_profile.id", read_only=True)
    teacher_name = serializers.CharField(source="teacher_profile.full_name", read_only=True)

    # Return merged values + absolute image URL
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role',
            'profile_picture', 'phone',
            'teacher_id', 'teacher_name'
        ]

    def _abs_url(self, request, f):
        """Turn FileField/ImageField value into an absolute URL."""
        if not f:
            return None
        try:
            url = f.url if hasattr(f, "url") else str(f)
        except Exception:
            url = str(f)
        if request and url and url.startswith("/"):
            return request.build_absolute_uri(url)
        return url

    def get_email(self, obj):
        # Prefer user.email; fall back to teacher_profile.contact_email
        tp = getattr(obj, "teacher_profile", None)
        return obj.email or getattr(tp, "contact_email", None)

    def get_phone(self, obj):
        # Prefer user.phone; fall back to teacher_profile.contact_phone
        tp = getattr(obj, "teacher_profile", None)
        return obj.phone or getattr(tp, "contact_phone", None)

    def get_profile_picture(self, obj):
        # Prefer user's picture; fall back to teacher_profile.photo; always absolute
        request = self.context.get("request")
        pic = self._abs_url(request, getattr(obj, "profile_picture", None))
        if pic:
            return pic
        tp = getattr(obj, "teacher_profile", None)
        return self._abs_url(request, getattr(tp, "photo", None))
        
        
        
        
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'phone', 'profile_picture']
        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
            'profile_picture': {'required': False},
        }

    def update(self, instance, validated_data):
        # Update User fields
        email = validated_data.get('email', None)
        phone = validated_data.get('phone', None)
        picture = validated_data.get('profile_picture', None)

        if email is not None:
            instance.email = email
        if phone is not None:
            instance.phone = phone
            # keep Teacher contact in sync for future fallbacks
            tp = getattr(instance, "teacher_profile", None)
            if tp:
                setattr(tp, "contact_phone", phone)
                tp.save()
        if picture is not None:
            instance.profile_picture = picture

        instance.save()
        return instance
        
User = get_user_model()

class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "phone",
                  "profile_picture", "password", "must_change_password", "is_active"]
        extra_kwargs = {
            "is_active": {"required": False, "default": True},
            "must_change_password": {"required": False, "default": True},
        }

    def create(self, validated_data):
        raw_pw = validated_data.pop("password", "") or None
        user = User(**validated_data)
        if "is_active" not in validated_data:
            user.is_active = True
        user.save()
        if not raw_pw:
            import secrets
            raw_pw = secrets.token_urlsafe(8)
        user.set_password(raw_pw)  # HASHES the password
        user.save()
        self.context["temp_password"] = raw_pw  # optional return
        return user