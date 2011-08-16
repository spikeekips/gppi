# -*- coding: utf-8 -*-

"""
##################################################
GPPi, Gamepresso Package Index
##################################################

>>> import os
>>> import sys
>>> import shutil
>>> import tempfile

>>> from django.conf import settings
>>> import gppi.package.models as models_package
>>> import gppi.package.forms as forms_package

>>> settings.MEDIA_ROOT = "/tmp/kkk"
>>> if os.path.exists(settings.MEDIA_ROOT) :
...     shutil.rmtree(settings.MEDIA_ROOT, )


>>> TEST_PACKAGES = {
...         "2011.08.09.16.37.51dev": "test-package-2011.08.09.16.37.51dev.tar.bz2",
...         "2011.08.09.16.38.26":    "test-package-2011.08.09.16.38.26.tar.bz2",
...         "2011.08.09.16.38.26dev": "test-package-2011.08.09.16.38.26dev.tar.bz2",
...         "2011.08.09.16.39.26dev": "test-package-2011.08.09.16.39.26dev.tar.bz2",
...    }



Test `setup.py`
################################################################################

>>> from distutils.dist import Distribution

At first, to run the `setup.py` command, write `.pypirc` file.

>>> _pypirc = \"\"\"
... [distutils]
... index-servers =
...     pypi
... \\t
... [pypi]
... index-url:%(url_pypi)s
... repository:%(url_pypi)s
... username:replica
... password:replica
... \\t
... \"\"\" % dict(url_pypi=URL_GPPI_PYPI, )

>>> _rc_dist = os.path.join(TEMPDIR, ".pypirc")
>>> with file(_rc_dist, "w", ) as f :
...     f.write(_pypirc, )


Authentication
================================================================================

To make the test simple, only use the 'django.contrib.auth.backends.ModelBackend',

>>> settings.AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', )

>>> from django.contrib.auth import models as models_auth, authenticate
>>> user_credentials_other = dict(username="replica0", password="replica", )
>>> _user_other = models_auth.User.objects.create_user(
...        email="replica0@localhost.com", **user_credentials_other)

>>> user_credentials = dict(username="replica", password="replica", )
>>> _user = models_auth.User.objects.create_user(
...        email="test-user@localhost.com", **user_credentials)

>>> from gppi.www_basic_auth import create_credential_header
>>> authenticate(**user_credentials).username == user_credentials.get("username")
True



`setup.py` `register`
================================================================================


don't print the log message,

>>> from distutils.log import _global_log
>>> _global_log._log = lambda *a, **kw: None


>>> _metadata = dict(
...         url="http://a.com",
...         author="spikeekips",
...         author_email="spikeekips@gmail.com",
...         name="gp.test",
...         license="License :: Other/Proprietary License",
...         classifiers=["Framework :: Gamepresso", "Environment :: Console", ],
...     )

We must give the valid authentication credential to authenticate to the server,
if invalid credential, it occurs error.

>>> register_package(
...        _metadata, create_credential_header(**user_credentials), ) # doctest:+ELLIPSIS
Using PyPI login from /var/folders/.../.pypirc
Server response (200): OK


If you try to register with the other user,
>>> register_package(_metadata, create_credential_header(
...    **user_credentials_other), ) # doctest:+ELLIPSIS
Using PyPI login from /var/folders/.../.pypirc
Server response (403): OK

>>> register_package(_metadata, create_credential_header(
...    **dict(username="incorrect", password="incorrect", )), ) # doctest:+ELLIPSIS
Using PyPI login from /var/folders/.../.pypirc
Server response (401): OK


Check in the models

>>> models_package.Package.objects.filter(
...        name=_metadata.get("name"), author=_metadata.get("author"), ).count() == 1
True
>>> _package = models_package.Package.objects.get(name=_metadata.get("name"), )
>>> [i.name for i in _package.classifiers.all()]
[u'Environment :: Console', u'Framework :: Gamepresso']


Package Versioning & Ordering
================================================================================

>>> from gppi.package.utils import parse_version
>>> pkg_resources.parse_version("0.1") < pkg_resources.parse_version("0.1-1")
True
>>> pkg_resources.parse_version("0.1") > pkg_resources.parse_version("0.1dev")
True
>>> pkg_resources.parse_version("0.1-1") > pkg_resources.parse_version("0.1dev")
True
>>> pkg_resources.parse_version("0.1-1") > pkg_resources.parse_version("0.1-1dev")
True

>>> parse_version("0.1")
('0.1', '0.1', 'f')
>>> parse_version("0.1-1")
('0.1-1', '0.1', 'g')
>>> parse_version("0.1dev")
('0.1dev', '0.1', '@')
>>> parse_version("0.1rc")
('0.1rc', '0.1', 'c')
>>> parse_version("0.1-1dev")
('0.1-1dev', '0.1', '@g')
>>> parse_version("0.1-1dev1rc")
('0.1-1dev1rc', '0.1', '@cg')
>>> parse_version("0.1a")
('0.1a', '0.1', 'f')

>>> _versions = (
...     "0.1",
...     "0.1dev",
...     "0.1-1",
...     "0.2",
...     "0.2dev",
...     "0.2rc",
... )

>>> for i in _versions :
...     _form = forms_package.Release(None, dict(owner=_user.pk, package=_package.key, version=i, ), )
...     None if _form.is_valid() else _form.errors
...     if not _form.is_valid() :
...         print "failed to validate form", _form.errors
...         break
...     None if _form.save() else "failed to save for the version, %s" % i

>>> [(i.version, i.version_base, i.version_tags, ) for i in _package.release_set.all()]
[(u'0.2', u'0.2', u'f'), (u'0.2rc', u'0.2', u'c'), (u'0.2dev', u'0.2', u'@'), (u'0.1-1', u'0.1', u'g'), (u'0.1', u'0.1', u'f'), (u'0.1dev', u'0.1', u'@')]


`setup.py` `upload`
================================================================================

clean up the previous, ::

before `register`, the command `upload` can not be accomplished, ::

>>> models_package.Package.objects.all().delete()

if just `upload` before `register`, it comes with `Forbidden`(403).

>>> _metadata = dict(
...         name="gp.test",
...         version="2011.08.09.16.38.26dev",
...     )

>>> _distattr = dict(
...         dist_files=(
...             ("sdist", "",
...                 os.path.dirname(__file__) + "/" + TEST_PACKAGES.get("2011.08.09.16.38.26dev"), ),
...         ),
...     )
>>> upload_package(_distattr, _metadata, create_credential_header(**user_credentials), )
Server response (400): OK


so, `register` first, ::

>>> _metadata = dict(
...         url="http://a.com",
...         author="spikeekips",
...         author_email="spikeekips@gmail.com",
...         name="gp.test",
...         license="License :: Other/Proprietary License",
...         classifiers=["Framework :: Gamepresso", "Environment :: Console", ],
...     )

>>> register_package(
...        _metadata, create_credential_header(**user_credentials), ) # doctest:+ELLIPSIS
Using PyPI login from /var/folders/.../.pypirc
Server response (200): OK


upload
--------------------------------------------------------------------------------

>>> _metadata = dict(
...         author="spikeekips",
...         author_email="spikeekips@gmail.com",
...         name="gp.test",
...         version="2011.08.09.16.38.26dev",
...         classifiers=["Framework :: Gamepresso", "Environment :: Console", ],
...     )

>>> _distattr = dict(
...         dist_files=(
...             ("sdist", "",
...                 os.path.dirname(__file__
...                     ) + "/" + TEST_PACKAGES.get("2011.08.09.16.38.26dev", ), ),
...         ),
...     )
>>> upload_package(_distattr, _metadata, create_credential_header(**user_credentials), )
Server response (200): OK



Check the uploaded file in the models

>>> _package = models_package.Package.objects.get(name=_metadata.get("name"), )
>>> _package.release_set.all().count() == 1
True
>>> _release = _package.release_set.all()[0]
>>> _release.version == _metadata.get("version")
True
>>> (_version, _version_base, _version_tags, ) = parse_version(_release.version, )
>>> _release.version_base == _version_base
True
>>> _release.version_tags == _version_tags
True

>>> _release.author == _package.author
True
>>> list(_release.classifiers.all(), ) == list(_package.classifiers.all(), )
True


Test `pip`
################################################################################

`pip` `search`
================================================================================

clean up the previous ones,

>>> models_package.Release.objects.all().delete()

register and upload package.

>>> _metadata = dict(
...         url="http://a.com",
...         author="spikeekips",
...         author_email="spikeekips@gmail.com",
...         name="common",
...         license="License :: Other/Proprietary License",
...         classifiers=["Framework :: Gamepresso", "Environment :: Console", ],
...     )

>>> register_package(
...        _metadata, create_credential_header(**user_credentials), ) # doctest:+ELLIPSIS
Using PyPI login from /var/folders/.../.pypirc
Server response (200): OK

>>> _files_version = [i for i in TEST_PACKAGES.keys() if i.find("dev") != -1]
>>> for _version in _files_version :
...    _metadata = dict(
...            name="common",
...            version=_version,
...        )
...    _distattr = dict(
...            dist_files=(
...                ("sdist", "", os.path.dirname(__file__) + "/" + TEST_PACKAGES.get(_version), ),
...            ),
...        )
...    upload_package(_distattr, _metadata, create_credential_header(**user_credentials), )
Server response (200): OK
Server response (200): OK
Server response (200): OK


`search`
--------------------------------------------------------------------------------

>>> import xmlrpclib, sys
>>> from pip.commands import search as search_pip

Create xmlrpc query,

>>> _query = dict(name=["common"], )
>>> _body = xmlrpclib.dumps((_query, "or", ), "search", )
>>> _response = client.post_raw(PATH_GPPI_PYPI_DEV, _body, **dict(HTTP_CONTENT_TYPE="text/xml", ))
>>> _o = xmlrpclib.loads(_response.content, )[0][0]
>>> print_results(search_pip.transform_hits(_o, ), )
common                    -
  INSTALLED: 0.0.0
  LATEST:    2011.08.09.16.39.26dev


`search` multiple packages
--------------------------------------------------------------------------------

>>> _metadata = dict(
...         url="http://a.com",
...         author="spikeekips",
...         author_email="spikeekips@gmail.com",
...         description="common",
...         name="zurich",
...         license="License :: Other/Proprietary License",
...         classifiers=["Framework :: Gamepresso", "Environment :: Console", ],
...     )

>>> register_package(
...        _metadata, create_credential_header(**user_credentials), ) # doctest:+ELLIPSIS
Using PyPI login from /var/folders/.../.pypirc
Server response (200): OK

if dev and official release,

>>> _files_version = TEST_PACKAGES.keys()
>>> for _version in _files_version :
...    _metadata = dict(
...            name="zurich",
...            version=_version,
...        )
...    _distattr = dict(
...            dist_files=(
...                ("sdist", "", os.path.dirname(__file__) + "/" + TEST_PACKAGES.get(_version), ),
...            ),
...        )
...    upload_package(_distattr, _metadata, create_credential_header(**user_credentials), )
Server response (200): OK
Server response (200): OK
Server response (200): OK
Server response (200): OK


`search` by `name`
................................................................................

>>> _query = dict(name=["common", "zurich", ], )
>>> _body = xmlrpclib.dumps((_query, "or", ), "search", )
>>> _response = client.post_raw(PATH_GPPI_PYPI_DEV, _body, **dict(HTTP_CONTENT_TYPE="text/xml", ))
>>> _o = xmlrpclib.loads(_response.content, )[0][0]
>>> print_results(search_pip.transform_hits(_o, ), )
zurich                    -
  INSTALLED: 0.0.0
  LATEST:    2011.08.09.16.39.26dev
common                    -
  INSTALLED: 0.0.0
  LATEST:    2011.08.09.16.39.26dev


`search` by `name` and `summary`
................................................................................

>>> _query = dict(name=["common", ], summary=["common", ], )
>>> _body = xmlrpclib.dumps((_query, "or", ), "search", )
>>> _response = client.post_raw(PATH_GPPI_PYPI_DEV, _body, **dict(HTTP_CONTENT_TYPE="text/xml", ))
>>> _o = xmlrpclib.loads(_response.content, )[0][0]
>>> print_results(search_pip.transform_hits(_o, ), )
common                    -
  INSTALLED: 0.0.0
  LATEST:    2011.08.09.16.39.26dev


`pip` `install`
================================================================================

when you run the `pip` `install` command, `pip` is trying to find the package page in pypi server.

>>> client.get(PATH_GPPI_PYPI + "zurich/",
...        **create_credential_header(**user_credentials)).content # doctest:+ELLIPSIS
'...test-package-2011.08.09.16.39.26dev.tar...
>>> client.get(PATH_GPPI_PYPI + "tags-f/" + "zurich/",
...        **create_credential_header(**user_credentials)).content # doctest:+ELLIPSIS
'...test-package-2011.08.09.16.38.26.tar...'
>>> client.get(PATH_GPPI_PYPI_DEV + "zurich/", **create_credential_header(**user_credentials)).content
'...test-package-2011.08.09.16.39.26dev.tar...'


"""


