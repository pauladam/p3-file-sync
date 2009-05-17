from django.db import models
import datetime

class Device(models.Model):
  preferred_name  = models.CharField(max_length=255)
  color = models.CharField(max_length=255)
  hnportcombo = models.CharField(max_length=255)
  rootdir = models.CharField(max_length=255)
  peers = models.CharField(max_length=255)

  def __unicode__(self):
    return "%s : %s" % (self.preferred_name, self.hnportcombo)

  def peer_list(self):
    l = self.peers.split(',')
    l.sort()
    return l

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

  # Suitable for use in templates
  def dict_repr(self,json_date=False):
    d = {}
    d['name'] = self.name
    d['size'] = self.size
    # Encode dates in a json serializable format
    if json_date:
      d['mtime'] = datetime.datetime.fromtimestamp(self.mtime).strftime('%Y-%m-%dT%H:%M:%S')
    else:
      d['mtime'] = datetime.datetime.fromtimestamp(self.mtime)
    d['full_path'] = self.full_path
    d['path'] = self.path
    d['gdocs_able_to_upload'] = self.full_path.lower().endswith('.doc')
    return d

  def __unicode__(self):
    return self.full_path

