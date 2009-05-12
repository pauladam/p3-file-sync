import os, datetime, mimetypes

from p3.filesync.models import File

from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse

import gdata.docs
import gdata.docs.service
import gdata.auth
import gdata.service

def human_readable_age(dt):
  now = datetime.datetime.utcnow()
  timedelta = now - dt

  yago = timedelta.days / 365
  mago = timedelta.days / 30
  wago = timedelta.days / 52
  dago = timedelta.days / 1
  hago = timedelta.days * 24
  miago = timedelta.days * 24 * 60
  sago = timedelta.days * 24 * 60 * 60

  # Could extend for hours, minutes etc

  if yago > 0:
    return (yago, 'year')
  elif mago > 0:
    return (mago, 'month')
  elif wago > 0:
    return (wago, 'week')
  elif dago > 0:
    return (dago, 'day')
  else:
    return (None,'a short while ago')

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
    return False

  ## Are we getting a token from the incoming GET?
  #single_use_token = gdata.auth.extract_auth_sub_token_from_url(get_full_url(request))
  #gd_client = gdata.docs.service.DocsService(source='ivo-filesync-v1')
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
    d['lastmodified'] = human_readable_age(lastmodified)
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

