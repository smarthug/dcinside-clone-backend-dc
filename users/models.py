
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = 'M', '남성'
        FEMALE = 'F', '여성'
        OTHER = 'O', '기타'

    display_name = models.CharField(max_length=50, blank=True, null=True)
    korean_name = models.CharField(max_length=50, blank=True, null=True)
    english_name = models.CharField(max_length=100, blank=True, null=True)
    icon = models.ImageField(upload_to='users/icons/', blank=True, null=True)
    level = models.PositiveIntegerField(default=1)
    points = models.IntegerField(default=0)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    resident_registration_number = models.CharField(max_length=20, blank=True, null=True)
    phone_primary = models.CharField(max_length=20, blank=True, null=True)
    phone_secondary = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    email_opt_in = models.BooleanField(default=True)
    message_opt_in = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)
    admin_note = models.TextField(blank=True, null=True)
    referrer = models.CharField(max_length=150, blank=True, null=True)
    login_count = models.PositiveIntegerField(default=0)
    appraiser_class = models.CharField(max_length=30, blank=True, null=True)
    specialty_primary = models.CharField(max_length=100, blank=True, null=True)
    specialty_secondary = models.CharField(max_length=100, blank=True, null=True)
    specialty_tertiary = models.CharField(max_length=100, blank=True, null=True)
    company_info = models.CharField(max_length=255, blank=True, null=True)
    education = models.CharField(max_length=255, blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    certificate1 = models.CharField(max_length=255, blank=True, null=True)
    certificate2 = models.CharField(max_length=255, blank=True, null=True)
    homepage_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.username
