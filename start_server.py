#!/usr/bin/python

import os, sys, subprocess

try:
  os.remove('/tmp/filesync_scan_fs_start_lock')
except OSError:
  pass

num_servers = sys.argv[1]
default_starting_port = 8000
output_file = open('server_log','a')

os.environ['DJANGO_SETTINGS_MODULE'] = 'p3.settings';

for s in range(int(num_servers)):

  port = (default_starting_port + s)
  print 'Starting a server on port %d...' % port
  proc = subprocess.Popen('python manage.py runserver 0.0.0.0:%d' % port, stderr=output_file, stdout=output_file, shell=True)

