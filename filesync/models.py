from django.db import models

# Create your models here.

class File(models.Model):
  full_path = models.CharField(max_length=255)
  path = models.CharField(max_length=255)
  name = models.CharField(max_length=128)
  mtime = models.FloatField()
  size = models.FloatField()
  deleted = models.BooleanField(default=False)
  device_name = models.CharField(max_length=128)

  def __unicode__(self):
    return self.full_path

