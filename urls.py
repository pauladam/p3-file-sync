from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import os
HOME = os.getcwd()

urlpatterns = patterns('',
    (r'^$','p3.filesync.views.index'),
    (r'^set_basedir$','p3.filesync.views.set_basedir'),
    (r'^download(?P<filepath>.*)','p3.filesync.views.download'),

    # If this gets too full of p3 stuff, can re-factor like so: 
    # (r'^p3/', include('p3.foo.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': HOME+'/static'}),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
