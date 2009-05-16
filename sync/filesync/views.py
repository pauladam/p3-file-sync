import os, datetime, mimetypes, time, sys
import common_utils

from sync.filesync.models import File, Device

from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404

import gdata.docs
import gdata.docs.service
import gdata.auth
import gdata.service

# TODO: Move to a common utils module, as this
# is used by both servers...

# reckon our name
hn = os.popen('hostname').read().strip()
port = sys.argv[2].split(':')[-1]
server_hn_combo = "%s:%s" % (hn, port)

# TODO: Move util funcs to ... utils!

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
    file_set = File.objects.filter(name__contains=request.GET.get('contains'))
  elif request.GET.has_key('matches'):
    file_set = File.objects.filter(name__exact=request.GET.get('matches'))
  elif request.GET.has_key('modifiedsince'):
    file_set = File.objects.filter(mtime__gte=request.GET.get('modifiedsince'))
  else:
    file_set = File.objects.all()

  if output_format == 'xml':
    if device_name == 'gdocs':
      name_map = {'Name':'name','LastModified':'lastmodified','View_Link':'view_link','Download_Link':'download_link'}
      xml_out  = xmlify_objects(gdocs_templ_entries, name_map)
    else:
      xml_out = xmlify_objects(file_set, {'Path':'path','Name':'name','Size':'size','LastModified':'mtime'})

    return HttpResponse(xml_out, mimetype="text/xml")
  else:

    files = list(file_set)

    local_docs_templ_entries = []
    for f in files:
      d = {}
      d['name'] = f.name
      d['size'] = f.size
      d['mtime'] = datetime.datetime.fromtimestamp(f.mtime)
      d['full_path'] = f.full_path
      d['path'] = f.path
      d['gdocs_able_to_upload'] = f.full_path.lower().endswith('.doc')
      local_docs_templ_entries.append(d)

      if device_name == 'gdocs':
        local_docs_templ_entries = []

    return render_to_response('index.html', {'files': local_docs_templ_entries,'gdocs_entries':gdocs_templ_entries, 'message':message})

  # Shouldnt get here
  return render_to_response('index.html', {'files': local_docs_templ_entries,'gdocs_entries':gdocs_templ_entries, 'message':message})

def settings(request):
  from background import check_fs
  import threading

  basedir = request.GET.get('rootdir', None)
  device_name = request.GET.get('device_name', None)

  if not basedir or not device_name:
    # Just return xml rep. of the settings
    xml_out = """<Settings>
                   <Root directory="%s"/>
                 </Settings>"""

    root_dir = File.objects.all()[:1].get().rootdir

    return HttpResponse(xml_out % root_dir, mimetype="text/xml")

  # Purge db of old contents as were changing the root dir...
  File.objects.all().delete()

  t = threading.Timer(0.0, check_fs, kwargs={'root':basedir, 'device_name':device_name}).start()

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
  # return HttpResponse("ok", mimetype="text/plain")
  return HttpResponse("ok from %s" % server_hn_combo, mimetype="text/plain")
