#!/usr/bin/env python2.4
#
# Copyright 2010 Steve Carlson
#

import os
import cgi
import operator
import sys
import re
import datetime, time
import wsgiref.handlers 
from models.Message import Message

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app

def addDict(basedict, sourcedict):
    for k, v in sourcedict.iteritems(): 
        basedict[k]=v
    return basedict

def HalfHourAgo():
    now = datetime.datetime.now()
    if now.minute > 30:
       return now.replace(minute=now.minute-30)
    else:
       return now.replace(hour=now.hour-1,minute=now.minute+30)

def GCMessages():
    STORED = db.GqlQuery("SELECT * FROM Message WHERE date <= :1", HalfHourAgo())
    #STORED = db.GqlQuery("SELECT * FROM Message")
    for M in STORED:
        M.delete()

class BaseHandler(webapp.RequestHandler):
    '''
        Render:  BUILD AND DISPLAY PAGE, ACCEPTS TEMPLATE AND ARGUMENTS
    '''
    def Render(self, templ=None, dict=None):
        path = os.path.join(os.path.dirname(__file__), 'templates', templ)
        self.response.out.write(template.render(path, dict))

class GarbageCollector(BaseHandler):
    '''
        GET: CLEARS TWITTER AND BLOG DATA FROM DB, 
    '''
    def get(self):
        try:
            GCMessages()
        except:
            pass

'''
    application = DEFINE WSGI HANDLERS
'''
application = webapp.WSGIApplication(
                                     [
                                      ('/crongc', GarbageCollector)
                                      ],
                                     debug=True)


def main():
    '''
        RUN SOME WSGI APPS
    '''
    run_wsgi_app(application)


if __name__ == "__main__":
    '''
        SOME SILLY BOILERPLATE, I BLAME GUIDO
    '''
    main()