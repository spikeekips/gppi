# -*- coding: utf-8 -*-

import pkg_resources
from django.db import models
from django import forms

from gppi._exceptions import Forbidden

import models as models_package
import utils as utils_package

class BasePackage (forms.ModelForm, ) :
    def __init__ (self, request, *a, **kw) :
        self._request = request

        super(BasePackage, self).__init__(*a, **kw)
        self.data_orig = dict(self.data.items())
        self.data = dict(self.data.items())


    def full_clean (self, *a, **kw) :
        if "protcol_version" in self.data :
            self.data["protocol_version"] = self.data["protcol_version"]

        _objects = models_package.Classifier.objects

        self.data["classifiers"] = list(filter(
                lambda x : x is not None,
                map(
                    lambda x : _objects.get(name=x,
                        ).key if _objects.filter(name=x, ).count() > 0 else None,
                    self.data.get("classifiers", list(), ),
                )
            ), )

        if "license" in self.data :
            self.data["license"] = _objects.get(name=self.data["license"],
                    ).key if _objects.filter(name=self.data["license"], ).count() > 0 else None

        return super(BasePackage, self).full_clean(*a, **kw)


class Package (BasePackage, ) :
    class Meta :
        model = models_package.Package


class Release (BasePackage, ) :
    class Meta :
        model = models_package.Release

    name          = forms.CharField(required=False, )
    version_base  = forms.CharField(required=False, )
    version_tags  = forms.CharField(required=False, )

    def clean_version (self, ) :
        _v = self.cleaned_data.get("version")
        if pkg_resources.safe_version(_v, ) != _v :
            raise forms.ValidationError("version is not safe")

        return _v

    def clean (self, ) :
        (_v, _base, _vtags, ) = utils_package.parse_version(self.cleaned_data.get("version"), )
        self.cleaned_data["version_base"] = _base
        self.cleaned_data["version_tags"] = _vtags

        _r = super(Release, self).clean()

        # update Package information
        if not self.cleaned_data.get("name") and self.cleaned_data.get("package") :
            self.data_orig["name"] = self.cleaned_data.get("package").name

        self._form_package = Package(
                self._request, self.data_orig, instance=self.cleaned_data.get("package"), )
        if not self._form_package.is_valid() :
            raise forms.ValidationError(self._form_package.errors, )

        return _r

    def save (self, *a, **kw) :
        _r = super(Release, self).save(*a, **kw)

        self._form_package.save()

        return _r




if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




