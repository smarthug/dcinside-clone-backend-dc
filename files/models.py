from django.db import models
from core.models import Gallery
from users.models import User

from dcclone.utils.fs import get_filename, mfs


def upload_to_file(instance, filename):
    return "private/{0}".format(get_filename(instance.file.read(), filename))


class File(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=upload_to_file,
        storage=mfs,
        help_text="The ad image file.")
    filename = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('gallery', 'author', 'file')

    # Create your models here.
