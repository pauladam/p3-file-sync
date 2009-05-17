# Filesync app start up code here:
from filesync.models import File, Device
import threading, sys, os, time, sched
import urllib
import utils
from utils import debug
import common_utils
import background

# reckon our name if were starting the server
if 'runserver' in sys.argv:

  server_hn_combo = common_utils.get_hostname()

  # Register w/ the nameserver
  NS_ADDRESS = 'http://ivo:6666' # NS lives at a 'known address'
  method = 'addhost'
  payload = server_hn_combo
  url = '/'.join([NS_ADDRESS, method, payload])
  urllib.urlopen(url)

  # Add device entry to the local db for our hostname
  # if it doesnt exist already
  if len(Device.objects.filter(hnportcombo=server_hn_combo)) < 1:
    Device(hnportcombo=server_hn_combo, color=utils.get_hex_color()).save()
  else: 
    # Get the reference to myself
    self_device = Device.objects.filter(hnportcombo=server_hn_combo).get()

  # Shorthand for, are we configured and 
  # prepared to start watching the fs?
  # AKA, are there files being watched already for
  # this device
  if len(File.objects.filter(device=self_device)) > 0:
    # Error prone when we have multiple roots, devices
    # we will always only have one local device but we may support
    # remote devices in the future... so basically we need to bind 
    # the (device name, root dir) tuple into the server instance
    # then wed use that tuple here. until then just use the first couplet we find...

    # Kind of cavalier but should work
    f = File.objects.filter(device=self_device)[:1].get()
    basedir, device_name = f.rootdir, f.device_name 

    fs_checker = background.FSChecker(basedir, device_name)
    fs_checker.start()


