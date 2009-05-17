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

  # For tracking replication 
  replicated = models.BooleanField(default=False)
  repl_promise = models.IntegerField(null=True)
  # comma separated list of hosts 
  repl_list = models.CharField(max_length=255)

  def add_to_repl_list(self, hn):
    s = set(self.repl_list.split(','))
    s.add(hn)
    self.repl_list = ','.join(list(s))

  def get_repl_list(self):
    l = self.repl_list.split(',')
    l.sort()
    l = [i for i in l if i]
    return l

  def repl_ratio(self):
    num_repls = len(self.repl_list.split(',')[1:])
    promises = self.repl_promise
    return '(%.2f%%)' % ((float(num_repls) / float(promises))*100)

  # Suitable for use in templates
  def dict_repr(self,json_date=False):
    d = {}
    d['name'] = self.name
    d['size'] = self.size
    # Encode dates in a json serializable format
    if json_date:
      d['mtime'] = datetime.datetime.fromtimestamp(self.mtime).strftime('%s')
    else:
      d['mtime'] = datetime.datetime.fromtimestamp(self.mtime)
    d['full_path'] = self.full_path
    d['path'] = self.path
    d['gdocs_able_to_upload'] = self.full_path.lower().endswith('.doc')
    d['replicated'] = self.replicated
    d['deleted'] = self.deleted
    if self.replicated:
      d['repl_ratio'] = self.repl_ratio()

    return d

  def __unicode__(self):
    return self.full_path

# Represents a backed up file on a host
class BackupFile(models.Model):
  remote_path = models.CharField(max_length=255)
  local_path = models.CharField(max_length=255)
 
