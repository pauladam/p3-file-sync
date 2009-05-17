import os, datetime, mimetypes, time, sys, random, fcntl, urllib, urllib2, glob
import simplejson as json
import common_utils
import utils
from utils import debug

from sync.filesync.models import File, Device

from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404

import gdata.docs
import gdata.docs.service
import gdata.auth
import gdata.service

# reckon our name
server_hn_combo = common_utils.get_hostname()
self_device = Device.objects.filter(hnportcombo=server_hn_combo).get()

# Return a filelist xml stanza 
# <FileList>
#   <File>
#     <Path>/path/to/file</Path>
#     <Name>filename.ext</Name>
#     <Size>file size</Size>
#     <LastModified>last mod date</LastModified>
#   </File>
#   ...
# </FileList>  
def xmlify_objects(files, name_map):

  import xml.etree.ElementTree as ET
  root = ET.Element("FileList")
  for file in files:
    file_node = ET.SubElement(root,'File')

    for display_name, name in name_map.items():
      n      = ET.SubElement(file_node, display_name)
      try:
        n.text = str(file.__getattribute__(name))
      except AttributeError:
        # Maybe its not an object but a dict
        n.text = str(file.get(name))

  return ET.tostring(root)

def get_full_url(request):
  return 'http://'+request.META['HTTP_HOST'] + request.META['PATH_INFO'] + '?' + request.META['QUERY_STRING']

def get_authsub_url():
  # TODO: Careful here... probably ought to change this...
  next = 'http://ivo:8000/'
  scopes = ['http://docs.google.com/feeds/']
  secure = False  # set secure=True to request a secure AuthSub token
  session = True
  # print '<a href="%s">Login to your Google account</a>' % GetAuthSubUrl()
  return gdata.service.GenerateAuthSubRequestUrl(next, scopes, secure=secure, session=session)

# TODO: Somewhere, need to re-add upgrade token garbage
def authd_with_gdocs(request):
  if request.session.get('gd_client',None):
    gd_client = request.session['gd_client']
    gd_client.GetDocumentListFeed()
    return True
  else:
    # Are we getting a token from the incoming GET?
    single_use_token = gdata.auth.extract_auth_sub_token_from_url(get_full_url(request))
    gdocs_client = gdata.docs.service.DocsService(source='ivo-filesync-v1')
    try:
      gdocs_client.UpgradeToSessionToken(single_use_token)
    except gdata.service.NonAuthSubToken:
      return False

    # Succeeded? So store in the session
    request.session['gd_client'] = gdocs_client
    return True

  return False

def login(request):
  return render_to_response('redirect_to_gdocs.html', {'authsub_url': get_authsub_url()})

