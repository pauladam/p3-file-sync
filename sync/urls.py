from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import os
HOME = os.getcwd()

urlpatterns = patterns('',
    (r'^$','sync.filesync.views.index'),
    (r'^settings$','sync.filesync.views.settings'),

    # Status monitor used by name server to clean up 
    # stale entries
    (r'^ruok$','sync.filesync.views.ruok'),

    # Accept peer list
    # set
    (r'^acceptpeerlist/(?P<peerlist>.*)$','sync.filesync.views.acceptpeerlist'),
    # get
    (r'^peerlist$','sync.filesync.views.peerlist'),

    # Trigger handler to send peers our updated file metadata
    (r'^broadcast_metadata$','sync.filesync.views.broadcast_metadata'),

    (r'^download(?P<filepath>.*)','sync.filesync.views.download'),
    # Synonym of the above defined in p1 requirements
    (r'^xml/file(?P<filepath>.*)','sync.filesync.views.download'),

    (r'^upload_to_gdocs(?P<filepath>.*)','sync.filesync.views.upload_to_gdocs'),
    # Synonym for the above
    (r'^xml/gdocsupload(?P<filepath>.*)','sync.filesync.views.upload_to_gdocs'),

    (r'(?P<device_name>\w+)/(?P<output_format>\w+)/filelist', 'sync.filesync.views.index'),

    (r'^login$','sync.filesync.views.login'),

    # If this gets too full of sync stuff, can re-factor like so: 
    # (r'^sync/', include('sync.foo.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': HOME+'/static'}),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
