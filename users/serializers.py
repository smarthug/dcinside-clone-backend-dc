from rest_framework import serializers

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'email',
            'display_name',
            'korean_name',
            'english_name',
            'icon',
            'photo',
            'birth_date',
            'gender',
            'postal_code',
            'address',
            'resident_registration_number',
            'phone_primary',
            'phone_secondary',
            'email_opt_in',
            'message_opt_in',
            'referrer',
            'appraiser_class',
            'specialty_primary',
            'specialty_secondary',
            'specialty_tertiary',
            'company_info',
            'education',
            'experience',
            'certificate1',
            'certificate2',
            'homepage_url',
        ]
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'display_name',
            'korean_name',
            'english_name',
            'icon',
            'photo',
            'birth_date',
            'gender',
            'postal_code',
            'address',
            'resident_registration_number',
            'phone_primary',
            'phone_secondary',
            'email_opt_in',
            'message_opt_in',
            'referrer',
            'level',
            'points',
            'login_count',
            'appraiser_class',
            'specialty_primary',
            'specialty_secondary',
            'specialty_tertiary',
            'company_info',
            'education',
            'experience',
            'certificate1',
            'certificate2',
            'homepage_url',
            'admin_note',
            'date_joined',
            'last_login',
        ]
        read_only_fields = (
            'id',
            'username',
            'level',
            'points',
            'login_count',
            'admin_note',
            'date_joined',
            'last_login',
        )
