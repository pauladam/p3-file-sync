import time, os, re
from filesync.models import File
from threading import Thread

class BackgroundWorker(Thread):
  def __init__ (self, root):
    Thread.__init__(self)
    self.root = root

  def run(self):
      # Run 1
      if len(File.objects.all()) < 1:
        print 'first run'

        for path, dirs, files in os.walk(self.root):
          if len(dirs) == 0:
            for f in files:
              print f

              full_file_path = "%s/%s" % (path,f)
              mtime = os.stat(full_file_path).st_mtime
              size = os.stat(full_file_path).st_size
              # Terse I know :) but its fine, seriously dont worry about it 
              File(name=f, size=size, mtime=mtime, path=path, full_path=full_file_path).save()
      else:
      # Run 1 + n
        while True:
          try:
            # sys.stderr.write('.')
            time.sleep(2)

            # Check if any updates are needed to the files in our db

            # Iterate through files in our db
            for file in File.objects.filter(deleted=False):
              print file
              try:
                statinfo = os.stat(file.full_path)
                  
                # sizes differ, adjust size
                if file.size != statinfo.st_size:
                  file.size = statinfo.st_size
                  file.save()

                # mtimes differ, adjust mtime
                if file.mtime != statinfo.st_mtime:
                  file.mtime = statinfo.st_mtime
                  file.save()

              except OSError, oserror:
                if oserror.strerror.startswith('No such file'):
                  # The file was deleted
                  file.deleted = True
                  file.save()
                
            # Do a fs walk just to check for new files
            known_files = [file.full_path for file in File.objects.all()]
            for path, dirs, files in os.walk('/home/paul/test'):
              if len(dirs) == 0:
                for f in files:
                  # Either a) we know about the file (boring)
                  #     or b) its been undeleted (set deleted flag from true to false)
                  #     or c) its new and needs to be added (make a new file object and save it)
                  full_file_path = "%s/%s" % (path,f)

                  if full_file_path in known_files:
                    file_from_db = File.objects.filter(full_path=full_file_path).get() # using .get() like .one()
                    # Set deleted flag to false
                    if file_from_db.deleted == True:
                      file_from_db.deleted = False
                      file_from_db.save()

                  # Totally new file, add it
                  elif full_file_path not in known_files:
                    statinfo = os.stat(full_file_path)
                    File(name=f, size=statinfo.st_size, mtime=statinfo.st_mtime, path=path, full_path=full_file_path).save()
          except KeyboardInterrupt:
            print 'KEYBOARD EXCEPTION booooy'
         
# worker = BackgroundWorker('/home/paul/test')
# worker.start()
 
