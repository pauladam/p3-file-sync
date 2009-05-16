from django.db import models

class Device(models.Model):
  preferred_name  = models.CharField(max_length=255)
  color = models.CharField(max_length=255)
  hnportcombo = models.CharField(max_length=255)
  rootdir = models.CharField(max_length=255)
  peers = models.CharField(max_length=255)

  def __unicode__(self):
    return "%s : %s" % (self.preferred_name, self.hnportcombo)

  def peer_list(self):
    return self.peers.split(',')

class File(models.Model):
  full_path = models.CharField(max_length=255)
  path = models.CharField(max_length=255)
  name = models.CharField(max_length=128)
  rootdir = models.CharField(max_length=255)
  mtime = models.FloatField()
  size = models.FloatField()
  deleted = models.BooleanField(default=False)
  device_name = models.CharField(max_length=128)
  # FK to 'owning' device
  device = models.ForeignKey(Device)

  def __unicode__(self):
    return self.full_path

