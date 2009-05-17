from django.contrib import admin
from sync.filesync.models import File, Device

admin.site.register(Device)
admin.site.register(File)

