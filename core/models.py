
from django.conf import settings
from django.db import models

from dcclone.utils.fs import get_filename, mfs

User = settings.AUTH_USER_MODEL

def upload_to_file(instance, filename):
    return "public/{0}".format(get_filename(instance.file.read(), filename))

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Gallery(TimestampedModel):
    slug = models.SlugField(unique=True, max_length=64)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    allow_images = models.BooleanField(default=True)
    permission_read = models.PositiveSmallIntegerField(default=99)
    permission_write = models.PositiveSmallIntegerField(default=1)
    permission_admin = models.PositiveSmallIntegerField(default=1)
    permission_per_post = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.slug})"


class Post(TimestampedModel):
    gallery = models.ForeignKey(
        Gallery, on_delete=models.CASCADE, related_name='posts', db_index=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    nickname = models.CharField(max_length=30, blank=True, null=True)
    image = models.ImageField(upload_to=upload_to_file, storage=mfs, blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    recommend = models.IntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    is_delete = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=False)
    is_notice = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.gallery.slug}] {self.title}"


class Comment(TimestampedModel):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    nickname = models.CharField(max_length=30, blank=True, null=True)
    content = models.TextField()
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    recommend = models.IntegerField(default=0)

    def __str__(self):
        return f"Comment #{self.id} on Post {self.post_id}"


class PostVote(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=((1, 'up'), (-1, 'down')))

    class Meta:
        unique_together = ('post', 'user')


class CommentVote(models.Model):
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=((1, 'up'), (-1, 'down')))

    class Meta:
        unique_together = ('comment', 'user')
