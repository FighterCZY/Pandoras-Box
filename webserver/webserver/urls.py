from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^pandora$', 'pandora.views.index'),
    url(r'^pandora/register$', 'pandora.views.register'),
    url(r'^pandora/login$', 'pandora.views.login'),
    url(r'^pandora/list$', 'pandora.views.list'),
    url(r'^pandora/upload$', 'pandora.views.upload'),
    # Examples:
    # url(r'^$', 'webserver.views.home', name='home'),
    # url(r'^webserver/', include('webserver.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
