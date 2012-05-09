from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import simplejson
from django.utils.translation import ugettext as _

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
