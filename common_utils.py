def get_hostname():
  import sys, os
  hn = os.popen('hostname').read().strip()
  port = sys.argv[2].split(':')[-1]
  server_hn_combo = "%s:%s" % (hn, port)
  return server_hn_combo


