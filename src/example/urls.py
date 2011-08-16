from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url("^gppi/", include("gppi.urls"), ),
)
