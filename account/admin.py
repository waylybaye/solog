from django.contrib import admin
from account.models import DropboxToken


class DropboxTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "access_token", "access_token_secret", "created_at")

admin.site.register(DropboxToken, DropboxTokenAdmin)
