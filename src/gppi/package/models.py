# -*- coding: utf-8 -*-

import os
from django.conf import settings
from django.db.models import Q
from django.contrib.auth import models as models_auth

from gppi import models
from gppi.models import manager, query


class Classifier (models.Model, ) :
    name                = models.CharField(max_length=200, unique=True, db_index=True, )

    def __unicode__ (self, ) :
        return self.name


class BasePackage (models.Model, ) :
    class Meta :
        abstract = True

    owner               = models.ForeignKey(models_auth.User, )
    time_added          = models.DateTimeField(auto_now_add=True, )
    time_updated        = models.DateTimeField(auto_now=True, )

    author              = models.CharField(max_length=200, db_index=True, blank=True, null=True, )
    author_email        = models.EmailField(db_index=True, blank=True, null=True, )
    classifiers         = models.ManyToManyField(Classifier, blank=True, null=True, )
    description         = models.TextField(blank=True, null=True, )
    summary             = models.TextField(blank=True, null=True, )
    download_url        = models.URLField(verify_exists=False, blank=True, null=True, )
    home_page           = models.URLField(verify_exists=False, blank=True, null=True, )

    comment             = models.TextField(blank=True, null=True, )
    protocol_version    = models.CharField(max_length=100, blank=True, null=True, )
    pyversion           = models.CharField(max_length=100, blank=True, null=True, )
    platform            = models.CharField(max_length=100, blank=True, null=True, )
    metadata_version    = models.CharField(max_length=100, blank=True, null=True, )


class Package (BasePackage, ) :
    class Meta :
        unique_together = ("name", )

    name                = models.CharField(max_length=200, db_index=True, unique=True, )
    license             = models.ForeignKey(Classifier, blank=True, null=True, related_name="package_license", )

    def __unicode__ (self, ) :
        return self.name


class ReleaseQuerySet (query.QuerySet, ) :
    def get_latest_version (self, version_tags=None, package=None, ) :
        _q = Q()
        if version_tags :
            if type(version_tags) not in (list, ) :
                version_tags= list(version_tags )

            version_tags.sort()
            _q = _q & Q(version_tags__icontains="".join(version_tags ), )

        if package :
            _q = _q & Q(package=package, )

        return self.filter(_q, )


class ReleaseManager (manager.Manager, ) :
    def get_query_set (self, ) :
        return ReleaseQuerySet(self.model, using=self._db, )

    def get_latest_version (self, *a, **kw) :
        return self.get_query_set().get_latest_version(*a, **kw)

    def get_latest_version_dev (self, *a, **kw) :
        kw["tags"] = list(kw["tags"]) + ["@", ]
        return self.get_latest_version(*a, **kw)


from django.db.models.fields.files import FieldFile as FieldFile_django
class FieldFile (FieldFile_django, ) :
    @property
    def basename (self, ) :
        return os.path.basename(self.name, )


class FileField (models.FileField, ) :
    attr_class = FieldFile


class Release (BasePackage, ) :
    objects = ReleaseManager()

    class Meta :
        unique_together = ("package", "version", )
        ordering = ("-version_base", "-version_tags", "-version", "time_updated", )

    package         = models.ForeignKey(Package, )
    license         = models.ForeignKey(Classifier, blank=True, null=True, related_name="release_license", )

    version         = models.CharField(max_length=200, db_index=True, )
    version_base    = models.CharField(max_length=200, db_index=True, blank=True, null=True, )
    version_tags    = models.CharField(max_length=200, db_index=True, blank=True, null=True, )

    content         = FileField(upload_to=settings.MEDIA_ROOT_RELEASE,
            max_length=200, blank=True, null=True, )
    filetype        = models.CharField(max_length=100, blank=True, null=True, )
    md5_digest      = models.CharField(max_length=32, blank=True, null=True, )

    def __unicode__ (self, ) :
        return u"%s-%s%s" % (
                self.package.name,
                self.version,
                ("(%s)" % self.version_tags) if self.version_tags else "",
            )




if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




