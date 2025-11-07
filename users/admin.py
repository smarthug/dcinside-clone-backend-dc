
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserAgreement, UserMetaInfo


class UserAgreementInline(admin.StackedInline):
    model = UserAgreement
    can_delete = False
    verbose_name_plural = 'User Agreements'
    readonly_fields = ('email_agreement_at', 'message_agreement_at',)


class UserMetaInfoInline(admin.StackedInline):
    model = UserMetaInfo
    can_delete = False
    verbose_name_plural = 'User Meta Info'
    fieldsets = (
        ('Personal Info', {'fields': ('korean_name',
         'english_name', 'birth_date', 'photo',)}),
        ('Contact & Address', {'fields': (
            'postal_code', 'address', 'phone_primary', 'phone_secondary', 'homepage_url',)}),
        ('Expert Info', {'fields': ('appraiser_class', 'specialty_primary', 'specialty_secondary',
         'specialty_tertiary', 'company_info', 'education', 'experience', 'certificate1', 'certificate2',)}),
    )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'id',
        'username',
        'display_name',
        'email',
        'level',
        'is_staff',
        'is_active',
    )
    search_fields = (
        'username',
        'display_name',
        'email',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'level',
    )
    readonly_fields = ('date_joined',)
    inlines = (UserAgreementInline, UserMetaInfoInline,)

    fieldsets = (
        (None, {"fields": ("username", "password",)}),
        (_("Personal info"), {"fields": ("display_name", "email", "level",)}),
        (_("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
        },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined",)}),
    )
