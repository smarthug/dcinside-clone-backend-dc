from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied


from .models import User, UserMetaInfo, UserAgreement, UserVerification, UserEducation, UserCareer, UserCertificate, UserExternalActivity, UserPublication, UserAward
from .utils import send_kica_email


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

    def validate_password(self, value):
        try:
            validate_password(value, self.instance)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

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
        
        content_html = f"""
            <h2 style="color: #333; text-align: center;">이메일 인증 안내</h2>
            <p style="color: #555; line-height: 1.6;">
                안녕하세요, {display_name}님.<br>
                한국건설감정사회 회원가입을 환영합니다.<br>
                아래 버튼을 클릭하여 이메일 인증을 완료해 주세요.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #007bff; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">이메일 인증하기</a>
            </div>
        """

        send_kica_email(
            subject='[한국건설감정사회] 회원가입 이메일 인증 안내',
            recipient_list=[email],
            content_html=content_html
        )
        return user


class UserEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEducation
        fields = ['id', 'school_name', 'major',
                  'degree', 'status', 'grad_date']


class UserCareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCareer
        fields = ['id', 'company', 'position',
                  'assigned_task', 'start_date', 'end_date']


class UserCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCertificate
        fields = ['id', 'name', 'issuer', 'date', 'license_no']


class UserExternalActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExternalActivity
        fields = ['id', 'content', 'start_date', 'end_date']


class UserPublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPublication
        fields = ['id', 'title', 'publisher', 'date']


class UserAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAward
        fields = ['id', 'name', 'issuer', 'date']


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
    
    # Affiliation
    company_info = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    department = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_industry = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_task = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_postal_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    activity_region = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    activity_region_2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    activity_region_3 = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    educations = UserEducationSerializer(many=True, required=False)
    careers = UserCareerSerializer(many=True, required=False)
    certificates = UserCertificateSerializer(many=True, required=False)
    activities = UserExternalActivitySerializer(many=True, required=False)
    publications = UserPublicationSerializer(many=True, required=False)
    awards = UserAwardSerializer(many=True, required=False)

    homepage_url = serializers.URLField(
        required=False, allow_blank=True, allow_null=True)

    # agreements
    email_opt_in = serializers.BooleanField(required=False)
    message_opt_in = serializers.BooleanField(required=False)
    privacy_policy_250923 = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'level',
            # meta
            'korean_name', 'english_name', 'postal_code', 'address', 'phone_primary', 'phone_secondary',
            'birth_date', 'photo', 'appraiser_class', 'specialty_primary', 'specialty_secondary',
            # Affiliation
            'company_info', 'company', 'department', 'position', 'company_industry', 'company_task',
            'company_postal_code', 'company_address', 'company_phone',
            'activity_region', 'activity_region_2', 'activity_region_3', 'homepage_url',
            # lists
            'educations', 'careers', 'certificates', 'activities', 'publications', 'awards',
            # agreements
            'email_opt_in', 'message_opt_in', 'privacy_policy_250923',
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
                
                'company_info': meta.company_info,
                'company': meta.company,
                'department': meta.department,
                'position': meta.position,
                'company_industry': meta.company_industry,
                'company_task': meta.company_task,
                'company_postal_code': meta.company_postal_code,
                'company_address': meta.company_address,
                'company_phone': meta.company_phone,
                
                'activity_region': meta.activity_region,
                'activity_region_2': meta.activity_region_2,
                'activity_region_3': meta.activity_region_3,
                
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
                'privacy_policy_250923': agr.privacy_policy_250923,
            })
        return data

    def update(self, instance, validated_data):
        # Permission Check for Restricted Fields
        user = self.context['request'].user
        
        # Check level update permission
        if 'level' in validated_data and user.level != 1:
            raise PermissionDenied("등급은 관리자만 수정할 수 있습니다.")
            
        # Check appraiser_class update permission
        if 'appraiser_class' in validated_data and user.level != 1:
            raise PermissionDenied("건설감정사 기수는 관리자만 수정할 수 있습니다.")

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
        privacy_policy_250923 = validated_data.pop('privacy_policy_250923', None)
        if email_opt_in is not None or message_opt_in is not None or privacy_policy_250923 is not None:
            defaults = {}
            if email_opt_in is not None:
                defaults['email_agreement'] = bool(email_opt_in)
                if defaults['email_agreement']:
                    defaults['email_agreement_at'] = timezone.now()
            if message_opt_in is not None:
                defaults['message_agreement'] = bool(message_opt_in)
                if defaults['message_agreement']:
                    defaults['message_agreement_at'] = timezone.now()
            if privacy_policy_250923 is not None:
                defaults['privacy_policy_250923'] = bool(privacy_policy_250923)
                if defaults['privacy_policy_250923']:
                    defaults['privacy_policy_250923_at'] = timezone.now()
            UserAgreement.objects.update_or_create(
                user=instance, defaults=defaults)

        # lists - replace all logic
        educations_data = validated_data.pop('educations', None)
        if educations_data is not None:
            instance.educations.all().delete()
            for item in educations_data:
                UserEducation.objects.create(user=instance, **item)

        careers_data = validated_data.pop('careers', None)
        if careers_data is not None:
            instance.careers.all().delete()
            for item in careers_data:
                UserCareer.objects.create(user=instance, **item)
        
        certificates_data = validated_data.pop('certificates', None)
        if certificates_data is not None:
            instance.certificates.all().delete()
            for item in certificates_data:
                UserCertificate.objects.create(user=instance, **item)
                
        activities_data = validated_data.pop('activities', None)
        if activities_data is not None:
            instance.activities.all().delete()
            for item in activities_data:
                UserExternalActivity.objects.create(user=instance, **item)

        publications_data = validated_data.pop('publications', None)
        if publications_data is not None:
            instance.publications.all().delete()
            for item in publications_data:
                UserPublication.objects.create(user=instance, **item)

        awards_data = validated_data.pop('awards', None)
        if awards_data is not None:
            instance.awards.all().delete()
            for item in awards_data:
                UserAward.objects.create(user=instance, **item)

        # meta fields (including photo)
        meta_fields = {
            'korean_name', 'english_name', 'postal_code', 'address', 'phone_primary', 'phone_secondary',
            'birth_date', 'photo', 'appraiser_class', 'specialty_primary', 'specialty_secondary',
            'company_info', 'homepage_url',
            'company', 'department', 'position', 'company_industry', 'company_task',
            'company_postal_code', 'company_address', 'company_phone', 
            'activity_region', 'activity_region_2', 'activity_region_3'
        }
        meta_updates = {k: v for k, v in validated_data.items()
                        if k in meta_fields}
        if meta_updates:
            UserMetaInfo.objects.update_or_create(
                user=instance, defaults=meta_updates)

        return instance
