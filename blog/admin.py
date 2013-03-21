from django.contrib import admin
from blog.models import Post, Blog


class PostAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_published", "last_update_at")

admin.site.register(Blog)
admin.site.register(Post, PostAdmin)
