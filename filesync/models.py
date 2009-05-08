from django.db import models

# Just using this as a hook point to 
# initiate our background tasks
import background

# Create your models here.

class File(models.Model):
  full_path = models.CharField(max_length=255)
  path = models.CharField(max_length=255)
  name = models.CharField(max_length=128)
  mtime = models.FloatField()
  size = models.FloatField()
  deleted = models.BooleanField(default=False)

  def __unicode__(self):
    return self.full_path

