# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
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

