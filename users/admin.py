
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'id',
        'username',
        'display_name',
        'korean_name',
        'email',
        'level',
        'points',
        'is_staff',
        'is_active',
    )
    search_fields = (
        'username',
        'display_name',
        'korean_name',
        'english_name',
        'email',
        'phone_primary',
        'phone_secondary',
        'referrer',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'gender',
        'email_opt_in',
        'message_opt_in',
        'level',
    )
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            '개인 정보',
            {
                'fields': (
                    'display_name',
                    'korean_name',
                    'english_name',
                    'birth_date',
                    'gender',
                    'icon',
                    'photo',
                    'resident_registration_number',
                )
            },
        ),
        (
            '연락처 및 주소',
            {
                'fields': (
                    'postal_code',
                    'address',
                    'phone_primary',
                    'phone_secondary',
                    'homepage_url',
                )
            },
        ),
        (
            '회원 설정',
            {
                'fields': (
                    'level',
                    'points',
                    'login_count',
                    'email_opt_in',
                    'message_opt_in',
                    'referrer',
                    'admin_note',
                )
            },
        ),
        (
            '전문가 정보',
            {
                'fields': (
                    'appraiser_class',
                    'specialty_primary',
                    'specialty_secondary',
                    'specialty_tertiary',
                    'company_info',
                    'education',
                    'experience',
                    'certificate1',
                    'certificate2',
                )
            },
        ),
    )

    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            '추가 정보',
            {
                'classes': ('wide',),
                'fields': (
                    'display_name',
                    'korean_name',
                    'english_name',
                    'birth_date',
                    'gender',
                    'postal_code',
                    'address',
                    'phone_primary',
                    'phone_secondary',
                    'email_opt_in',
                    'message_opt_in',
                    'referrer',
                ),
            },
        ),
    )
