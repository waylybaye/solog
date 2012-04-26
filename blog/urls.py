from django.conf.urls import patterns, url

urlpatterns = patterns("blog.views",
    url(r'^post$', 'post', name='post'),
    url(r'^(\w+)$', 'detail', name='detail'),
)
