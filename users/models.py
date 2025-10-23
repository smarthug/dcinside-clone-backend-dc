from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
# from django.contrib.postgres.fields import ArrayField


class User(AbstractBaseUser, PermissionsMixin):

    username = models.CharField(max_length=150)
    display_name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.username}"


class UserAgreement(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='agreements', unique=True)
    email_agreement = models.BooleanField(default=False)
    email_agreement_at = models.DateTimeField(auto_now_add=True)
    message_agreement = models.BooleanField(default=False)
    message_agreement_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class UserMetaInfo(models.Model):
    class Specialty(models.IntegerChoices):
        ARCHITECTURE = 1, '건축'
        CIVIL = 2, '토목'
        ENVIRONMENT = 3, '환경'
        ELECTRICAL = 4, '전기'
        MECHANICAL = 5, '설비'
        STRUCTURE = 6, '건축,토목구조'
        CULTURAL_HERITAGE = 7, '문화재'
        LAW = 8, '법률'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_login_at = models.DateTimeField(auto_now_add=True)

    korean_name = models.CharField(max_length=50, blank=True, null=True)
    english_name = models.CharField(max_length=100, blank=True, null=True)

    postal_code = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    phone_primary = models.CharField(max_length=20, blank=True, null=True)
    phone_secondary = models.CharField(max_length=20, blank=True, null=True)

    birth_date = models.DateField(blank=True, null=True)

    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)
    appraiser_class = models.CharField(max_length=30, blank=True, null=True)
    specialty_primary = models.PositiveSmallIntegerField(
        choices=Specialty.choices, blank=True, null=True)
    specialty_secondary = models.PositiveSmallIntegerField(
        choices=Specialty.choices, blank=True, null=True)
    specialty_tertiary = models.PositiveSmallIntegerField(
        choices=Specialty.choices, blank=True, null=True)
    company_info = models.CharField(max_length=255, blank=True, null=True)
    education = models.CharField(max_length=255, blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    certificate1 = models.CharField(max_length=255, blank=True, null=True)
    certificate2 = models.CharField(max_length=255, blank=True, null=True)
    homepage_url = models.URLField(blank=True, null=True)
