#!/usr/bin/python

import os, sys, subprocess, time

num_servers = sys.argv[1]
default_starting_port = 8000
if len(sys.argv) > 2:
  default_starting_port = int(sys.argv[2])

output_file = open('server_log','a')

os.environ['DJANGO_SETTINGS_MODULE'] = 'sync.settings';

for s in range(int(num_servers)):

  port = (default_starting_port + s)
  print 'Starting a server on port %d...' % port
  proc = subprocess.Popen('python manage.py runserver 0.0.0.0:%d' % port, stderr=output_file, stdout=output_file, shell=True)
  time.sleep(1)

