#!/usr/bin/env python

import logging
import os
import httplib2

from google.appengine.dist import use_library
use_library('django', '1.2')

from events import FetchEvent

from models import CompanySubscription
from models import User

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

from xml.dom import minidom

appDirectLink = "https://www.appdirect.com/purchase/480"

class WelcomeHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'welcome.html')
        template_values = { 'appDirectLink' : appDirectLink }
        self.response.out.write(template.render(path, template_values))

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            subscriptions = CompanySubscription.all()
            logoutUrl = users.create_logout_url("/")
            
            appUser = User.all()\
                .filter('openid =', user.federated_identity()).get()
            if appUser == None:
                appUser = User.all()\
                    .filter('email =', user.email()).get()
            if appUser:
                sub = appUser.subscription
                appUsers = User.all().filter('subscription = ', sub)
                template_values = { 'appUser' : appUser, \
                                        'companyName' : sub.name, \
                                        'edition' : sub.edition, \
                                        'appUsers' : appUsers, \
                                        'logoutUrl' : logoutUrl }
                path = os.path.join(os.path.dirname(__file__), 'index.html')
                self.response.out.write(template.render(path, template_values))
            else:
                # Send the user to AppDirect to purchase the app
                self.redirect(appDirectLink)
        else:
            # Log this user in
            self.redirect(users.create_login_url("https://www.appdirect.com/openid/id"))

class EventHandler(webapp.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        self.response.out.write(FetchEvent(self.request.get('token')))

def main():
    application = webapp.WSGIApplication([('/', WelcomeHandler),\
                                              ('/main', MainHandler),\
                                              ('/event', EventHandler)],\
                                             debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
