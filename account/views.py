import os
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import simplejson
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from dropbox import client, rest, session
import markdown
from account.models import DropboxToken
from dateutil import parser
from django.conf import settings
from blog.models import Post


def render_json(**kwargs):
    return HttpResponse(simplejson.dumps(kwargs))


def account_login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')

    print username, password
    user = authenticate(username=username, password=password)
    if not user:
        return render_json(success=False, message=_(u"username or password was invalid."))

    login(request, user)
    return render_json(success=True)


def account_logout(request):
    logout(request)
    return redirect('/')


@login_required
def dropbox_auth(request, callback=None):
    sess = session.DropboxSession(settings.DROPBOX_KEY, settings.DROPBOX_SECRET, 'app_folder')

    if callback:
        request_token = request.session['request_token']
        del request.session['request_token']
        request_token = session.OAuthToken(*request_token.split('&'))
        access_token = sess.obtain_access_token(request_token)
        DropboxToken.objects.create(
            user=request.user,
            access_token=access_token.key,
            access_token_secret=access_token.secret
        )
        return redirect(reverse("account:dropbox_sync"))


    request_token = sess.obtain_request_token()
    request.session['request_token'] = "%s&%s" % (request_token.key, request_token.secret)

    callback = request.build_absolute_uri(reverse("account:dropbox_callback"))
    url = sess.build_authorize_url(request_token, callback)
    return redirect(url)


@login_required
def dropbox_sync(request):
    sess = session.DropboxSession(settings.DROPBOX_KEY, settings.DROPBOX_SECRET, 'app_folder')
    dropbox_token = DropboxToken.objects.get(user=request.user)
    sess.set_token(dropbox_token.access_token, dropbox_token.access_token_secret)

    api = client.DropboxClient(sess)
    metas = api.metadata('/')


    new_or_updated_files = []

    for content in metas['contents']:
        name = content['path']
        modified = parser.parse(content['modified'])

        try:
            post = Post.objects.get(filename=name)
            if post.last_update_at < modified:
                new_or_updated_files.append(name)

        except Post.DoesNotExist:
            new_or_updated_files.append(name)


    for name in new_or_updated_files:
        update_post(request, api, name)

    return redirect("/")


def update_post(request, api, path):
    parent_dir, name = os.path.split(path)
    try:
        post = Post.objects.get(filename=path)
    except Post.DoesNotExist:
        post = Post(
            user=request.user,
            filename=path
        )

    f, metadata = api.get_file_and_metadata(path)
    content = f.read()

    last_modified = parser.parse(metadata['modified'])

    md = markdown.Markdown(extensions=['meta'])

    html = md.convert(content.decode('utf8'))

    if 'date' in md.Meta:
        post.created_at = parser.parse(md.Meta.get('date')[0])
    else:
        if not post.created_at:
            post.created_at = last_modified

    post.last_update_at = last_modified

    post.title = md.Meta.get('title', ['Untitled'])[0]
    post.slug = md.Meta.get('slug', [slugify(name[:-3])])[0]
    post.content = content
    post.content_html = html
    post.content_format = 'markdown'

    if 'published' in md.Meta and md.Meta.get('published').lower() == 'false':
        post.is_published = False
    post.save()

