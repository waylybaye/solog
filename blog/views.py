from importlib import import_module
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext
from haystack.query import SearchQuerySet
from blog.forms import EntryForm
from blog.models import Post
from mmseg import seg_txt


def index(request):
    """
    Index page
    """
    return render_to_response("index.html", {}, RequestContext(request))


def format_content(format, content):
    depend = {
        'markdown': 'markdown',
    }
    try:
        if format == 'markdown':
            import markdown
            return markdown.markdown(content)
        elif format == 'txt':
            return content
        elif format == 'html':
            return content
        elif format == 'textile':
            return content
        elif format == 'restructuredtext':
            return content

    except ImportError:
        raise Exception('You should install "%s" to use %s format.' % (depend.get(format),  format))


@login_required
def post(request, post_id=None):
    """
    post a new post
    """
    post = get_object_or_404(Post, id=post_id) if post_id else None
    if request.method == 'POST':
        form = EntryForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.content_html = format_content(post.content_format, post.content)
            post.save()
            return redirect(post.get_absolute_url())
    else:
        form = EntryForm(instance=post)

    context = {'form': form}
    return render_to_response("blog/post.html", context, RequestContext(request))


def detail(request, entry_id=None):
    post = get_object_or_404(Post, id=entry_id)
    context = {'post': post}
    return render_to_response("blog/detail.html", context, RequestContext(request))


def search(request):
    q = request.GET.get('q')
    q = ' '.join([t.decode('utf8') for t in seg_txt(q.encode('utf8')) ])
    queryset = SearchQuerySet()
    results = queryset.autocomplete(content_auto=q) | queryset.filter(text=q)
    return render_to_response('blog/search.html', {'results': results, 'q': q}, RequestContext(request))
