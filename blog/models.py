from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import urlencode
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from datetime import datetime


class BlogManager(models.Manager):
    def get_current(self):
        return self.get(id=1)


class Blog(models.Model):
    name = models.CharField(max_length=50, verbose_name=u"Blog Name")
    description = models.TextField(_(u"Blog Description"))

    objects = BlogManager()


FORMAT_CHOICES = (
    ('restructuredtext', 'reST (reStructuredText)'),
    ('textile', 'Textile'),
    ('markdown', 'Markdown'),
    ('html', 'HTML'),
    ('txt', 'Plain Text'),
)


class PostManager(models.Manager):
    def post(user, title, content, format='txt'):
        return self.create(
            user = user,
            title = title,
            content = content,
            content_format = format,
        )


class Post(models.Model):
    user = models.ForeignKey(User, related_name="entries")

    title = models.CharField(max_length=100)
    slug = models.SlugField()

    filename = models.CharField(max_length=255, null=True, blank=True)

    content = models.TextField(default="")
    content_html = models.TextField(default="")
    content_format = models.CharField(max_length='30', choices=FORMAT_CHOICES)

    is_published = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(default=datetime.now)
    last_update_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return u"blog:detail", [self.slug or self.id]


class Version(models.Model):
    entry = models.ForeignKey(Post)
    revision = models.IntegerField()

    content = models.TextField()
    diff = models.TextField()
    edit_at = models.DateTimeField(auto_now_add=True)


class Images(models.Model):
    pass


class SyncActivity(models.Model):
    user = models.ForeignKey(User)
    description = models.TextField()
    post = models.ForeignKey(Post, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.description


