import threading, urllib, time
from fns.ns.models import Host

def check_filesync_servers():

  # This may be run by multiple threads
  # but its ok tho tho  b/c this threads 
  # purpose is just to check 
  # wether servers are alive or not. 
  # Basically its idempotent.

  # Checking health of known servers
  # in efforts to clean up old entries
  for host in Host.objects.all():
    time.sleep(1)
    print 'checking %s' % host
    method = 'ruok'
    url = '/'.join(['http:/',host.hostname,method])
    print url
    try:
      print urllib.urlopen(url).read()
    except IOError:
      print 'Got IOError when checking %s, will delete' % host.hostname
      Host.objects.filter(hostname=host.hostname).get().delete()
      # so lets consider him dead

  # And play it again sam...
  t = threading.Timer(30, check_filesync_servers).start()

t = threading.Timer(0.0, check_filesync_servers).start()