import sys
import os
import hashlib
import platform
import urlparse
import StringIO
import tempfile
from base64 import standard_b64encode

# To fake the setuptools, which trying to find `.pypirc` in $HOME, use fake user HOME.
TEMPDIR = tempfile.mkdtemp()
os.environ["HOME"] = TEMPDIR

from django.test import client as client_test

from setuptools.command.register import register
from setuptools.command.upload import upload
from distutils.dist import Distribution

from django.core.urlresolvers import reverse
PATH_GPPI_PYPI = reverse("gppi-pypi")
PATH_GPPI_PYPI_DEV = reverse("gppi-pypi-dev", kwargs=dict(tags="@"), )
URL_GPPI_PYPI = "http://testserver%s" % PATH_GPPI_PYPI
URL_GPPI_PYPI_DEV = "http://testserver%s" % PATH_GPPI_PYPI_DEV


class FakePayload (client_test.FakePayload, ) :
    def __init__ (self, *a, **kw) :
        super(FakePayload, self).__init__(*a, **kw)
        self.readline = self.__content.readline
        self._wrapped = self.__content


class Client (client_test.Client, ) :
    def post_raw (self, path, post_data, content_type=client_test.MULTIPART_CONTENT, **extra) :
        parsed = urlparse.urlparse(path)
        _r = {
            "CONTENT_LENGTH": len(post_data),
            "CONTENT_TYPE": content_type,
            "PATH_INFO": self._get_path(parsed),
            "QUERY_STRING": parsed[4],
            "REQUEST_METHOD": "POST",
            "wsgi.input": FakePayload(post_data, ),
        }
        _r.update(extra)
        return self.request(**_r)


