from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class BlogManager(models.Manager):
    def get_current(self):
        return self.get(id=1)


class Blog(models.Model):
    name = models.CharField(max_length=50, verbose_name=u"Blog Name")
    description = models.TextField(_(u"Blog Description"))

    objects = BlogManager()


class Entry(models.Model):
    user = models.ForeignKey(User, related_name="entries")

    title = models.CharField(max_length=100)
    slug = models.SlugField()

    content = models.TextField(default="")
    content_html = models.TextField(default="")

    created_at = models.DateTimeField(auto_now_add=True)
    last_update_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return "blog:detail", [self.id]


class Version(models.Model):
    entry = models.ForeignKey(Entry)
    revision = models.IntegerField()

    content = models.TextField()
    diff = models.TextField()
    edit_at = models.DateTimeField(auto_now_add=True)


class Images(models.Model):
    pass
