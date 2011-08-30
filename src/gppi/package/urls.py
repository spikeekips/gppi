# -*- coding: utf-8 -*-

import re
from django.conf import settings
from django.conf.urls.defaults import patterns, url

from gppi.package import views as view_package
from gppi.urls import conditional_url
from gppi.package.utils import VERSION_TAGS


RE_PACKAGE_NAME = "[A-Za-z0-9.\-]+"
RE_VERSION_TAGS = "".join(map(re.escape, VERSION_TAGS, ), )


urlpatterns = patterns("",
    url(r"^media/(?P<path>.*)$", "django.views.static.serve",
        kwargs=dict(document_root=settings.MEDIA_ROOT, ), ),
    url(r"^media/", "django.views.static.serve",
        name="gppi-media", ),

    url(r"^tags-(?P<tags>[%(vf)s][%(vf)s]*)/(?P<slug>%(pn)s)(|/)$" % dict(
            pn=RE_PACKAGE_NAME,
            vf=RE_VERSION_TAGS,
        ),
        view_package.Package.as_view(), ),
    url(r"^tags-(?P<tags>[%(vf)s][%(vf)s]*)/" % dict(vf=RE_VERSION_TAGS, ),
        view_package.PYPI.as_view(), name="gppi-pypi-dev", ),

    url(r"^(?P<slug>%s)(|/)$" % RE_PACKAGE_NAME,
        view_package.Package.as_view(), dict(tags=None, ), ),

    conditional_url(r"^", view_package.PYPI.as_view(), dict(tags=None, ),
        name="gppi-pypi", methods=("post", ), ),

    conditional_url(r"^", view_package.Packages.as_view(), dict(tags=None, ),
        name="index", methods=("get", ), ),

)


if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