def post_to_server (data, auth=None, ):
    boundary = "--------------GHSKFJDLGDS7543FJKLFHRE75642756743254"
    sep_boundary = "\n--" + boundary
    end_boundary = sep_boundary + "--"
    body = StringIO.StringIO()
    for key, value in data.items() :
        if type(value) not in (type([]), ) :
            value = [value]

        for value in value:
            body.write(sep_boundary)

            _headers = list()
            if type(value) in (tuple, ) :
                key = "%s\"; filename=\"%s" % (key, value[0], )
                value = value[1]
                _headers.append("\nContent-Type: application/octet-stream")
                _headers.append("\nContent-Transfer-Encoding: base64")

            body.write("\nContent-Disposition: form-data; name=\"%s\"" % key, )
            for i in _headers :
                body.write(i, )

            body.write("\n\n")
            body.write(value)
            if value and value[-1] == "\r":
                body.write("\n")
    body.write(end_boundary)
    body.write("\n")
    body = body.getvalue()

    # build the Request
    headers = {
        "Content-type": "multipart/form-data; boundary=%s; charset=utf-8" % boundary,
        "Content-length": str(len(body))
    }
    return (body, headers, auth, )


def upload_file (dist, command, pyversion, filename, ) :
    import base64
    content = open(filename, 'rb').read()
    meta = dist.distribution.metadata
    data = {
        # action
        ':action': 'file_upload',
        'protcol_version': '1',

        # identify release
        'name': meta.get_name(),
        'version': meta.get_version(),

        # file content
        'content': (os.path.basename(filename), base64.encodestring(content).rstrip(), ),
        'filetype': command,
        'pyversion': pyversion,
        'md5_digest': hashlib.md5(content).hexdigest(),

        # additional meta-data
        'metadata_version' : '1.0',
        'summary': meta.get_description(),
        'home_page': meta.get_url(),
        'author': meta.get_contact(),
        'author_email': meta.get_contact_email(),
        'license': meta.get_licence(),
        'description': meta.get_long_description(),
        'keywords': meta.get_keywords(),
        'platform': meta.get_platforms(),
        'classifiers': meta.get_classifiers(),
        'download_url': meta.get_download_url(),
        # PEP 314
        'provides': meta.get_provides(),
        'requires': meta.get_requires(),
        'obsoletes': meta.get_obsoletes(),
        }
    comment = ''
    if command == 'bdist_rpm':
        dist, version, id = platform.dist()
        if dist:
            comment = 'built for %s %s' % (dist, version)
    elif command == 'bdist_dumb':
        comment = 'built for %s' % platform.platform(terse=1)
    data['comment'] = comment

    if dist.sign:
        data['gpg_signature'] = (os.path.basename(filename) + ".asc",
                                 open(filename + ".asc").read())

    auth = "Basic " + standard_b64encode(dist.username + ":" + dist.password)

    return (data, auth, )


