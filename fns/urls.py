from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^fns/', include('fns.foo.urls')),

    (r'^hostlist',   'fns.ns.views.hostlist'),
    (r'^addhost/(?P<hn>.*)$',    'fns.ns.views.addhost'),
    (r'^removehost/(?P<hn>.*)$', 'fns.ns.views.removehost'),
    (r'^removeall$', 'fns.ns.views.removeall'),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
