# -*- coding: utf-8 -*-

"""
This module is the derived work from pterk's `Basic HTTP Authentication`
(http://djangosnippets.org/snippets/56/).
"""

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse


ADMIN_EMAIL = ["<a href=\"mailto:%(e)s\">%(e)s</a>" % dict(e=i[1], ) for i in settings.ADMINS]

HTML_AUTHORIZATION_REQUIRED = _("""
<html>
<body>
<pre>Authorization Required, contact %s</pre>
</body>
</html>
""") % ", ".join(ADMIN_EMAIL, )


def basic_challenge (realm=None, ) :
    if realm is None:
        realm = getattr(settings, "WWW_AUTHENTICATION_REALM", _("Restricted Access"))

    response = HttpResponse(HTML_AUTHORIZATION_REQUIRED, mimetype="text/html", )
    response["WWW-Authenticate"] = "Basic realm='%s'" % (realm)
    response.status_code = 401
    return response


def basic_authenticate (authentication, ) :
    # Taken from paste.auth
    (authmeth, auth) = authentication.split(" ", 1, )
    if "basic" != authmeth.lower() :
        return None

    auth = auth.strip().decode("base64")
    username, password = auth.split(":", 1, )
    return authenticate(username=username, password=password, )


def create_credential_header (username=None, password=None, response=None, ) :
    """
    >>> c = dict(username="test", )
    >>> create_credential_header(**c)
    Traceback (most recent call last):
    ...
    ValueError: username and password must be given.

    >>> c = dict(password="test", )
    >>> create_credential_header(**c)
    Traceback (most recent call last):
    ...
    ValueError: username and password must be given.

    >>> c = dict(username="test", password="testp", )
    >>> create_credential_header(**c)
    {'HTTP_AUTHORIZATION': 'basic dGVzdDp0ZXN0cA=='}

    with response,
    >>> _response = dict(HTTP_AUTHORIZATION="missing", )
    >>> create_credential_header(response=_response, **c)
    {'HTTP_AUTHORIZATION': 'basic dGVzdDp0ZXN0cA=='}
    """
    if not (username and password) :
        raise ValueError("username and password must be given.")

    _header = dict(
            HTTP_AUTHORIZATION="basic %s" % (
                ("%s:%s" % (username, password, )).encode("base64").strip(),
            ),
        )

    if not response :
        return _header

    response.update(_header, )
    return response


def decorator_login_required (func, ) :
    def wrapper (*a, **kw) :
        if hasattr(a[0], "META", ) :  # it's `request`
            _request = a[0]
        else :
            _request = a[1]

        if "HTTP_AUTHORIZATION" not in _request.META :
            return basic_challenge()

        _user = basic_authenticate(_request.META["HTTP_AUTHORIZATION"], )
        if _user is None:
            return basic_challenge()

        login(_request, _user, )
        return func(*a, **kw)

    return wrapper


class BasicAuthenticationMiddleware (object, ) :
    def process_request(self, request, ) :
        if not request.path.startswith(reverse("gppi-pypi", ), ) :
            return None

        if request.user.is_authenticated() :
            return None
        elif "HTTP_AUTHORIZATION" not in request.META :
            return None

        user = basic_authenticate(request.META["HTTP_AUTHORIZATION"], )
        if user is None:
            return basic_challenge()
        else:
            login(request, user, )

        return None


if __name__ == "__main__" :
    import doctest
    doctest.testmod()


