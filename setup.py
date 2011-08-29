# -*- coding: utf-8 -*-

import glob
import pkg_resources
import shutil
import os
import string

from setuptools import setup, find_packages
from distutils.command.clean import clean as clean_orig


class clean (clean_orig, ) :
    user_options = clean_orig.user_options
    user_options.extend((
           ('extras=', 'E', "the files and directories to clean up, with `glob` expression." ""),
           ('not-dist', 'N', "don't touch the dist directory" ""),
        ), )

    def initialize_options (self, ) :
        clean_orig.initialize_options(self, )
        self.extras = ""
        self.not_dist = False

    def finalize_options (self, ) :
        clean_orig.finalize_options(self, )

        self.set_undefined_options("build", ("extras", "extras", ), )
        self.set_undefined_options("build", ("not-dist", "not_dist", ), )
        self.extras = filter(string.strip, self.extras.split(), )

    def _get_egg_info_name (self, ) :
        _egg_name = pkg_resources.safe_name(self.distribution.get_name(), )
        return os.path.join(
            (self.distribution.package_dir or dict()).get("", os.curdir, ),
            (pkg_resources.to_filename(_egg_name, ) + ".egg-info"),
        )


    def run (self, ) :
        clean_orig.run(self, )

        # remove *.pyc, *.pyo
        for _d, _sd, _fs in os.walk(".") :
            _t = filter(
                    lambda x : not x.startswith(".") and (x.endswith(".pyc") or x.endswith(".pyo")),
                    _fs, )

            if not _t :
                continue

            map(os.remove, map(lambda x : os.path.join(_d, x, ), _t, ), )

        # remove useless directories
        _t = self.extras + ["build", self._get_egg_info_name(), ]
        if not self.not_dist :
            _t.append("dist", )
        else :
            _t.append("*.egg", )

        for i in _t :
            for j in glob.glob(i, ) :
                if os.path.isdir(j) :
                    shutil.rmtree(j)
                else :
                    os.remove(j)

        # remove all the temporary *.egg-info directories
        for _r, _ds, _fs in os.walk("..") :
            for _d in _ds :
                if os.path.basename(os.path.dirname(_d, )).startswith(".") :
                    continue

                if _d.endswith(".egg-info") :
                    shutil.rmtree(os.path.join(_r, _d, ), )


setup(
    cmdclass=dict(clean=clean, ),
    name="gppi",
    version="0.2",
    description="Local PYPI server",
    author="spikeekips",
    author_email="spikeekips@gmail.com",
    url="http://github.com/spikeekips/gppi/",
    download_url="http://github.com/spikeekips/gppi/",
    platforms=["Any", ],
    license="License :: OSI Approved :: GNU General Public License (GPL)",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Communications :: File Sharing",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development",
        "Topic :: Software Development :: Version Control",
        "Topic :: System :: Archiving :: Packaging",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Software Distribution",
    ],

    install_requires=(
        "pip>=1.0.1",
        "setuptools>=0.5",
        "django>=1.3",
    ),

    zip_safe=False,
    include_package_data=True,

    package_dir={"": "src", },
    packages=find_packages("src", exclude=("pypi", "example", ), ),
    test_suite="tests.run",
)