# TODO: Add param to fetch / show contents of cached md for other devices
def index(request, message=None, error=None, device_name='all', output_format='html'):
  if not authd_with_gdocs(request):
    return render_to_response('redirect_to_gdocs.html', {'authsub_url': get_authsub_url()})
  else: 
    # If we just logged in, redirect back home to clean up the crufty url
    # containing the tokens passed back from google
    if 'token' in request.GET.keys():
      return HttpResponseRedirect(reverse('sync.filesync.views.index'))

  gdocs_client = request.session['gd_client']

  # TODO: Should probably de-couple this from the request as 
  # it takes a few seconds...
  gdocs_entries = gdocs_client.GetDocumentListFeed().entry

  gdocs_templ_entries = []
  for doc in gdocs_entries:
    d = {}
    d['name'] = doc.title.text
    lastmodified = datetime.datetime.strptime(doc.updated.text[:-5],"%Y-%m-%dT%H:%M:%S")
    d['lastmodified'] = lastmodified
    d['view_link'] = doc.GetHtmlLink().href
    d['download_link'] = doc.GetMediaURL()
    gdocs_templ_entries.append(d)

  # Set specification (matches, contains, modifiedsince ...)?
  if request.GET.has_key('contains'):
    file_set = File.objects.filter(name__contains=request.GET.get('contains')).filter(device=self_device)
  elif request.GET.has_key('matches'):
    file_set = File.objects.filter(name__exact=request.GET.get('matches')).filter(device=self_device)
  elif request.GET.has_key('modifiedsince'):
    file_set = File.objects.filter(mtime__gte=request.GET.get('modifiedsince')).filter(device=self_device)
  else:
    file_set = File.objects.filter(device=self_device)

  if output_format == 'xml':
    if device_name == 'gdocs':
      name_map = {'Name':'name','LastModified':'lastmodified','View_Link':'view_link','Download_Link':'download_link'}
      xml_out  = xmlify_objects(gdocs_templ_entries, name_map)
    else:
      xml_out = xmlify_objects(file_set, {'Path':'path','Name':'name','Size':'size','LastModified':'mtime'})

    return HttpResponse(xml_out, mimetype="text/xml")
  else:
    
    current_device = self_device.hnportcombo
    currently_viewing = 'Local Files'

    cache_device_list = [(mdc.split('/')[-1].split('of_')[-1]) 
                         for mdc in glob.glob('data/metadata_cache/*') if mdc.split('/')[-1].startswith(server_hn_combo)]

    if request.GET.has_key('remote_device') and request.GET.get('remote_device') != self_device.hnportcombo:
      cached_data = eval(file('data/metadata_cache/%s_cache_of_%s' % (server_hn_combo, request.GET.get('remote_device'))).read())

      currently_viewing = 'Remote Device (%s)' % cached_data['device_name']
      current_device = cached_data['device_name']

      local_docs_templ_entries = []
      # Convert timestamps back to datetime objects
      for f in cached_data['files']:
        # Convert time from long back into datetime for templ
        f['mtime'] = datetime.datetime.fromtimestamp(int(f['mtime']))
        local_docs_templ_entries.append(f)

    elif request.GET.has_key('remote_device') and request.GET.get('remote_device') == self_device.hnportcombo:
      return HttpResponseRedirect(reverse('sync.filesync.views.index'))

    # Default set
    else: 
      files = list(file_set)

      local_docs_templ_entries = []
      for f in files:
        local_docs_templ_entries.append(f.dict_repr())

        if device_name == 'gdocs':
          local_docs_templ_entries = []

    template_context = {'files': local_docs_templ_entries,
                        'gdocs_entries':gdocs_templ_entries, 
                        'message':message,
                        'currently_viewing':currently_viewing,
                        'current_device':current_device,
                        'this_device':self_device,
                        'cache_device_list':cache_device_list,
                        'disk_icons':['Disk%s.gif' % random.randint(1,len(self_device.peer_list())) for i in range(len(self_device.peer_list()))]}
    return render_to_response('index.html', template_context)

  # Shouldnt get here
  return render_to_response('index.html', {'files': local_docs_templ_entries,'gdocs_entries':gdocs_templ_entries, 'message':message})

def settings(request):
  import background 

  basedir = request.GET.get('rootdir', None)
  device_name = request.GET.get('device_name', None)

  if not basedir or not device_name:
    # Just return xml rep. of the settings
    xml_out = """<Settings>
                   <Root directory="%s"/>
                 </Settings>"""

    root_dir = File.objects.filter(device=self_device).get().rootdir

    return HttpResponse(xml_out % root_dir, mimetype="text/xml")

  # Purge db of our old contents as were changing the root dir...
  File.objects.filter(device=self_device).delete()

  # Set the rootdir on our Device
  self_device.rootdir = basedir
  self_device.preferred_name = device_name
  self_device.save()

  fs_checker = background.FSChecker(basedir, device_name)
  fs_checker.start()

  # sleep for a second, give the fs walker a chance to get some entries
  # in the db
  time.sleep(1)
 
  return HttpResponseRedirect(reverse('sync.filesync.views.index'))

def download(request, filepath):
  basename = filepath.split('/')[-1]
  response = HttpResponse(mimetype=mimetypes.guess_type(basename))
  response['Content-Disposition'] = "attachment; filename=" + basename
  response['Content-Length'] = os.path.getsize(filepath)
  response.write(open(filepath).read())
  return response

def upload_to_gdocs(request, filepath):
  gdocs_client = request.session['gd_client']

  filename = filepath.split('/')[-1]
  ext = filename.split('.')[-1].upper()

  # Is this file type supported?
  if not gdata.docs.service.SUPPORTED_FILETYPES.get(ext):
    error = 'File type %s not supported for uploads to google docs' % ext.lower()
    print error
    #return render_to_response('index.html', {'files': local_docs_templ_entries,'gdocs_entries':gdocs_templ_entries, 'error':error})
    raise Http404

  ms = gdata.MediaSource(file_path=filepath, content_type=gdata.docs.service.SUPPORTED_FILETYPES[ext])
  entry = gdocs_client.UploadDocument(ms, filename)
  info = '%s uploaded successfully to Google Docs' % filename

  # Redirect to index
  return HttpResponseRedirect(reverse('sync.filesync.views.index'))

def ruok(request):
  return HttpResponse("ok from %s" % server_hn_combo, mimetype="text/plain")

