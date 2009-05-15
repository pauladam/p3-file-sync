from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import os
HOME = os.getcwd()

urlpatterns = patterns('',
    (r'^$','p3.filesync.views.index'),
    (r'^settings$','p3.filesync.views.settings'),

    (r'^download(?P<filepath>.*)','p3.filesync.views.download'),
    # Synonym of the above defined in p1 requirements
    (r'^xml/file(?P<filepath>.*)','p3.filesync.views.download'),

    (r'^upload_to_gdocs(?P<filepath>.*)','p3.filesync.views.upload_to_gdocs'),
    (r'^login$','p3.filesync.views.login'),
    (r'(?P<device_name>\w+)/(?P<output_format>\w+)/filelist', 'p3.filesync.views.index'),

    # If this gets too full of p3 stuff, can re-factor like so: 
    # (r'^p3/', include('p3.foo.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': HOME+'/static'}),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