client = Client()


class FakeServer(object):
    def __init__ (self, headers=dict(), ) :
        self._headers = headers

    def __call__ (self, *args) :
        (_body, _headers, _auth, ) = post_to_server(*args)
        _headers = dict(map(lambda x : (x[0].replace("-", "_").upper(), x[1], ), _headers.items()))
        _headers.update(self._headers)
        _response = client.post_raw(PATH_GPPI_PYPI, _body, **_headers)
        return _response.status_code, "OK"


class FakeServerUpload (FakeServer, ) :
    def __init__ (self, dist, headers=dict(), ) :
        self._dist = dist

        super(FakeServerUpload, self).__init__(headers, )

    def __call__ (self, *args) :
        (_status_code, _msg, ) = super(
                FakeServerUpload, self).__call__(*upload_file(self._dist, *args))
        print "Server response (%s): %s" % (_status_code, _msg, )
        return (_status_code, _msg, )


def register_package (metadata, headers=dict(), ) :
    _dist = Distribution(dict(script_name="/tmp/", verbose=-1, ))

    for k, v in metadata.items() :
        setattr(_dist.metadata, k, v, )

    if "-q" not in sys.argv :
        sys.argv.append("-q")

    register.DEFAULT_REPOSITORY = URL_GPPI_PYPI
    _cmd = register(_dist)
    _cmd.announce = lambda a, b=None: sys.stdout.write(a + "\n")

    _cmd.post_to_server = FakeServer(headers, )
    _cmd.run()


