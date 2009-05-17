import logging, os
from django.conf import settings

def get_hex_color():
  import random
  return '#'+''.join([hex(random.randint(0,15))[2] for i in range(6)])

def get_files_for_device(device):
  from sync.filesync.models import File, Device
  return list(File.objects.filter(device=Device.objects.filter(hnportcombo=device.hnportcombo).get()))

def getlogger():
  logger = logging.getLogger()
  hdlr = logging.FileHandler(settings.LOG_FILE)
  formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s%(message)s','%Y-%m-%d %a %H:%M:%S') 
  
  hdlr.setFormatter(formatter)
  logger.addHandler(hdlr)
  logger.setLevel(logging.NOTSET)

  return logger

def debug(msg):
  logger = getlogger()
  logger.debug(msg)

def check_fs_running(device_name):
  FS_SCAN_LOCK = '/tmp/filesync_scan_fs_start_lock_%s' % device_name

  try:
    statinfo = os.stat(FS_SCAN_LOCK)

    # Otherwise, this state is locked, a thread is running so just bail
    if statinfo:
      thread_running = True
  except OSError:
    # No threads started yet, create a lock
    file(FS_SCAN_LOCK,'w').write('ok')
    thread_running = False

  return thread_running
