# -*- coding: utf-8 -*-


import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.http import HttpResponse

from package import models as models_package


class XMLRPCHandler (SimpleXMLRPCDispatcher, ) :
    def __init__ (self, ) :
        SimpleXMLRPCDispatcher.__init__(self, True, "utf-8", )

        #self.register_function(self._list_packages)
        #self.register_function(self._package_releases, )
        #self.register_function(self._release_urls)
        #self.register_function(self._release_urls, name="package_urls") # Deprecated
        #self.register_function(self._release_data)
        #self.register_function(self._release_data, name="package_data") # Deprecated
        self.register_function(self._search, name="search", )
        #self.register_function(self._updated_releases)
        #self.register_function(self._changelog)
        #self.register_function(self._changed_packages)
        #self.register_function(self._post_cheesecake_for_release)

        self.register_introspection_functions()
        self.register_multicall_functions()

    def __call__ (self, request, ) :
        request._stream._wrapped.seek(0, 0, )
        _d = self._marshaled_dispatch(
                request._stream.read(),
                dispatch_method=self._decorator_dispatch(request, ),
            )
        request._stream._wrapped.seek(0, 0, )

        _response = HttpResponse(_d, status=200, )
        _response["content-type"] = "text/xml"
        _response["charset"] = "UTF-8"
        _response["content-length"] = len(_d, )

        return _response

    def _decorator_dispatch (self, request, ) :
        def wrapper (method, params, ) :
            return self._dispatch(method, list(params) + [request, ], )

        return wrapper

    def system_multicall (self, call_list, ) :
        if len(call_list) > 100 :
            raise xmlrpclib.Fault, "multicall too large"

        return SimpleXMLRPCDispatcher.system_multicall(self, call_list)

    def _search (self, spec, op, request, ) :
        def _as_dict (release, pool, ) :
            pool.append(
                dict(
                    name=release.package.name,
                    version=release.version,
                    summary=release.summary,
                    _pypi_ordering=len(pool),
                ),
            )

        op = op.lower() if op.lower() in ("and", "or", ) else "or"

        _q = Q()
        for k, v in spec.items() :
            try :
                models_package.Package._meta.get_field(k, )
            except FieldDoesNotExist :
                continue

            for j in v :
                _q = (_q.__and__ if op == "and" else _q.__or__)(
                        Q(**{"%s__icontains" % k: j.lower(), }), )

        _qs = models_package.Package.objects.filter(_q, )
        if _qs.count() < 1 :
            return list()

        # sort by it's name
        _s = map(lambda x : (x.name, x, ), _qs, )
        _s.sort()

        _pool = list()
        for (_name, _package, ) in _s :
            _qs = _package.release_set.get_latest_version(version_tags=request.version_tags, )
            map(lambda x : _as_dict(x, _pool, ), _qs, )

        return _pool


xmlrpc_handler = XMLRPCHandler()

