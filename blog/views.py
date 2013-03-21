from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.markup.templatetags.markup import restructuredtext
from django.shortcuts import render_to_response, redirect, get_object_or_404, render
from django.template.context import RequestContext
from django.template.defaultfilters import linebreaksbr
from blog.forms import EntryForm
from blog.models import Post


def index(request):
    """
    Index page
    """

    query = Post.objects.order_by('-id')
    results = {}
    if query.count():
        first_post = Post.objects.order_by('id')[0]
        last_post = query[0]
        years = range(first_post.created_at.year, last_post.created_at.year + 1)
        years.sort(reverse=True)
        for year in years:
            results[year] = query.filter(created_at__year=year)

    # return render_to_response("index.html", {'results': results}, RequestContext(request))
    return render_to_response("index.html", {'posts': query}, RequestContext(request))


def format_content(format, content):
    depend = {
        'markdown': 'markdown',
    }
    try:
        if format == 'markdown':
            import markdown
            return markdown.markdown(content)
        elif format == 'txt':
            return linebreaksbr(content)
        elif format == 'html':
            return content
        elif format == 'textile':
            try:
                import textile
                return textile.textile(content)
            except ImportError:
                raise Exception(u"You must install PyTextile to use textile format.")
        elif format == 'restructuredtext':
            try:
                import docutils
                return restructuredtext(content)
            except ImportError:
                raise Exception(u"You must install docutils to use reST format.")

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
            try:
                post.content_html = format_content(post.content_format, post.content)
                post.save()
                return redirect(post.get_absolute_url())
            except Exception, e:
                messages.error(request, e.message)

    else:
        form = EntryForm(instance=post)

    context = {'form': form}
    return render_to_response("blog/post.html", context, RequestContext(request))


def detail(request, slug_or_id):
    if slug_or_id.isdigit():
        query = {'id': slug_or_id}
    else:
        query = {'slug': slug_or_id}

    post = get_object_or_404(Post, **query)

    context = {'post': post}
    return render(request, "blog/detail.html", context)

