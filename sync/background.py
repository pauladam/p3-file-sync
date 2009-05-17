import time, os, re, sys, threading
from filesync.models import File, Device
import common_utils
import sched, time
from utils import debug

# TODO: Check fs isnt started on server start, only after a
# dir is set. we should start it if we can and we have files to watch..

class FSChecker:

  def __init__(self, root, device_name):
    self.root = root
    self.device_name = device_name
    self.running = False

  def start(self):

    if self.running:
      return
    self.running = True

    t = threading.Timer(0.0, self.check_fs, kwargs={}).start()

  def check_fs(self):

    #if 'runserver' in sys.argv:
    #  this_device = Device.objects.filter(hnportcombo=common_utils.get_hostname()).get()

    # TODO: while not stopped
    while True:
      time.sleep(2)
    
      this_device = Device.objects.filter(hnportcombo=common_utils.get_hostname()).get()

      # Run 1
      if len(File.objects.filter(device=this_device)) < 1:
        debug('first run')

        for path, dirs, files in os.walk(self.root):
          for f in files:
            full_file_path = '/'.join([path,f])

            mtime = os.stat(full_file_path).st_mtime
            size = os.stat(full_file_path).st_size
            # Terse I know :) but its fine, seriously dont worry about it 
            File(name=f, 
                 size=size, 
                 mtime=mtime, 
                 path=path, 
                 full_path=full_file_path, 
                 device_name=self.device_name,
                 rootdir=self.root,
                 device=this_device).save()

    # And reset timer
    lt = threading.Timer(5.0, check_fs, kwargs={'root':root,'device_name':device_name}).start()
    
