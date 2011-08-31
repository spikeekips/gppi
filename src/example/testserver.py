#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import resource

from twisted.scripts._twistd_unix import ServerOptions
from twisted.python import usage
from twisted.application import service, strports
from twisted.internet import reactor
from twisted.web import server, wsgi, http, resource as resource_web


class HTTPFactory (server.Site, ) :
    LOG_FORMAT_STAND = """
     ========================================================
     Call Type: %s
     ........................................................
     User From: %s (x-forwarded-for: %s)
          Host: %s
        Header: %s
        Status: %s
     Byte Sent: %s
     ........................................................
    User-Agnet: %s
       Referer: %s
    """
    LOG_FORMAT = """%s - %s [%s] "%s" %s %s "%s" "%s"
    """

    def __init__ (self, *a, **kw) :
        self._is_stand = kw.get("is_stand", )
        if "is_stand" in kw :
            del kw["is_stand"]

        server.Site.__init__(self, *a, **kw)

    def log (self, request, ) :
        firstLine = "%s %s HTTP/%s" % (
            request.method,
            request.uri,
            ".".join([str(x) for x in request.clientproto]), )

        _remote_addr = request.getHeader("x-forwarded-for", )
        if not _remote_addr :
            _remote_addr = request.getClientIP()

        if not self._is_stand and self.logFile :
            self.logFile.write(
                 self.LOG_FORMAT % (
                    _remote_addr,
                    #request.getClientIP(),
                    # XXX: Where to get user from?
                    "-",
                    http.datetimeToLogString(),
                    firstLine,
                    request.code,
                    request.sentLength or "-",
                    self._escape(request.getHeader("referer") or "-"),
                    self._escape(request.getHeader("user-agent") or "-"),
                    )
                )

        if self._is_stand :
            self.logFile.write(
                self.LOG_FORMAT_STAND % (
                        request.getHeader("x-requested-with") or "",
                        request.getClientIP(),
                        _remote_addr if request.getHeader("x-forwarded-for") else "",
                        request.host,
                        firstLine,
                        request.code,
                        request.sentLength or "-",
                        self._escape(request.getHeader("user-agent") or "-"),
                        self._escape(request.getHeader("referer") or "-"),
                    )
                )


class RootResource (resource_web.Resource, ) :
    def __init__ (self, ) :
        resource_web.Resource.__init__(self, )
        self.resource = None

    def getChild (self, path, request, ) :
        if self.resource is None :
            raise RuntimeError("there is no resource.")

        _path = request.prepath.pop(0, )
        request.postpath.insert(0, _path, )

        return self.resource


class WSGIServer (object, ) :
    def __init__ (
                self,
                name,
                port=8000,
                interface=None,
                pool_size=500,
                is_stand=False,
                http_factory=None,
            ) :

        self._name         = name
        self._port         = port
        self._interface    = interface
        self._pool_size    = pool_size
        self._is_stand     = is_stand
        self._http_factory = http_factory

        self._resource = RootResource()

    def putChild_by_handler (self, name, handler, ) :
        _thread = reactor.getThreadPool()
        _thread.adjustPoolsize(0, self._pool_size, )

        # Allow Ctrl-C to get you out cleanly:
        reactor.addSystemEventTrigger('after', 'shutdown', _thread.stop, )

        self.putChild(name, wsgi.WSGIResource(reactor, _thread, handler, ), )

    def putChild (self, name, _resource, ) :
        if self._resource.resource is None :
            self._resource.resource = _resource
            return

        self._resource.putChild(name, _resource, )

    def run (self, ) :
        application = service.Application(self._name, )

        if self._http_factory is None :
            http_factory = HTTPFactory

        _factory = http_factory(
                self._resource,
                is_stand=self._is_stand,
            )

        _s = strports.service(
            "tcp:%d%s" % (
                int(self._port),
                ((":interface=%s" % self._interface) if self._interface else ""),
            ),
            _factory,
        )
        _s.setServiceParent(application, )

        return application


class WSGIServerDjango (WSGIServer, ) :
    def run (self, ) :
        from django.core.handlers.wsgi import WSGIHandler as WSGIHandler_django
        self.putChild_by_handler("", WSGIHandler_django(), )

        return super(WSGIServerDjango, self).run()


