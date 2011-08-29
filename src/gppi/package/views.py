# -*- coding: utf-8 -*-


import base64
import StringIO
import cgi

from django.db import models
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from gppi._exceptions import BadRequest, Forbidden, Unauthorized
from gppi.www_basic_auth import decorator_login_required

from gppi._xmlrpc import xmlrpc_handler

import forms as forms_package
import models as models_package


class BaseView (View, ) :
    def dispatch (self, request, *a, **kw) :
        if not hasattr(request, "_form", ) :
            request._form = dict()

        request.version_tags = kw.get("tags", None, )

        if "tags" in kw :
            del kw["tags"]

        try :
            return super(BaseView, self).dispatch(request, *a, **kw)
        except (BadRequest, Forbidden, Unauthorized, ), e :
            return HttpResponse(e.content, status=e.code, )


class PYPI (BaseView, ) :
    def transmute (self, field, field_name, ) :
        from django.core.files.uploadedfile import InMemoryUploadedFile
        if hasattr(field, 'filename') and field.filename:
            _encoding = field.headers.getheader("content-transfer-encoding")
            if _encoding and _encoding.lower() == "base64" :
                _v = base64.decodestring(field.value, )
            else :
                _v = field.value

            v = InMemoryUploadedFile(
                    file=StringIO.StringIO(_v),
                    field_name=field_name,
                    name=field.filename,
                    content_type=field.type,
                    size=len(field.value),
                    charset=None,
                )
        else:
            v = field.value.decode('utf-8')

        return v

    def decode_form (self, form, ) :
        d = {}
        for k in form.keys():
            v = form[k]
            if isinstance(v, list):
                d[k] = [self.transmute(i, k, ) for i in v]
            else:
                d[k] = self.transmute(v, k, )

            if d[k] == "UNKNOWN" :
                d[k] = None

        return d

    @method_decorator(csrf_exempt, )
    def dispatch (self, request, *a, **kw) :
        try :
            request._form = self.decode_form(
                    cgi.FieldStorage(fp=request._stream, environ=request.META, ), )
        except TypeError:
            pass
        finally:
            if hasattr(request._stream, "_wrapped") :
                request._stream._wrapped.seek(0, 0, )

        return super(PYPI, self).dispatch(request, *a, **kw)

    def post (self, request, ) :
        if request.META.get("HTTP_CONTENT_TYPE") == "text/xml" :
            return HttpResponse(
                    xmlrpc_handler(request, ), content_type="text/xml", )

        if ":action" in request._form :
            return getattr(self, "_action_%s" % request._form.get(":action"), )(request, )

        return HttpResponse()

    @decorator_login_required
    def _action_submit (self, request, ) :  # register package
        _package = None
        try :
            _package = models_package.Package.objects.get(name=request._form.get("name"), )
        except models.ObjectDoesNotExist :
            pass
        else :
            if _package.owner != request.user :
                raise Forbidden("you are not owner of this package, '%s'" % request._form.get("name"), )

        _data = dict(request._form.items())
        _data["owner"] = request.user.pk

        _form = forms_package.Package(request, _data, instance=_package, )
        if not _form.is_valid() :
            raise BadRequest(_form.errors, )

        return HttpResponse(_form.save(), )

    @decorator_login_required
    def _action_file_upload (self, request, ) :
        _name = request._form.get("name")
        _package = None
        try :
            _package = models_package.Package.objects.get(name=_name, )
        except models.ObjectDoesNotExist :
            raise BadRequest("Can not find the registered package, name '%s'" % _name, )
        else :
            if _package.owner != request.user :
                raise Forbidden("you are not owner of this package, '%s'" % _name, )

        _data = dict(request._form.items())
        _data["owner"] = request.user.pk
        _data["package"] = _package.key

        _form = forms_package.Release(request, _data, request._form, )
        if not _form.is_valid() :
            raise BadRequest(_form.errors, )

        _form.save()

        # update package information
        _data = dict(request._form.items())
        _data["owner"] = request.user.pk
        _form = forms_package.Package(request, _data, instance=_package, )
        if not _form.is_valid() :
            raise BadRequest(_form.errors, )

        _form.save()
        return HttpResponse()


class Package (BaseView, DetailView, ) :
    model = models_package.Package
    slug_field = "name"

    def get_context_data (self, *a, **kw) :
        _context = super(Package, self, ).get_context_data(*a, **kw)
        _package = _context.get("package")

        try :
            _release = _package.release_set.get_latest_version(version_tags=self.request.version_tags, )[0]
        except :
            _release = None

        _context.update(release=_release, )
        return _context


class Packages (BaseView, ) :
    def get (self, request, *a, **kw) :
        return render(
                request,
                "package/index.html",
            )


if __name__ == "__main__"  :
    import doctest
    doctest.testmod()

