from fns.ns.models import Host
import urllib

def announce_hostlist():

  print 'announcing hostlist'

  host_set = set([h.hostname for h in Host.objects.all()])

  for h in host_set:
    ann_list = ','.join(list(host_set.difference(set([h]))))
    url = '/'.join(['http:/',h,'acceptpeerlist',ann_list])
    print 'Telling %s about peers: %s [%s]' % (h, ann_list, url)
    try:
      urllib.urlopen(url).read()
    except:
      # Ok this is kind of dangerous in that we are
      # catching all exceptions, but I think sometimes
      # we are announcing to a dead peer in which this 
      # should throw some type of socket open exception
      pass
 
