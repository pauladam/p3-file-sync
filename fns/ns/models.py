from django.db import models

class Host(models.Model):
  hostname = models.CharField(max_length=200)
  online  = models.BooleanField()

  def __unicode__(self):
    return self.hostname

