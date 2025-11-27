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

        verification_link = f"{settings.FRONT_BASE_URL}/verify/?token={verification_obj.token}"
        
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
            <h2 style="color: #333; text-align: center;">이메일 인증 안내</h2>
            <p style="color: #555; line-height: 1.6;">
                안녕하세요, {display_name}님.<br>
                한국건설감정사회 회원가입을 환영합니다.<br>
                아래 버튼을 클릭하여 이메일 인증을 완료해 주세요.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #007bff; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">이메일 인증하기</a>
            </div>
            <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                본 메일은 발신 전용입니다.<br>
                요청하지 않으셨다면 이 메일을 무시해 주세요.
            </p>
        </div>
        """

        send_mail('[한국건설감정사회] 회원가입 이메일 인증 안내',
                  '',
                  settings.DEFAULT_FROM_EMAIL,
                  [email],
                  fail_silently=False,
                  html_message=html_message,
                  )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    # related meta fields
    korean_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    english_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    postal_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    phone_primary = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    phone_secondary = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    appraiser_class = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    specialty_primary = serializers.IntegerField(
        required=False, allow_null=True)
    specialty_secondary = serializers.IntegerField(
        required=False, allow_null=True)
    specialty_tertiary = serializers.IntegerField(
        required=False, allow_null=True)
    company_info = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    education = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    experience = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    certificate1 = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    certificate2 = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    homepage_url = serializers.URLField(
        required=False, allow_blank=True, allow_null=True)

    # agreements
    email_opt_in = serializers.BooleanField(required=False)
    message_opt_in = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'level',
            # meta
            'korean_name', 'english_name', 'postal_code', 'address', 'phone_primary', 'phone_secondary',
            'birth_date', 'photo', 'appraiser_class', 'specialty_primary', 'specialty_secondary', 'specialty_tertiary',
            'company_info', 'education', 'experience', 'certificate1', 'certificate2', 'homepage_url',
            # agreements
            'email_opt_in', 'message_opt_in',
            # readonly timestamps
            'date_joined', 'last_login',
        ]
        read_only_fields = ('id', 'username', 'date_joined', 'last_login')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        meta = UserMetaInfo.objects.filter(user=instance).first()
        if meta:
            data.update({
                'korean_name': meta.korean_name,
                'english_name': meta.english_name,
                'postal_code': meta.postal_code,
                'address': meta.address,
                'phone_primary': meta.phone_primary,
                'phone_secondary': meta.phone_secondary,
                'birth_date': meta.birth_date.isoformat() if meta.birth_date else None,
                'appraiser_class': meta.appraiser_class,
                'specialty_primary': meta.specialty_primary,
                'specialty_secondary': meta.specialty_secondary,
                'specialty_tertiary': meta.specialty_tertiary,
                'company_info': meta.company_info,
                'education': meta.education,
                'experience': meta.experience,
                'certificate1': meta.certificate1,
                'certificate2': meta.certificate2,
                'homepage_url': meta.homepage_url,
            })
            # photo URL (if present)
            if meta.photo and hasattr(meta.photo, 'url'):
                data['photo'] = meta.photo.url
        agr = UserAgreement.objects.filter(user=instance).first()
        if agr:
            data.update({
                'email_opt_in': agr.email_agreement,
                'message_opt_in': agr.message_agreement,
            })
        return data

    def update(self, instance, validated_data):
        # pull user fields
        email = validated_data.pop('email', None)
        display_name = validated_data.pop('display_name', None)
        level = validated_data.pop('level', None)
        
        if email is not None:
            instance.email = email
        if display_name is not None:
            instance.display_name = display_name
        if level is not None:
            instance.level = level
            
        instance.save(update_fields=['email', 'display_name', 'level'])

        # agreements
        email_opt_in = validated_data.pop('email_opt_in', None)
        message_opt_in = validated_data.pop('message_opt_in', None)
        if email_opt_in is not None or message_opt_in is not None:
            defaults = {}
            if email_opt_in is not None:
                defaults['email_agreement'] = bool(email_opt_in)
            if message_opt_in is not None:
                defaults['message_agreement'] = bool(message_opt_in)
            UserAgreement.objects.update_or_create(
                user=instance, defaults=defaults)

        # meta fields (including photo)
        meta_fields = {
            'korean_name', 'english_name', 'postal_code', 'address', 'phone_primary', 'phone_secondary',
            'birth_date', 'photo', 'appraiser_class', 'specialty_primary', 'specialty_secondary', 'specialty_tertiary',
            'company_info', 'education', 'experience', 'certificate1', 'certificate2', 'homepage_url',
        }
        meta_updates = {k: v for k, v in validated_data.items()
                        if k in meta_fields}
        if meta_updates:
            UserMetaInfo.objects.update_or_create(
                user=instance, defaults=meta_updates)

        return instance
