from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'pandora.views.index'),
    url(r'^register$', 'pandora.views.register'),
    url(r'^login$', 'pandora.views.login'),
    url(r'^list$', 'pandora.views.list'),
    url(r'^upload$', 'pandora.views.upload'),
    url(r'^show$', 'pandora.views.show'),
    # Examples:
    # url(r'^$', 'webserver.views.home', name='home'),
    # url(r'^webserver/', include('webserver.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
