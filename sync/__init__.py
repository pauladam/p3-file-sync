# Filesync app start up code here:
from filesync.models import File
import threading, sys, os
from background import check_fs
import urllib

# reckon our name
hn = os.popen('hostname').read().strip()
port = sys.argv[2].split(':')[-1]
server_hn_combo = "%s:%s" % (hn, port)

# Server start up time so add ourself to 
# the NS known host list
NS_ADDRESS = 'http://ivo:6666' # NS lives at a 'known address'
method = 'addhost'
payload = server_hn_combo
url = '/'.join([NS_ADDRESS, method, payload])

urllib.urlopen(url)

# Create a token so we can know if weve 'run' already
# since django executes this module multiple times.
# A less bad approach would be to detect in python 
# if our thread is running already, we could do that
# but this might suffice
FS_SCAN_LOCK = '/tmp/filesync_scan_fs_start_lock'

try:
  statinfo = os.stat(FS_SCAN_LOCK)

  # Otherwise, this state is locked, a thread is running so just bail
  if statinfo:
    thread_running = True
except OSError:
  # No threads started yet, create a lock
  file(FS_SCAN_LOCK,'w').write('ok')
  thread_running = False

print sys._getframe(1).f_code.co_name

# Shorthand for, are we configured and 
# prepared to start watching the fs?
if not thread_running and len(File.objects.all()) > 0:
  # Error prone when we have multiple roots, devices
  # we will always only have one local device but we may support
  # remote devices in the future... so basically we need to bind 
  # the (device name, root dir) tuple into the server instance
  # then wed use that tuple here. until then just use the first couplet we find...
  f = File.objects.all()[:1].get()
  basedir, device_name = f.rootdir, f.device_name 

  print 'starting thread'
  t = threading.Timer(0.0, check_fs, kwargs={'root':basedir, 'device_name':device_name}).start()
