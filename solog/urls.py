from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SoloG.views.home', name='home'),
    # url(r'^SoloG/', include('SoloG.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('blog.urls', namespace="blog")),
    url(r'^$', 'blog.views.index', name="index"),
    url(r'^accounts/', include('account.urls', namespace='account')),
    url(r'^search$', 'blog.views.search', name='search'),
)
