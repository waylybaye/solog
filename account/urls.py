from django.conf.urls import patterns, url

urlpatterns = patterns('account.views',
    url(r'^login$', 'account_login', name='login'),
    url(r'^logout$', 'account_logout', name='logout'),
)
