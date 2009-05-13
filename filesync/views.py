import os, datetime, mimetypes, time

from p3.filesync.models import File

from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404

import gdata.docs
import gdata.docs.service
import gdata.auth
import gdata.service

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
def xmlify_objects(files):
  import xml.etree.ElementTree as ET
  root = ET.Element("FileList")
  for file in files:
    file_node = ET.SubElement(root,'File')

    path_node = ET.SubElement(file_node,'Path')
    path_node.text = file.path
    name_node = ET.SubElement(file_node,'Name')
    name_node.text = file.name
    size_node = ET.SubElement(file_node,'Size')
    size_node.text = str(file.size)
    lastmodified_node = ET.SubElement(file_node,'LastModified')
    lastmodified_node.text = str(file.mtime)

  return ET.tostring(root)

def get_full_url(request):
  return 'http://'+request.META['HTTP_HOST'] + request.META['PATH_INFO'] + '?' + request.META['QUERY_STRING']

def get_authsub_url():
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
    gdocs_client.UpgradeToSessionToken(single_use_token)
    # Succeeded? So store in the session
    request.session['gd_client'] = gdocs_client
    return True

  return False

  #try:
  #  gd_client.UpgradeToSessionToken(single_use_token)
  #except gdata.service.NonAuthSubToken:
  #  # Nope not in this request, lets continue 
  #  # maybe the token is stored in the session
  #  pass
  #
  #if request.session.get('authd',False):
  #  #print PSUEDO_AUTH_URL % str(request.session['authd']).split('=')[1] 
  #  # stored_session_token_str = str(request.session['authd']).split('=')[1]
  #  
  #  try:
  #    #single_use_token = gdata.auth.extract_auth_sub_token_from_url(PSUEDO_AUTH_URL + stored_session_token_str)
  #    #print PSUEDO_AUTH_URL + stored_session_token_str
  #    #print single_use_token
  #    gd_client = gdata.docs.service.DocsService(source='ivo-filesync-v1')
  #    print 'token'
  #    print type(request.session['authd'])
  #    print request.session['authd']
  #    gd_client.UpgradeToSessionToken(request.session['authd'])
  #  except: # gdata.service.NonAuthSubToken:
  #    # Nope, our stored token didnt work either, 
  #    # lets clear the old one and request a new one
  #    print 'couldnt upgrade :('
  #    del request.session['authd']
  #    pass

  ## We got this far, maybe we have a good token, lets pull
  ## a document feed to test
  ## and remember to store the session token in the django session

  #try:
  #  if gd_client.GetDocumentListFeed():
  #    request.session['authd'] = single_use_token
  #    request.session['gd_client'] = gd_client
  #    return True
  #except:
  #  return False

  #return False
  ##  print gd_client.token_store

def login(request):
  return render_to_response('redirect_to_gdocs.html', {'authsub_url': get_authsub_url()})
  
def index(request, message=None, error=None):

  if not authd_with_gdocs(request):
    return render_to_response('redirect_to_gdocs.html', {'authsub_url': get_authsub_url()})
  else: 
    # If we just logged in, redirect back home to clean up the crufty url
    # containing the tokens passed back from google
    if 'token' in request.GET.keys():
      return HttpResponseRedirect(reverse('p3.filesync.views.index'))

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

  files = list(File.objects.all())

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

  return render_to_response('index.html', {'files': local_docs_templ_entries,'gdocs_entries':gdocs_templ_entries, 'message':message})

# Move filelist methods to their own view 
def filelist(request, device_name='all'):
  print 'running filelist'

  xml_out = xmlify_objects(File.objects.all())

  return HttpResponse(xml_out, mimetype="text/xml")


def set_basedir(request):
  from background import check_fs
  import threading
  basedir = request.POST['basedir']

  # Purge db of old contents as were changing the root dir...
  File.objects.all().delete()

  t = threading.Timer(0.0, check_fs, kwargs={'root':basedir}).start()

  # sleep for a second, give the fs walker a chance to get some entries
  # in the db
  time.sleep(1)
 
  return HttpResponseRedirect(reverse('p3.filesync.views.index'))

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

  print "extension : %s" % ext
  ms = gdata.MediaSource(file_path=filepath, content_type=gdata.docs.service.SUPPORTED_FILETYPES[ext])
  entry = gdocs_client.UploadDocument(ms, filename)
  print 'Document now accessible online at:', entry.GetAlternateLink().href

  #return render_to_response('index.html', {'files': local_docs_templ_entries,'gdocs_entries':gdocs_templ_entries, 'error':error})
  # Redirect to index
  return HttpResponseRedirect(reverse('p3.filesync.views.index', args=(1,)))

