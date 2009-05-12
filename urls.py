from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import os
HOME = os.getcwd()

urlpatterns = patterns('',
    (r'^$','p3.filesync.views.index'),
    (r'^set_basedir$','p3.filesync.views.set_basedir'),

    # Example:
    # (r'^p3/', include('p3.foo.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': HOME+'/static'}),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
