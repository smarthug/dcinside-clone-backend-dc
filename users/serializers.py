from rest_framework import serializers

from .models import User, UserMetaInfo, UserAgreement


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    # Accept minimal extra fields for meta/agreement; optional
    korean_name = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    email_opt_in = serializers.BooleanField(write_only=True, required=False)
    message_opt_in = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'email',
            'display_name',
            # extra accepted, mapped manually
            'korean_name',
            'email_opt_in',
            'message_opt_in',
        ]
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        korean_name = validated_data.pop('korean_name', None)
        email_opt_in = validated_data.pop('email_opt_in', None)
        message_opt_in = validated_data.pop('message_opt_in', None)

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # create or update related meta info
        if korean_name:
            UserMetaInfo.objects.update_or_create(user=user, defaults={'korean_name': korean_name})
        # agreements (optional)
        if email_opt_in is not None or message_opt_in is not None:
            UserAgreement.objects.update_or_create(
                user=user,
                defaults={
                    'email_agreement': bool(email_opt_in) if email_opt_in is not None else False,
                    'message_agreement': bool(message_opt_in) if message_opt_in is not None else False,
                }
            )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'display_name',
            'date_joined',
            'last_login',
        ]
        read_only_fields = fields
