#!/bin/sh
# clear django_session table
DJANGO_SETTINGS_MODULE="myproj.settings" python -c 'from django.contrib.sessions.models import Session; Session.objects.all().delete()' 
#python manage.py runserver

