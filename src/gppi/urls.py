# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url, include
from django.http import HttpResponseNotAllowed
from django.utils.functional import update_wrapper


CONDITIONAL_VIEWS = dict()


def decorator_conditional_view (func, key, ) :
    def wrapper (request, *a, **kw) :
        _func = None
        for i in CONDITIONAL_VIEWS.get(key, ) :
            if i.get("methods") is None :
                _func = i.get("view")
                break
            elif request.method in i.get("methods", list(), ) :
                _func = i.get("view")
                break

        if _func is None :
            return HttpResponseNotAllowed(list(), )

        return _func(request, *a, **kw)

    update_wrapper(wrapper, func, assigned=tuple(), )
    return wrapper


def conditional_url (regex, view, *a, **kw) :
    _org = ("kwargs", "name", "prefix", )
    _kw = dict([(k, v, ) for k, v in kw.items() if k in _org])

    _methods = kw.get("methods", None, )
    CONDITIONAL_VIEWS.setdefault(regex, list(), )
    CONDITIONAL_VIEWS[regex].append(
            dict(
                    view=view,
                    methods=[i.upper() for i in _methods] if _methods else None,
                )
        )

    return url(regex, decorator_conditional_view(view, key=regex, ), *a, **_kw)


urlpatterns = patterns('',
    url(r'^', include("gppi.package.urls"), ),

)

