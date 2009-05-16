#!/usr/bin/python

import datetime, time

while True:
  now = datetime.datetime.now()

  # Every 5 seconds
  if now.second % 5 == 0:
    print 'every 5 seconds'

  ## Every 10 seconds
  #if now.second % 10 == 0:
  #  print 'every 10 seconds'

  ## Every 30 seconds 
  #if now.second % 30 == 0:
  #  print 'every 30 seconds'

  ## Every minute
  #if now.second % 60 == 0:
  #  print 'every 60 seconds'


  time.sleep(1)

