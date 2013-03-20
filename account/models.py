from datetime import datetime
from django.contrib.auth.models import User
from django.db import models


class DropboxToken(models.Model):
    user = models.ForeignKey(User, related_name="dropbox_tokens")
    access_token = models.CharField(max_length=100)
    access_token_secret = models.CharField(max_length=100)

    created_at = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return self.access_token
