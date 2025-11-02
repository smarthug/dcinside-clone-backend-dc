from django.core.mail import send_mail
from django.conf import settings

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


from .models import User, UserMetaInfo, UserAgreement, UserVerification


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    passwordConfirm = serializers.CharField(write_only=True, min_length=8)
    email_opt_in = serializers.BooleanField(
        write_only=True, required=False, default=False)
    message_opt_in = serializers.BooleanField(
        write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            "passwordConfirm",
            'email',
            'email_opt_in',
            'message_opt_in',
        ]
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        password_confirm = validated_data.pop('passwordConfirm')
        email_opt_in = validated_data.pop('email_opt_in')
        message_opt_in = validated_data.pop('message_opt_in')

        display_name = validated_data.get('username')
        email = validated_data.get('email')

        if password != password_confirm:
            raise serializers.ValidationError(
                {'password': _('Passwords must match.')})

        user = User(**validated_data,
                    display_name=display_name, is_active=False)
        user.set_password(password)
        user.save()

        # agreements
        UserAgreement.objects.update_or_create(
            user=user,
            defaults={
                'email_agreement': bool(email_opt_in),
                'message_agreement': bool(message_opt_in),
            }
        )
        # Verifiation
        [verification_obj, created] = UserVerification.objects.update_or_create(
            user=user,
        )

        send_mail('[한국건설감정사회] 회원가입 이메일인증 입니다.',
                  #   '<div style="width: fit-content; min-width:100%;">',
                  'rokkor0472@gmail.com',
                  '',
                  [email],
                  fail_silently=False,
                  html_message=f'<a href="http://{settings.FRONT_BASE_URL}/verify/?token={str(verification_obj.token).replace("-", "")}">인증하기</a>',
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


class UserMetaProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMetaInfo
        fields = "__all__"
        read_only_fields = ['user']
