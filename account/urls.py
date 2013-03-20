from django.conf.urls import patterns, url

urlpatterns = patterns('account.views',
    url(r'^login$', 'account_login', name='login'),
    url(r'^logout$', 'account_logout', name='logout'),
    url(r'^dropbox/auth$', 'dropbox_auth', name='dropbox_auth'),
    url(r'^dropbox/callback$', 'dropbox_auth', {'callback': True}, name='dropbox_callback'),
    url(r'^dropbox/sync$', 'dropbox_sync', name='dropbox_sync'),
)
