from django.contrib import admin
from sync.filesync.models import File, Device, BackupFile

admin.site.register(Device)
admin.site.register(File)
admin.site.register(BackupFile)