def acceptpeerlist(request, peerlist):

  self_device.peers = peerlist
  self_device.save()

  # Redirect to broadcast_metadata since our list has 
  # been updated
  #return HttpResponseRedirect(reverse('sync.filesync.views.broadcast_metadata'))

  return HttpResponse("ok from %s" % server_hn_combo, mimetype="text/plain")

def peerlist(request):

  return HttpResponse("peerlist for %s : %s" % (server_hn_combo,self_device.peers) , mimetype="text/plain")

def broadcast_metadata(request):

  debug('in broadcast_metadata')
  
  # TODO: Also take care of the case where we need to send md about 3rd party devices as well

  # Pack up our file metadata and send to known peers

  # Get files
  files = utils.get_files_for_device(self_device)
  l = []
  for f in files:
    l.append(f.dict_repr(json_date=True))

  # Dump format : dict  {'device_name':'ivo:8001', 'version': 1, 'files': [file list]}

  # Pickle list
  # If we have a dump already read its version, update and re-write
  # else, simply write 
  target_dump_fn = 'data/%s.metadata.json' % self_device.hnportcombo.replace(':','_')

  dump_dict = {'device_name':self_device.hnportcombo, 'version':1, 'files':l}

  if os.path.exists(target_dump_fn):
    dump_fd = file(target_dump_fn,'r')
    last_dump = json.load(dump_fd)
    dump_fd.close()

    dump_dict['version'] = last_dump['version'] + 1

    # Need to protect this operation
    dump_fd = file(target_dump_fn,'w')
    fcntl.lockf(dump_fd,fcntl.LOCK_EX)
    json.dump(dump_dict,dump_fd)
    fcntl.lockf(dump_fd,fcntl.LOCK_UN)
    dump_fd.close()

    debug("pickle version: %s %s " % (target_dump_fn, last_dump['version']))
  else:

    # Need to protect this operation
    dump_fd = file(target_dump_fn,'w')
    fcntl.lockf(dump_fd,fcntl.LOCK_EX)
    json.dump(dump_dict,dump_fd)
    fcntl.lockf(dump_fd,fcntl.LOCK_UN)
    dump_fd.close()

  # Post updated metadata to 
  for peer in self_device.peer_list():
    debug('[%s] broadcasting md update to %s' % (self_device, peer))
    url = '/'.join(['http:/',peer,'recv_metadata',])
    raw_post_data = {'device' : self_device.hnportcombo, 'metadata' : dump_dict}
    data = urllib.urlencode(raw_post_data)
    debug(url)
    req = urllib2.Request(url, data)
    res = urllib2.urlopen(req)
    debug(res.read())

  return HttpResponse("%s : Sending peers updated metadata" % (self_device.hnportcombo), mimetype="text/plain")

def recv_metadata(request):
  incoming_device = request.POST.get('device')
  #incoming_md = simplejson.loads(request.POST.get('metadata'))
  #incoming_md = eval(request.POST.get('metadata'))
  incoming_md = request.POST.get('metadata')

  target_fn = 'data/metadata_cache/%s_cache_of_%s' % (self_device.hnportcombo, incoming_device)
  # Check if we have a cache of this devices md already
  # if no, just write it (easy case)
  if not os.path.exists(target_fn):
    debug('in first if')
    f = file(target_fn,'w')
    f.write(incoming_md)
    f.close()
  else:
    # if yes, read and make sure this version is newer
    evaled_incoming_md = eval(request.POST.get('metadata'))
    incoming_md_version = int(evaled_incoming_md['version'])

    # Check existing cache 
    f_c = file(target_fn,'r')
    existing_md_cache = eval(f_c.read())
    f_c.close()

    existing_md_cache_version = int(existing_md_cache['version'])

    debug('existing cache vers: %s, incoming vers: %s' % (existing_md_cache['version'], incoming_md_version))
    if incoming_md_version > existing_md_cache_version:
      debug('Incoming md cache version is newer so replace current md cache')
      f_c = file(target_fn,'w')
      f_c.write(request.POST.get('metadata'))
      f_c.close()
      
  return HttpResponse("%s : recv metadata ok" % (self_device.hnportcombo), mimetype="text/plain")

def replicate(request, filepath):
  repl_num = request.GET.get('repl_num')
  debug("Replicate request from client for: %s, %s times" % (filepath, repl_num))

  f = File.objects.filter(full_path=filepath).get()
  f.replicated = True
  f.repl_promise = int(repl_num)
  f.save()

  # Try to send to some peers
  for peers in self_device.peer_list():
    pass

  return HttpResponse("%s : replicate ok" % (self_device.hnportcombo), mimetype="text/plain")
