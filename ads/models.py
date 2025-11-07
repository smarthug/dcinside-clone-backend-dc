from django.db import models
from django.utils import timezone

from ads.utils.fs import get_filename, mfs


def upload_to_image_large(instance, filename):
    return "media/ads/{0}".format(get_filename(instance.image_large.read(), filename))


def upload_to_image_small(instance, filename):
    return "media/ads/{0}".format(get_filename(instance.image_small.read(), filename))


class AdManager(models.Manager):
    """
    Custom manager to return only ads that are currently active and published.
    """

    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )


class Ad(models.Model):
    """
    Model to represent an advertisement.
    """
    LOCATION_CHOICES = [
        ('hero', 'Hero Section (Slideshow)'),
        ('sidebar', 'Sidebar Ad'),
        ('banner', 'Banner Ad'),
        ('partner', 'Partner Ad'),
    ]

    title = models.CharField(
        max_length=255,
        help_text="Internal title for the ad."
    )
    image_large = models.ImageField(
        upload_to=upload_to_image_large,
        storage=mfs,
        help_text="The ad image file."
    )
    image_small = models.ImageField(
        upload_to=upload_to_image_small,
        storage=mfs,
        help_text="The ad image file."
    )
    link_url = models.TextField(
        max_length=4096,
        blank=True,
        null=True,
        help_text="URL the ad links to when clicked."
    )
    location = models.CharField(
        max_length=50,
        choices=LOCATION_CHOICES,
        default='hero',
        db_index=True,
        help_text="Where this ad will be displayed."
    )

    # Publishing fields
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date and time when the ad starts being visible."
    )
    end_date = models.DateTimeField(
        help_text="Date and time when the ad stops being visible."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Manually toggle this ad on or off."
    )

    # Ordering field
    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
        db_index=True,
        help_text="Order for display. 0 is highest."
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()  # The default manager
    published = AdManager()     # The custom 'published' manager

    class Meta:
        # Default ordering is by the 'order' field,
        # then by start_date as a tie-breaker.
        ordering = ['order', '-start_date']
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"

    def __str__(self):
        return self.title
