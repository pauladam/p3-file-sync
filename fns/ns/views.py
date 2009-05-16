from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from fns.ns.models import Host
import urllib
import fns_utils

def hostlist(request):
  str_out = ','.join([h.hostname for h in Host.objects.all()])
  if str_out.startswith(','):
    str_out = str_out[1:]

  return HttpResponse(str_out, mimetype="text/plain")

def addhost(request, hn):
  str_out = 'Adding host %s ' % hn

  # We dont want duplicate entries in our db
  # so make this function idempotent for add's

  if len(Host.objects.filter(hostname=hn)) < 1:
    print 'adding new host'
    Host(hostname=hn).save()
  else:
    print 'wont add host'

  return HttpResponse(str_out, mimetype="text/plain")

def removehost(request, hn):
  str_out = 'Removing host %s ' % hn

  try:
    Host.objects.filter(hostname=hn).get().delete()
  except DoesNotExist:
    print 'Couldnt remove host : %s, caught DoesNotExist' % hn

  return HttpResponse(str_out, mimetype="text/plain")

def removeall(request):
  str_out = 'Removing all hosts'

  Host.objects.all().delete()

  return HttpResponse(str_out, mimetype="text/plain")

