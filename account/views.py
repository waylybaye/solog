from datetime import datetime
import os
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import simplejson
from django.utils.translation import ugettext as _
from dropbox import client, rest, session
import markdown
from slugify import slugify
from account.models import DropboxToken
from dateutil import parser
from django.conf import settings
from blog.models import Post, SyncActivity


def render_json(**kwargs):
    return HttpResponse(simplejson.dumps(kwargs))


def account_login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')

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
    """
    Authorize dropbox
    """
    sess = session.DropboxSession(settings.DROPBOX_KEY, settings.DROPBOX_SECRET, 'app_folder')

    if callback:
        request_token = request.session['request_token']
        del request.session['request_token']
        request_token = session.OAuthToken(*request_token.split('&'))
        access_token = sess.obtain_access_token(request_token)

        dropbox_token, _ = DropboxToken.objects.get_or_create(user=request.user)
        dropbox_token.access_token=access_token.key
        dropbox_token.access_token_secret = access_token.secret
        dropbox_token.save()

        return redirect(reverse("account:dropbox_sync"))

    request_token = sess.obtain_request_token()
    request.session['request_token'] = "%s&%s" % (request_token.key, request_token.secret)

    callback = request.build_absolute_uri(reverse("account:dropbox_callback"))
    url = sess.build_authorize_url(request_token, callback)
    return redirect(url)


@login_required
def dropbox_sync(request):
    """
    Sync posts from Dropbox folders

    """
    # TODO: support token param which allow user sync their posts through a url with no need to login
    user = request.user

    sess = session.DropboxSession(settings.DROPBOX_KEY, settings.DROPBOX_SECRET, 'app_folder')
    dropbox_token = DropboxToken.objects.get(user=user)
    sess.set_token(dropbox_token.access_token, dropbox_token.access_token_secret)

    api = client.DropboxClient(sess)
    metas = api.metadata('/')

    new_or_updated_files = []

    for content in metas['contents']:
        name = content['path']
        modified = parser.parse(content['modified'])

        try:
            post = Post.objects.get(user=user, filename=name)
            if post.last_update_at < modified:
                new_or_updated_files.append(name)

        except Post.DoesNotExist:
            new_or_updated_files.append(name)


    for name in new_or_updated_files:
        update_post(request, api, name)


    if not new_or_updated_files:
        SyncActivity.objects.create(
            user=user,
            description="No changes found."
        )

    return redirect("/")


def update_post(request, api, path):
    """
    Update or create a post from Dropbox file
    Supported markdown Meta:
        Title: Post title
        Slug: url slug. default slugify(title), filename
        Date: post created date
        Published: not publish this post if Published is false
    """
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

    extensions = ['meta', 'fenced_code']
    md = markdown.Markdown(extensions=extensions)

    html = md.convert(content.decode('utf8'))

    file_name = os.path.splitext(name)[0]
    meta = md.Meta

    title = meta.get('title', [file_name])[0]
    slug = meta.get('slug', [slugify(title)])[0]
    not_published = 'published' in meta and meta.get('published')[0].lower() == 'false'
    created_date = parser.parse(meta.get('date')[0]) if 'date' in meta else datetime.now()

    if 'date' in meta:
        post.created_at = created_date
    else:
        if not post.created_at:
            post.created_at = last_modified

    post.last_update_at = last_modified

    post.title = title
    post.slug = slug
    post.content = content
    post.content_html = html
    post.content_format = 'markdown'
    post.is_published = not not_published

    post.save()

    SyncActivity.objects.create(
        user=post.user,
        post=post,
    )

