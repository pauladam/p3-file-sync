import time, os, re, sys, threading
from filesync.models import File, Device
import common_utils
import sched, time, urllib
from utils import debug
import utils

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

    # TODO: or while not stopped
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

        # Files updated, trigger a md broadcast
        utils.trigger_md_broadcast(this_device.hnportcombo)
              
      # Run 1 + n
      # Check if any updates are needed to the files in our db
      for file in File.objects.filter(deleted=False, device=this_device):
        try:
          statinfo = os.stat(file.full_path)
            
          # sizes differ, adjust size
          if file.size != statinfo.st_size:
            debug('adjusting file sizes: %s ' % file)
            file.size = statinfo.st_size
            utils.trigger_md_broadcast(this_device.hnportcombo)
            file.save()

          # mtimes differ, adjust mtime
          if file.mtime != statinfo.st_mtime:
            debug('adjusting file mtime: %s ' % file)
            file.mtime = statinfo.st_mtime
            utils.trigger_md_broadcast(this_device.hnportcombo)
            file.save()

        except OSError, oserror:
          if oserror.strerror.startswith('No such file'):
            # The file was deleted
            debug('changing file deleted status false->true: %s' % file  )
            file.deleted = True
            utils.trigger_md_broadcast(this_device.hnportcombo)
            file.save()
          
      # Do a fs walk just to check for new files
      known_files = [file.full_path for file in File.objects.all()]
      for path, dirs, files in os.walk(self.root):
          for f in files:
            # Either a) we know about the file (boring)
            #     or b) its been undeleted (set deleted flag from true to false)
            #     or c) its new and needs to be added (make a new file object and save it)
            full_file_path = "%s/%s" % (path,f)

            if full_file_path in known_files:
              file_from_db = File.objects.filter(full_path=full_file_path)[:1].get() # using .get() like .one()
              # Set deleted flag to false
              if file_from_db.deleted == True:
                debug('changing file deleted status true->false: %s' % file_from_db)
                utils.trigger_md_broadcast(this_device.hnportcombo)
                file_from_db.deleted = False
                file_from_db.save()

            # Totally new file, add it
            elif full_file_path not in known_files:
              statinfo = os.stat(full_file_path)
              debug('[%s] found a new file, adding it: %s' % (this_device, full_file_path))
              utils.trigger_md_broadcast(this_device.hnportcombo)
              File(name=f, 
                   size=statinfo.st_size, 
                   mtime=statinfo.st_mtime, 
                   path=path, 
                   full_path=full_file_path, 
                   device_name=self.device_name,
                   rootdir=self.root,
                   device=this_device).save()