def upload_package (distattr, metadata, headers=dict(), ) :
    _dist = Distribution(dict(script_name="/tmp/", ))

    for k, v in distattr.items() :
        setattr(_dist, k, v, )

    for k, v in metadata.items() :
        setattr(_dist.metadata, k, v, )

    upload.DEFAULT_REPOSITORY = URL_GPPI_PYPI
    _cmd = upload(_dist)
    _cmd.announce = lambda a, b=None: sys.stdout.write(a + "\n")

    _cmd.upload_file = FakeServerUpload(_cmd, headers, )
    _cmd.run()


import textwrap
import pkg_resources
from pip.commands.search import highest_version


def print_results(hits, name_column_width=25, terminal_width=None):
    installed_packages = [p.project_name for p in pkg_resources.working_set]
    for hit in hits:
        name = hit['name']
        summary = hit['summary'] or ''
        if terminal_width is not None:
            # wrap and indent summary to fit terminal
            summary = textwrap.wrap(summary, terminal_width - name_column_width - 5)
            summary = ('\n' + ' ' * (name_column_width + 3)).join(summary)
        line = '%s - %s' % (name.ljust(name_column_width), summary)
        try:
            print (line)
            dist = pkg_resources.get_distribution(name) if name in installed_packages else None
            try:
                latest = highest_version(hit['versions'])
                if dist and dist.version == latest:
                    print '  INSTALLED: %s (latest)' % dist.version
                else:
                    print '  INSTALLED: %s' % "0.0.0"
                    print '  LATEST:    %s' % latest
            finally:
                pass
        except UnicodeEncodeError:
            pass


if __name__ == "__main__"  :
    import doctest
    doctest.testmod()


