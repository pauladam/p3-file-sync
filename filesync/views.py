import os, datetime, mimetypes

from p3.filesync.models import File

from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404

import gdata.docs
import gdata.docs.service
import gdata.auth
import gdata.service

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
  
def index(request):

  if not authd_with_gdocs(request):
    return render_to_response('redirect_to_gdocs.html', {'authsub_url': get_authsub_url()})

  gdocs_client = request.session['gd_client']
  gdocs_entries = gdocs_client.GetDocumentListFeed().entry

  ## Loop through the feed and extract each document entry.
  #for document_entry in documents_feed.entry:
  #  # Display the title of the document on the command line.
  #  print document_entry.title.text

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
  # TODO: Will need to massage files as well
  # for better file size and last modified date display
  # TODO: Also need to add download link 
  # TODO also need to add upload link to google docs

  return render_to_response('index.html', {'files': files,'gdocs_entries':gdocs_templ_entries})

def set_basedir(request):
  from background import BackgroundWorker
  basedir = request.POST['basedir']

  # Purge db of old contents as were changing the root dir...
  File.objects.all().delete()

  # XXX Isnt catching changes?

  # Start our fs monitor
  worker = BackgroundWorker(basedir)
  worker.start()
 
  return HttpResponseRedirect(reverse('p3.filesync.views.index'))

#def download(request, filename):
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

