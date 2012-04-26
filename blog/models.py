from django.contrib.auth.models import User
from django.db import models


class Entry(models.Model):
    user = models.ForeignKey(User, related_name="entries")

    title = models.CharField(max_length=100)
    slug = models.SlugField()

    content = models.TextField(default="")
    content_html = models.TextField(default="")

    created_at = models.DateTimeField(auto_now_add=True)
    last_update_at = models.DateTimeField(auto_now=True)


class Version(models.Model):
    entry = models.ForeignKey(Entry)
    revision = models.IntegerField()

    content = models.TextField()
    diff = models.TextField()
    edit_at = models.DateTimeField(auto_now_add=True)


class Images(models.Model):
    pass
