import threading, urllib, time, sys
from fns.ns.models import Host
import fns_utils
import datetime

def check_filesync_servers():
  print 'ping!'

  if 'runserver' in sys.argv:
    # This may be run by multiple threads
    # but its ok tho tho  b/c this threads 
    # purpose is just to check 
    # whether servers are alive or not. 
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
        # so lets consider him dead
        try:
          Host.objects.filter(hostname=host.hostname).get().delete()
        except Host.DoesNotExist:
          # Hes already been removed, no biggie
          pass 

        # Change of host list so lets send out an update
        #print 'timer ticked, and we removed a host, lets update group'
        fns_utils.announce_hostlist()

    # And play it again sam...
    t = threading.Timer(30, check_filesync_servers).start()

t = threading.Timer(10.0, check_filesync_servers).start()
