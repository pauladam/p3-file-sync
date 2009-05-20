#!/bin/bash
python manage.py sqlclear filesync > sqlclear
sqlite3 filesync.db < sqlclear
python manage.py syncdb