class Options (ServerOptions, ) :
    synopsis = "Usage: %s [options]" % os.path.basename(sys.argv[0])
    optFlags = (
        ["vv", None, "verbose", ],
    )
    optParameters = (
        ["wsgiserver", None, None, "wsgiserver module path", ],
        ["root", None, "./", "application root path", ],
        ["port", None, "8080", "listen port", ],
        ["django-settings", None, "settings", "django settings module name", ],
        ["interface", None, None, "listen interface, usually IP address", ],
        ["pool_size", None, "500", "server thread pool size", ],
        ["logfile", None, "/tmp/twisted.log", "log to a specified file, - for stdout", ],
        ["pidfile", None, "/tmp/twisted.pid", "Name of the pidfile [default: twistd.pid]", ],
    )
    unused_short = ("-o", "-f", "-s", "-y", "-d", )
    unused_long = ("--rundir=", "--python=", "--savestats", "--no_save",
        "--encrypted", "--file=", "--source=", "--originalname", )

    def __init__ (self, *a, **kw) :
        ServerOptions.__init__(self, *a, **kw)

        for i in self.unused_long :
            if self.longOpt.count(i[2:]) > 0 :
                del self.longOpt[self.longOpt.index(i[2:])]

    def parseOptions (self, *a, **kw) :
        self._skip_reactor = kw.get("skip_reactor")
        if "skip_reactor" in kw :
            del kw["skip_reactor"]

        super(Options, self).parseOptions(*a, **kw)

        if self.get("nodaemon") and self.get("logfile") :
            self["logfile"] = None

        if not self.get("django-settings") :
            raise usage.UsageError("'django-settings' must be given.", )

        if not self.get("wsgiserver") :
            self["wsgiserver"] = WSGIServerDjango

        if not self.get("root") :
            raise usage.UsageError("'root' must be given and valid path.", )

        if not self.get("port") :
            raise usage.UsageError("'port' must be int value.", )

        self.opt_port(self.get("port"), )
        self.opt_pool_size(self.get("pool_size"), )

    def opt_root (self, value, ) :
        _path = os.path.abspath(os.path.expanduser(value, ))
        if not os.path.exists(_path) :
            raise usage.UsageError("'root' must be given and valid path.", )

        self["root"] = _path

    def opt_wsgiserver (self, value, ) :
        try :
            self["wsgiserver"] = getattr(__import__(value, None, None, ("wsgiserver", ), ), "WSGIServer", )
        except (ImportError, AttributeError, ) :
            raise usage.UsageError("'wsgiserver' must be valid python module path.", )

    def opt_port (self, value, ) :
        try :
            self["port"] = int(value, )
        except ValueError :
            raise usage.UsageError("invalid `port`, '%s', it must be int value." % value, )

    def opt_pool_size (self, value, ) :
        try :
            self["pool_size"] = int(value, )
        except ValueError :
            raise usage.UsageError(
                "invalid `pool_size`, '%s', it must be int value." % value, )

    def opt_vv (self, value, ) :
        del self["vv"]
        self["verbose"] = True

    def opt_reactor (self, v, ) :
        if self._skip_reactor :
            return
        return ServerOptions.opt_reactor(self, v, )


if __name__ == "__builtin__"  :
    _options = Options()
    _options.parseOptions(skip_reactor=True, )

    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024, ), )

    sys.path.insert(0, _options.get("root"), )

    os.environ["DJANGO_SETTINGS_MODULE"] = _options.get("django-settings")

    application = _options.get("wsgiserver")(
        "%s:%s" % (_options.get("django-settings"), _options.get("port"), ),
        port=_options.get("port"),
        interface=_options.get("interface"),
        pool_size=_options.get("pool_size"),
        is_stand=_options.get("nodaemon"),
    ).run()

elif __name__ == "__main__"  :
    _found = False
    _n = list()
    _n.append(sys.argv[0], )
    for i in sys.argv[1:] :
        if _found :
            _found = False
            continue
        elif i in Options.unused_short :
            _found = True
            continue
        elif filter(i.startswith, Options.unused_long, ) :
            continue

        _n.append(i, )

    _n.extend(["-y", __file__, ], )
    sys.argv = _n

    from twisted.application import app
    from twisted.scripts.twistd import runApp
    app.run(runApp , Options, )




if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




