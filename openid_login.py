#!/usr/bin/env python

import logging

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

class OpenIdLoginHandler(webapp.RequestHandler):
  def get(self):
    continue_url = self.request.GET.get('continue')
    openid_url = self.request.GET.get('openid')
    if openid_url == None or openid_url == "":
        openid_url = "https://www.appdirect.com/openid/id"
    logging.info("Openid URL: %s" % openid_url)
    login_url = users.create_login_url(dest_url = continue_url, federated_identity=openid_url)
    logging.info("Redirecting user to %s" % login_url)
    self.redirect(login_url)

def main():
    application = webapp.WSGIApplication([('/_ah/login_required', OpenIdLoginHandler)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
