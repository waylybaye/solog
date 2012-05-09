from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext
from blog.forms import EntryForm
from blog.models import Entry


def index(request):
    """
    Index page
    """
    return render_to_response("index.html", {}, RequestContext(request))


@login_required
def post(request):
    """
    post a new entry
    """
    if request.method == 'POST':
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            return redirect(entry.get_absolute_url())
    else:
        form = EntryForm()

    context = {'form': form}
    return render_to_response("blog/post.html", context, RequestContext(request))


def detail(request, entry_id=None):
    #entry = get_object_or_404(Entry, id=entry_id)
    #context = {'entry': entry}
    context = {}
    return render_to_response("blog/detail.html", context, RequestContext(request))
